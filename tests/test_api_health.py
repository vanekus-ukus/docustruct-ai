from __future__ import annotations

from docustruct_ai.api.routes.health import health


def test_health_endpoint(db_session) -> None:
    response = health(db_session)
    assert response.status in {"ok", "degraded"}
    assert response.database in {"ok", "error"}
