from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.knowledge.models.domain import AuditEvent, DataChange, Relationship
from app.main import app


def _upgrade_tmp_db(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "dossiers_d4_test.db"
    db_url = f"sqlite:///{db_path}"
    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "app/db/migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    engine = create_engine(db_url, future=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def _client_with_db(SessionLocal: sessionmaker[Session]) -> TestClient:
    def override_get_db() -> Iterator[Session]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _create_entity(client: TestClient, name: str, entity_type: str = "person") -> str:
    resp = client.post(
        "/api/v1/dossiers/entities",
        json={"canonical_name": name, "entity_type": entity_type, "profile_status": "active"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _base_connection_payload(**overrides):
    payload = {
        "relation_type": "fam.parent_of",
        "nature": "declarado",
        "verification_status": "nao_verificado",
        "status": "active",
        "created_by": "human_user:tester",
    }
    payload.update(overrides)
    return payload


def test_d4_migration_and_relationship_model(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    with SessionLocal() as db:
        rows = db.execute(select(Relationship)).scalars().all()
        assert rows == []


def test_taxonomy_endpoint_and_catalog_counts(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        resp = client.get("/api/v1/dossiers/connections/taxonomy")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] == 25
        assert data["approved_count"] == 21
        statuses = {}
        for item in data["items"]:
            statuses[item["status_mvp"]] = statuses.get(item["status_mvp"], 0) + 1
        assert statuses.get("approved") == 21
        assert statuses.get("requires_review") == 1
        assert statuses.get("blocked_by_model") == 3
        assert statuses.get("deferred", 0) == 0
    finally:
        app.dependency_overrides.clear()


def test_create_directed_connection_list_detail_and_traceability(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        a = _create_entity(client, "Alice", "person")
        b = _create_entity(client, "Bob", "person")
        payload = _base_connection_payload(
            relation_type="fam.parent_of",
            other_entity_id=b,
            anchor_role="from",
            description="Parentesco declarado",
        )
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=payload)
        assert r.status_code == 201, r.text
        conn = r.json()
        assert conn["relation_type"] == "fam.parent_of"
        assert conn["from_entity_id"] == a
        assert conn["to_entity_id"] == b
        assert conn["directionality"] == "directed"
        assert conn["nature"] == "declarado"
        assert conn["verification_status"] == "nao_verificado"
        assert conn["status"] == "active"
        assert conn["perspective"] == "outgoing"
        assert conn["perspective_label"] in {"Pai/mãe/responsável de", "Pai/mãe de"}

        lst = client.get(f"/api/v1/dossiers/entities/{a}/connections")
        assert lst.status_code == 200
        assert lst.json()["total"] == 1
        lst_b = client.get(f"/api/v1/dossiers/entities/{b}/connections")
        assert lst_b.status_code == 200
        assert lst_b.json()["total"] == 1
        assert lst_b.json()["items"][0]["perspective"] == "incoming"

        detail = client.get(f"/api/v1/dossiers/connections/{conn['id']}?anchor_entity_id={b}")
        assert detail.status_code == 200
        assert detail.json()["perspective"] == "incoming"

        with SessionLocal() as db:
            audits = db.execute(select(AuditEvent).where(AuditEvent.action == "dossier.connection.create")).scalars().all()
            changes = db.execute(select(DataChange).where(DataChange.entity_table == "relationships")).scalars().all()
            assert len(audits) >= 1
            assert len(changes) >= 1
    finally:
        app.dependency_overrides.clear()


def test_undirected_canonicalization_and_duplicate_conflict(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        a = _create_entity(client, "Ana", "person")
        b = _create_entity(client, "Bia", "person")
        # create in reverse order relative to canonical expectation still yields canonical pair
        payload = _base_connection_payload(relation_type="fam.sibling_of", other_entity_id=a)
        r = client.post(f"/api/v1/dossiers/entities/{b}/connections", json=payload)
        assert r.status_code == 201, r.text
        conn = r.json()
        assert conn["directionality"] == "undirected"
        ids = sorted([a, b])
        assert conn["from_entity_id"] == ids[0]
        assert conn["to_entity_id"] == ids[1]

        # duplicate semantic (same undirected pair) -> 409
        r2 = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=payload | {"other_entity_id": b})
        assert r2.status_code == 409, r2.text
    finally:
        app.dependency_overrides.clear()


def test_inverse_equivalence_supplier_customer_conflict(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        x = _create_entity(client, "Empresa X", "company")
        y = _create_entity(client, "Empresa Y", "company")
        p1 = _base_connection_payload(relation_type="biz.supplier_to", other_entity_id=y, anchor_role="from")
        r1 = client.post(f"/api/v1/dossiers/entities/{x}/connections", json=p1)
        assert r1.status_code == 201, r1.text
        # inverse equivalent same semantic link -> 409
        p2 = _base_connection_payload(relation_type="biz.customer_of", other_entity_id=x, anchor_role="from")
        r2 = client.post(f"/api/v1/dossiers/entities/{y}/connections", json=p2)
        assert r2.status_code == 409, r2.text
    finally:
        app.dependency_overrides.clear()


def test_multiple_distinct_vigencias_allowed_and_overlap_conflict(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        p = _create_entity(client, "Joao", "person")
        c = _create_entity(client, "Empresa A", "company")
        t1_from = datetime(2018, 1, 1, tzinfo=timezone.utc)
        t1_to = datetime(2020, 1, 1, tzinfo=timezone.utc)
        t2_from = datetime(2023, 1, 1, tzinfo=timezone.utc)
        t2_to = datetime(2025, 1, 1, tzinfo=timezone.utc)
        base = _base_connection_payload(relation_type="exec.director_of", other_entity_id=c, anchor_role="from")
        r1 = client.post(f"/api/v1/dossiers/entities/{p}/connections", json=base | {"valid_from": t1_from.isoformat(), "valid_to": t1_to.isoformat(), "time_precision": "year"})
        assert r1.status_code == 201, r1.text
        r2 = client.post(f"/api/v1/dossiers/entities/{p}/connections", json=base | {"valid_from": t2_from.isoformat(), "valid_to": t2_to.isoformat(), "time_precision": "year"})
        assert r2.status_code == 201, r2.text
        # overlap with first -> 409
        overlap = client.post(
            f"/api/v1/dossiers/entities/{p}/connections",
            json=base | {"valid_from": datetime(2019, 1, 1, tzinfo=timezone.utc).isoformat(), "valid_to": datetime(2021, 1, 1, tzinfo=timezone.utc).isoformat()},
        )
        assert overlap.status_code == 409, overlap.text
    finally:
        app.dependency_overrides.clear()


def test_validation_rules_422_and_not_operational_types(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        a = _create_entity(client, "A", "person")
        b = _create_entity(client, "B", "person")
        comp = _create_entity(client, "Comp", "company")

        # missing created_by -> 422
        bad = _base_connection_payload(relation_type="fam.spouse_of", other_entity_id=b)
        bad.pop("created_by")
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=bad)
        assert r.status_code == 422, r.text

        # invalid created_by format -> 422
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=_base_connection_payload(relation_type="fam.spouse_of", other_entity_id=b, created_by="tester"))
        assert r.status_code == 422, r.text

        # non-approved relation type -> 422
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=_base_connection_payload(relation_type="corp.beneficial_owner_of", other_entity_id=comp, anchor_role="from"))
        assert r.status_code == 422, r.text
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=_base_connection_payload(relation_type="asset.owner_of", other_entity_id=comp, anchor_role="from"))
        assert r.status_code == 422, r.text

        # entity type incompatibility (family person-person only) -> 422
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=_base_connection_payload(relation_type="fam.spouse_of", other_entity_id=comp))
        assert r.status_code == 422, r.text

        # inferido cannot be verificado -> 422
        r = client.post(
            f"/api/v1/dossiers/entities/{a}/connections",
            json=_base_connection_payload(relation_type="fam.parent_of", other_entity_id=b, anchor_role="from", nature="inferido", verification_status="verificado"),
        )
        assert r.status_code == 422, r.text

        # temporal invalid -> 422
        r = client.post(
            f"/api/v1/dossiers/entities/{a}/connections",
            json=_base_connection_payload(
                relation_type="fam.parent_of",
                other_entity_id=b,
                anchor_role="from",
                valid_from=datetime(2020, 1, 2, tzinfo=timezone.utc).isoformat(),
                valid_to=datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat(),
            ),
        )
        assert r.status_code == 422, r.text

        # self relation -> 422
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=_base_connection_payload(relation_type="fam.sibling_of", other_entity_id=a))
        assert r.status_code == 422, r.text

        # 404 entity/reference
        r = client.post(f"/api/v1/dossiers/entities/{a}/connections", json=_base_connection_payload(relation_type="fam.sibling_of", other_entity_id="00000000-0000-0000-0000-000000000000"))
        assert r.status_code == 404, r.text
    finally:
        app.dependency_overrides.clear()


def test_archived_not_reactivated_and_patch_rules(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        a = _create_entity(client, "A", "person")
        b = _create_entity(client, "B", "person")
        r = client.post(
            f"/api/v1/dossiers/entities/{a}/connections",
            json=_base_connection_payload(relation_type="fam.sibling_of", other_entity_id=b),
        )
        assert r.status_code == 201, r.text
        cid = r.json()["id"]

        arch = client.patch(f"/api/v1/dossiers/connections/{cid}", json={"status": "archived"})
        assert arch.status_code == 200, arch.text
        assert arch.json()["status"] == "archived"

        react = client.patch(f"/api/v1/dossiers/connections/{cid}", json={"status": "active"})
        assert react.status_code == 422, react.text

        # new record can be created for reestablished link (archived does not block by itself per rules)
        # but same semantic without disjoint/allowed condition and no temporal distinction -> conflicts (409) in our conservative model?
        # archived is excluded from conflict set (active/needs_review/inactive only), so creating equivalent new one is allowed.
        r2 = client.post(
            f"/api/v1/dossiers/entities/{a}/connections",
            json=_base_connection_payload(relation_type="fam.sibling_of", other_entity_id=b),
        )
        assert r2.status_code == 201, r2.text
    finally:
        app.dependency_overrides.clear()
