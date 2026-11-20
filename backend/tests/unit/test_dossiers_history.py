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
from app.knowledge.models.domain import AuditEvent, DataChange, EntityInteraction
from app.main import app


def _upgrade_tmp_db(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "dossiers_d3_test.db"
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


def _create_entity(client: TestClient, name: str = "Entidade D3") -> str:
    resp = client.post(
        "/api/v1/dossiers/entities",
        json={"canonical_name": name, "entity_type": "person", "profile_status": "active"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_d3_migration_and_interaction_model(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    with SessionLocal() as db:
        # sanity: table exists and is queryable
        rows = db.execute(select(EntityInteraction)).scalars().all()
        assert rows == []


def test_interaction_crud_timeline_filters_and_traceability(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        entity_id = _create_entity(client, "Histórico Teste")
        now = datetime.now(timezone.utc)
        earlier = now - timedelta(days=10)
        later = now + timedelta(days=2)

        # create declared/observed interaction
        r1 = client.post(
            f"/api/v1/dossiers/entities/{entity_id}/interactions",
            json={
                "interaction_type": "meeting",
                "title": "Reunião inicial",
                "description": "Contato presencial",
                "nature": "declarado",
                "status": "registered",
                "occurred_at": earlier.isoformat(),
                "channel": "presencial",
                "location_text": "São Paulo",
                "participants_text": "Equipe A",
                "confidence": 0.7,
                "created_by": "tester",
            },
        )
        assert r1.status_code == 201, r1.text
        i1 = r1.json()
        assert i1["nature"] == "declarado"
        assert i1["interaction_type"] == "meeting"

        # create interpreted interaction (no auto promotion implied)
        r2 = client.post(
            f"/api/v1/dossiers/entities/{entity_id}/interactions",
            json={
                "interaction_type": "note",
                "title": "Interpretação de contexto",
                "nature": "interpretado",
                "status": "needs_review",
                "occurred_at": later.isoformat(),
                "justification": "Análise manual preliminar",
            },
        )
        assert r2.status_code == 201, r2.text
        i2 = r2.json()
        assert i2["nature"] == "interpretado"

        # create a_confirmar interaction
        r3 = client.post(
            f"/api/v1/dossiers/entities/{entity_id}/interactions",
            json={
                "interaction_type": "call",
                "title": "Ligação a confirmar",
                "nature": "a_confirmar",
                "occurred_at": now.isoformat(),
            },
        )
        assert r3.status_code == 201, r3.text
        i3 = r3.json()

        # list default (occurred_desc)
        lst = client.get(f"/api/v1/dossiers/entities/{entity_id}/interactions")
        assert lst.status_code == 200
        body = lst.json()
        assert body["total"] == 3
        ids = [x["id"] for x in body["items"]]
        assert ids[0] == i2["id"]  # later first

        # filter by nature
        declared = client.get(
            f"/api/v1/dossiers/entities/{entity_id}/interactions", params={"nature": "declarado"}
        ).json()
        assert declared["total"] == 1 and declared["items"][0]["id"] == i1["id"]

        # filter by status
        review = client.get(
            f"/api/v1/dossiers/entities/{entity_id}/interactions", params={"status": "needs_review"}
        ).json()
        assert review["total"] == 1 and review["items"][0]["id"] == i2["id"]

        # text search
        search = client.get(
            f"/api/v1/dossiers/entities/{entity_id}/interactions", params={"q": "confirmar"}
        ).json()
        assert search["total"] == 1 and search["items"][0]["id"] == i3["id"]

        # detail
        detail = client.get(f"/api/v1/dossiers/interactions/{i1['id']}")
        assert detail.status_code == 200
        assert detail.json()["participants_text"] == "Equipe A"

        # update (explicit status/nature change, traceable)
        upd = client.patch(
            f"/api/v1/dossiers/interactions/{i3['id']}",
            json={
                "status": "confirmed",
                "nature": "observado",
                "verification_status": "verificado",
            },
        )
        assert upd.status_code == 200
        assert upd.json()["status"] == "confirmed"
        assert upd.json()["nature"] == "observado"

        # summary
        summary = client.get(f"/api/v1/dossiers/entities/{entity_id}/interactions/summary")
        assert summary.status_code == 200
        s = summary.json()
        assert s["interactions_count"] == 3
        assert s["pending_confirmation_or_review"] >= 1
        assert "observado" in s["by_nature"]

        # traceability: audit_events and data_changes recorded
        with SessionLocal() as db:
            audits = db.execute(
                select(AuditEvent).where(AuditEvent.target_type == "entity_interaction")
            ).scalars().all()
            changes = db.execute(
                select(DataChange).where(DataChange.entity_table == "entity_interactions")
            ).scalars().all()
            assert len(audits) >= 4  # 3 creates + 1 update
            assert any(a.action == "dossier.interaction.create" for a in audits)
            assert any(a.action == "dossier.interaction.update" for a in audits)
            assert len(changes) >= 4
            assert any(c.change_type == "create" for c in changes)
            assert any(c.change_type == "update" for c in changes)
    finally:
        app.dependency_overrides.clear()


def test_interaction_validation_and_not_found(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        entity_id = _create_entity(client, "Validação D3")

        # invalid nature
        bad_nature = client.post(
            f"/api/v1/dossiers/entities/{entity_id}/interactions",
            json={"interaction_type": "meeting", "title": "X", "nature": "inventada"},
        )
        assert bad_nature.status_code == 422

        # missing required title
        bad_title = client.post(
            f"/api/v1/dossiers/entities/{entity_id}/interactions",
            json={"interaction_type": "meeting", "title": "", "nature": "declarado"},
        )
        assert bad_title.status_code == 422

        # invalid temporal range
        now = datetime.now(timezone.utc)
        bad_time = client.post(
            f"/api/v1/dossiers/entities/{entity_id}/interactions",
            json={
                "interaction_type": "meeting",
                "title": "Tempo inválido",
                "nature": "observado",
                "started_at": (now + timedelta(days=1)).isoformat(),
                "ended_at": now.isoformat(),
            },
        )
        assert bad_time.status_code == 422

        # entity not found
        nf = client.post(
            "/api/v1/dossiers/entities/00000000-0000-0000-0000-000000000000/interactions",
            json={"interaction_type": "meeting", "title": "X", "nature": "declarado"},
        )
        assert nf.status_code == 404

        # invalid optional reference (integrity validated)
        bad_ref = client.post(
            f"/api/v1/dossiers/entities/{entity_id}/interactions",
            json={
                "interaction_type": "meeting",
                "title": "Ref inválida",
                "nature": "declarado",
                "document_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert bad_ref.status_code == 404

        # interaction not found
        g = client.get("/api/v1/dossiers/interactions/00000000-0000-0000-0000-000000000000")
        assert g.status_code == 404
        p = client.patch(
            "/api/v1/dossiers/interactions/00000000-0000-0000-0000-000000000000",
            json={"status": "confirmed"},
        )
        assert p.status_code == 404
    finally:
        app.dependency_overrides.clear()
