from __future__ import annotations

from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.knowledge.models.domain import (
    AuditEvent,
    DataChange,
    Entity,
    EntityAlias,
    EntityIdentifier,
)
from app.main import app


def _upgrade_tmp_db(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "dossiers_test.db"
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


def _base_person() -> dict:
    return {
        "entity_type": "person",
        "canonical_name": "Maria Silva",
        "description": "Executiva do setor financeiro",
        "primary_location": "São Paulo, SP",
        "profile_status": "active",
        "verification_status": "nao_verificado",
        "profile_data": {"occupation": "Diretora", "specialization": "Private Banking"},
        "identifiers": [
            {"id_type": "email_ref", "value": "maria@example.com", "is_primary": True}
        ],
        "aliases": [{"name": "M. Silva", "alias_type": "alternate"}],
    }


def test_d1_migration_creates_entity_profile_tables(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    with SessionLocal() as db:
        table_names = {
            row[0]
            for row in db.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).all()
        }
        assert "entities" in table_names
        assert "entity_identifiers" in table_names
        assert "entity_aliases" in table_names
        # ensure auxiliary tables and new columns are usable
        assert db.execute(select(EntityIdentifier)).scalars().all() == []
        assert db.execute(select(EntityAlias)).scalars().all() == []
        e = Entity(
            entity_type="other",
            canonical_name="X",
            normalized_name="x",
            profile_status="active",
            description="d",
            primary_location="loc",
            profile_data={"k": "v"},
        )
        db.add(e)
        db.commit()
        db.refresh(e)
        assert e.id
        assert e.profile_status == "active"
        assert e.profile_data == {"k": "v"}


def test_create_get_list_update_entity(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        r = client.post("/api/v1/dossiers/entities", json=_base_person())
        assert r.status_code == 201, r.text
        created = r.json()
        assert created["entity_type"] == "person"
        assert created["canonical_name"] == "Maria Silva"
        assert created["normalized_name"] == "maria silva"
        assert created["profile_status"] == "active"
        assert created["description"] == "Executiva do setor financeiro"
        assert created["profile_data"]["occupation"] == "Diretora"
        assert len(created["identifiers"]) == 1
        assert created["identifiers"][0]["id_type"] == "email_ref"
        assert len(created["aliases"]) == 1
        assert created["aliases"][0]["normalized_name"] == "m silva"
        eid = created["id"]

        g = client.get(f"/api/v1/dossiers/entities/{eid}")
        assert g.status_code == 200
        assert g.json()["id"] == eid

        lst = client.get("/api/v1/dossiers/entities")
        assert lst.status_code == 200
        body = lst.json()
        assert body["total"] == 1
        assert body["items"][0]["id"] == eid

        upd = client.patch(
            f"/api/v1/dossiers/entities/{eid}",
            json={
                "description": "Executiva sênior",
                "profile_status": "pending",
                "aliases": [{"name": "Maria S.", "alias_type": "alternate"}],
                "identifiers": [
                    {
                        "id_type": "email_ref",
                        "value": "maria@example.com",
                        "is_primary": True,
                    },
                    {
                        "id_type": "linkedin",
                        "value": "https://linkedin.com/in/maria",
                        "is_primary": False,
                    },
                ],
            },
        )
        assert upd.status_code == 200, upd.text
        ub = upd.json()
        assert ub["description"] == "Executiva sênior"
        assert ub["profile_status"] == "pending"
        assert len(ub["aliases"]) == 1 and ub["aliases"][0]["name"] == "Maria S."
        assert len(ub["identifiers"]) == 2

        with SessionLocal() as db:
            audits = db.execute(
                select(AuditEvent).where(AuditEvent.target_id == eid)
            ).scalars().all()
            actions = {a.action for a in audits}
            assert "dossier.entity.create" in actions
            assert "dossier.entity.update" in actions
            changes = db.execute(
                select(DataChange).where(
                    DataChange.entity_id == eid,
                    DataChange.entity_table == "entities",
                )
            ).scalars().all()
            assert len(changes) >= 2
    finally:
        app.dependency_overrides.clear()


def test_search_filters_and_pagination(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        e1 = client.post("/api/v1/dossiers/entities", json=_base_person()).json()
        e2 = client.post(
            "/api/v1/dossiers/entities",
            json={
                "entity_type": "company",
                "canonical_name": "Alfa Participações",
                "aliases": [{"name": "Alfa Holding"}],
                "identifiers": [{"id_type": "domain", "value": "alfa.example.com"}],
                "profile_data": {"sector": "finance"},
            },
        ).json()
        e3 = client.post(
            "/api/v1/dossiers/entities",
            json={
                "entity_type": "institution",
                "canonical_name": "Banco Central",
                "profile_status": "archived",
            },
        ).json()

        # by name
        r = client.get("/api/v1/dossiers/entities", params={"q": "maria"})
        assert r.status_code == 200
        assert r.json()["total"] == 1 and r.json()["items"][0]["id"] == e1["id"]
        # by alias
        r = client.get("/api/v1/dossiers/entities", params={"q": "Holding"})
        assert r.json()["total"] == 1 and r.json()["items"][0]["id"] == e2["id"]
        # by identifier
        r = client.get("/api/v1/dossiers/entities", params={"q": "alfa.example"})
        assert r.json()["total"] == 1 and r.json()["items"][0]["id"] == e2["id"]
        # by type
        r = client.get("/api/v1/dossiers/entities", params={"entity_type": "company"})
        assert r.json()["total"] == 1
        # by profile_status
        r = client.get(
            "/api/v1/dossiers/entities", params={"profile_status": "archived"}
        )
        assert r.json()["total"] == 1 and r.json()["items"][0]["id"] == e3["id"]
        # pagination
        r = client.get(
            "/api/v1/dossiers/entities",
            params={"limit": 1, "offset": 0, "sort": "name_asc"},
        )
        assert r.json()["total"] == 3 and len(r.json()["items"]) == 1
        r2 = client.get(
            "/api/v1/dossiers/entities",
            params={"limit": 1, "offset": 1, "sort": "name_asc"},
        )
        assert len(r2.json()["items"]) == 1
        assert r.json()["items"][0]["id"] != r2.json()["items"][0]["id"]
    finally:
        app.dependency_overrides.clear()


def test_duplicate_candidates_detection_no_merge(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        a = client.post(
            "/api/v1/dossiers/entities",
            json={
                "entity_type": "company",
                "canonical_name": "Beta SA",
                "identifiers": [{"id_type": "cnpj", "value": "12.345.678/0001-90"}],
                "aliases": [{"name": "Beta S.A."}],
            },
        ).json()
        b = client.post(
            "/api/v1/dossiers/entities",
            json={
                "entity_type": "company",
                "canonical_name": "Beta S.A",
                "identifiers": [{"id_type": "cnpj", "value": "12345678000190"}],
            },
        ).json()
        c = client.post(
            "/api/v1/dossiers/entities",
            json={"entity_type": "company", "canonical_name": "Gamma Ltda"},
        ).json()

        r = client.get(
            f"/api/v1/dossiers/entities/{a['id']}/duplicate-candidates"
        )
        assert r.status_code == 200, r.text
        items = r.json()["items"]
        assert len(items) >= 1
        cand_ids = [i["candidate"]["id"] for i in items]
        assert b["id"] in cand_ids
        assert c["id"] not in cand_ids
        match = next(i for i in items if i["candidate"]["id"] == b["id"])
        assert match["score_level"] in {"high", "medium", "low"}
        assert len(match["reasons"]) >= 1

        # ensure no merge/mutation: still three entities
        lst = client.get("/api/v1/dossiers/entities")
        assert lst.json()["total"] == 3
    finally:
        app.dependency_overrides.clear()


def test_validation_and_not_found(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        r = client.post(
            "/api/v1/dossiers/entities",
            json={"entity_type": "person", "canonical_name": ""},
        )
        assert r.status_code == 422
        r = client.get("/api/v1/dossiers/entities/does-not-exist")
        assert r.status_code == 404
        r = client.patch(
            "/api/v1/dossiers/entities/does-not-exist",
            json={"description": "x"},
        )
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()
