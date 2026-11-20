from __future__ import annotations

from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.knowledge.models.domain import (
    AuditEvent,
    ClaimConflict,
    ClaimEntityLink,
    DataChange,
    Document,
    DocumentEntityLink,
    Evidence,
    ExtractedClaim,
    ResearchSource,
)
from app.main import app


def _upgrade_tmp_db(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "dossiers_d2_test.db"
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


def _create_entity(client: TestClient, name: str = "Empresa Alfa") -> str:
    r = client.post(
        "/api/v1/dossiers/entities",
        json={"entity_type": "company", "canonical_name": name},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_d2_migration_creates_research_tables_and_columns(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    with SessionLocal() as db:
        tables = {
            row[0]
            for row in db.execute(
                __import__("sqlalchemy").text(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            ).all()
        }
        for t in [
            "research_sources",
            "document_entity_links",
            "claim_entity_links",
            "claim_conflicts",
        ]:
            assert t in tables
        # ensure extended columns are usable
        rs = ResearchSource(name="Fonte X", source_type="site")
        db.add(rs)
        db.flush()
        assert rs.reliability_status == "nao_avaliada"
        doc = Document(title="Doc", origin_type="manual", source_locator="ref://1")
        db.add(doc)
        db.flush()
        link = DocumentEntityLink(document_id=doc.id, entity_id=_create_entity_via_db(db))
        db.add(link)
        db.commit()


def _create_entity_via_db(db: Session) -> str:
    from app.knowledge.models.domain import Entity

    e = Entity(entity_type="company", canonical_name="E", normalized_name="e")
    db.add(e)
    db.flush()
    return e.id


def test_research_source_crud_and_traceability(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        created = client.post(
            "/api/v1/dossiers/research-sources",
            json={
                "name": "Portal Público",
                "source_type": "site",
                "domain": "example.gov",
                "url": "https://example.gov/info",
                "reliability_status": "alta",
                "reliability_justification": "Fonte oficial",
            },
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["name"] == "Portal Público"
        assert body["reliability_status"] == "alta"
        sid = body["id"]

        listing = client.get("/api/v1/dossiers/research-sources", params={"q": "Portal"})
        assert listing.status_code == 200
        assert listing.json()["total"] == 1

        detail = client.get(f"/api/v1/dossiers/research-sources/{sid}")
        assert detail.status_code == 200

        upd = client.patch(
            f"/api/v1/dossiers/research-sources/{sid}",
            json={"verification_status": "verificado", "classification": "oficial"},
        )
        assert upd.status_code == 200
        assert upd.json()["verification_status"] == "verificado"
        assert upd.json()["classification"] == "oficial"

        with SessionLocal() as db:
            audits = db.execute(
                select(AuditEvent).where(AuditEvent.target_id == sid)
            ).scalars().all()
            actions = {a.action for a in audits}
            assert "dossier.research_source.create" in actions
            assert "dossier.research_source.update" in actions
            changes = db.execute(
                select(DataChange).where(DataChange.entity_id == sid)
            ).scalars().all()
            assert len(changes) >= 2
    finally:
        app.dependency_overrides.clear()


def test_document_create_list_requires_anchor_and_links_entity(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        eid = _create_entity(client)

        # missing anchor
        bad = client.post(
            f"/api/v1/dossiers/entities/{eid}/documents",
            json={"title": "Sem ancora"},
        )
        assert bad.status_code == 422

        ok = client.post(
            f"/api/v1/dossiers/entities/{eid}/documents",
            json={
                "title": "Relatório Público",
                "document_type": "relatorio",
                "source_locator": "https://example.com/relatorio.pdf",
                "origin_type": "manual",
                "is_reference_only": True,
                "verification_status": "nao_verificado",
            },
        )
        assert ok.status_code == 201, ok.text
        doc = ok.json()
        assert doc["title"] == "Relatório Público"
        assert doc["is_reference_only"] is True
        assert any(link["entity_id"] == eid for link in doc["entity_links"])
        did = doc["id"]

        lst = client.get(f"/api/v1/dossiers/entities/{eid}/documents")
        assert lst.status_code == 200
        assert lst.json()["total"] == 1
        assert lst.json()["items"][0]["id"] == did

        detail = client.get(f"/api/v1/dossiers/documents/{did}")
        assert detail.status_code == 200

        upd = client.patch(
            f"/api/v1/dossiers/documents/{did}",
            json={"verification_status": "em_verificacao", "description": "Atualizado"},
        )
        assert upd.status_code == 200
        assert upd.json()["verification_status"] == "em_verificacao"

        with SessionLocal() as db:
            assert db.get(Document, did) is not None
            links = db.execute(
                select(DocumentEntityLink).where(DocumentEntityLink.document_id == did)
            ).scalars().all()
            assert len(links) == 1
            audits = db.execute(
                select(AuditEvent).where(AuditEvent.target_id == did)
            ).scalars().all()
            assert any(a.action == "dossier.document.create" for a in audits)
    finally:
        app.dependency_overrides.clear()


def test_claim_evidence_conflict_and_summary(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        eid = _create_entity(client, "Pessoa Beta")
        rs = client.post(
            "/api/v1/dossiers/research-sources",
            json={"name": "Fonte Notícia", "source_type": "noticia", "url": "https://n.example"},
        ).json()
        doc = client.post(
            f"/api/v1/dossiers/entities/{eid}/documents",
            json={
                "title": "Matéria",
                "source_locator": "https://n.example/m",
                "research_source_id": rs["id"],
            },
        ).json()

        # epistemic guard: inferential claim marked verified requires justification
        bad_claim = client.post(
            f"/api/v1/dossiers/entities/{eid}/claims",
            json={
                "claim_text": "Hipótese sem base explícita",
                "claim_type": "hipotese",
                "verification_status": "verificado",
            },
        )
        assert bad_claim.status_code == 422

        c1 = client.post(
            f"/api/v1/dossiers/entities/{eid}/claims",
            json={
                "claim_text": "Afirmação declarada A",
                "claim_type": "declaracao",
                "verification_status": "nao_verificado",
                "document_id": doc["id"],
                "research_source_id": rs["id"],
            },
        )
        assert c1.status_code == 201, c1.text
        claim1 = c1.json()
        assert claim1["claim_type"] == "declaracao"
        assert claim1["conflict_status"] == "none"

        c2 = client.post(
            f"/api/v1/dossiers/entities/{eid}/claims",
            json={
                "claim_text": "Afirmação contraditória B",
                "claim_type": "declaracao",
                "verification_status": "nao_verificado",
            },
        )
        assert c2.status_code == 201
        claim2 = c2.json()

        ev = client.post(
            f"/api/v1/dossiers/claims/{claim1['id']}/evidence",
            json={
                "relation_type": "supports",
                "evidence_type": "trecho",
                "excerpt": "Trecho de apoio",
                "locator": "p. 1",
                "document_id": doc["id"],
                "research_source_id": rs["id"],
            },
        )
        assert ev.status_code == 201, ev.text
        assert ev.json()["relation_type"] == "supports"

        conflict = client.post(
            f"/api/v1/dossiers/claims/{claim1['id']}/conflicts",
            json={
                "conflicting_claim_id": claim2["id"],
                "conflict_type": "contradicao",
                "description": "Informações divergentes",
                "status": "open",
            },
        )
        assert conflict.status_code == 201, conflict.text

        # conflict reflected in list and claim state
        conflicts = client.get(f"/api/v1/dossiers/entities/{eid}/conflicts")
        assert conflicts.status_code == 200
        assert conflicts.json()["total"] == 1

        claim1_detail = client.get(f"/api/v1/dossiers/claims/{claim1['id']}")
        assert claim1_detail.status_code == 200
        assert claim1_detail.json()["conflict_status"] == "conflicting"
        assert len(claim1_detail.json()["evidence"]) == 1
        assert len(claim1_detail.json()["conflicts"]) == 1

        # resolve conflict
        cid = conflict.json()["id"]
        upd_conf = client.patch(
            f"/api/v1/dossiers/claims/{claim1['id']}/conflicts/{cid}",
            json={"status": "resolved"},
        )
        assert upd_conf.status_code == 200
        claim1_after = client.get(f"/api/v1/dossiers/claims/{claim1['id']}").json()
        assert claim1_after["conflict_status"] == "none"

        summary = client.get(f"/api/v1/dossiers/entities/{eid}/research/summary")
        assert summary.status_code == 200, summary.text
        s = summary.json()
        assert s["documents_count"] == 1
        assert s["claims_count"] == 2
        assert s["evidence_count"] == 1
        assert s["research_sources_count"] >= 1
        assert s["open_conflicts"] == 0
        assert s["claims_by_type"].get("declaracao") == 2

        with SessionLocal() as db:
            assert db.get(ExtractedClaim, claim1["id"]) is not None
            assert db.get(Evidence, ev.json()["id"]) is not None
            assert db.get(ClaimConflict, cid) is not None
            links = db.execute(
                select(ClaimEntityLink).where(ClaimEntityLink.claim_id == claim1["id"])
            ).scalars().all()
            assert len(links) >= 1
            # traceability
            audits = db.execute(
                select(AuditEvent).where(
                    AuditEvent.target_type.in_(["claim", "evidence", "claim_conflict"])
                )
            ).scalars().all()
            actions = {a.action for a in audits}
            assert "dossier.claim.create" in actions
            assert "dossier.evidence.create" in actions
            assert "dossier.claim_conflict.create" in actions
    finally:
        app.dependency_overrides.clear()
