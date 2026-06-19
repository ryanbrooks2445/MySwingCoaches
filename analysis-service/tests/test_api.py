from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_is_public_and_fast() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_job_drain_rejects_invalid_shared_secret() -> None:
    response = client.post("/jobs/drain", headers={"X-Analysis-Secret": "wrong"})

    assert response.status_code == 401
