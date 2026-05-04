import sys

import pytest
from fastapi.testclient import TestClient


class FakePipeline:
    def __init__(self):
        self.executions = []
        self.queries = []

    def execute(self, user_id, podcast_id, audio_input_path):
        vault_path = f"storage/users/{user_id}/indices/{podcast_id}"
        self.executions.append(
            {
                "user_id": user_id,
                "podcast_id": podcast_id,
                "audio_input_path": audio_input_path,
                "vault_path": vault_path,
            }
        )
        return {
            "language": "en",
            "duration": 12.5,
            "speaker_count": 2,
            "summary": "Fake podcast summary",
            "vault_path": vault_path,
        }

    def ask_ai(self, question, vault_path=None):
        self.queries.append({"question": question, "vault_path": vault_path})
        return f"Answer from {vault_path}: {question}"


def clear_backend_modules():
    for module_name in list(sys.modules):
        if module_name == "backend" or module_name.startswith("backend."):
            del sys.modules[module_name]


@pytest.fixture()
def client_with_pipeline(tmp_path, monkeypatch):
    clear_backend_modules()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path / "storage"))
    monkeypatch.setenv("DEBUG", "false")

    from backend.main import app
    from backend.routers.ingest import set_pipeline

    fake_pipeline = FakePipeline()

    with TestClient(app) as client:
        set_pipeline(fake_pipeline)
        yield client, fake_pipeline


def register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    return tokens


def test_authenticated_upload_job_vault_and_query_flow(client_with_pipeline):
    client, fake_pipeline = client_with_pipeline
    tokens = register_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    upload_response = client.post(
        "/ingest/upload",
        headers=headers,
        data={"title": "Episode 1"},
        files={"file": ("episode.mp3", b"fake audio bytes", "audio/mpeg")},
    )
    assert upload_response.status_code == 202
    job_id = upload_response.json()["job_id"]

    job_response = client.get(f"/ingest/jobs/{job_id}", headers=headers)
    assert job_response.status_code == 200
    assert job_response.json()["status"] == "completed"

    vault_response = client.get("/vaults/", headers=headers)
    assert vault_response.status_code == 200
    podcasts = vault_response.json()["podcasts"]
    assert len(podcasts) == 1
    assert podcasts[0]["title"] == "Episode 1"
    assert podcasts[0]["summary"] == "Fake podcast summary"
    assert podcasts[0]["speaker_count"] == 2

    query_response = client.post(
        "/query/ask",
        headers=headers,
        json={"podcast_id": podcasts[0]["id"], "question": "What was discussed?"},
    )
    assert query_response.status_code == 200
    assert "What was discussed?" in query_response.json()["answer"]
    assert fake_pipeline.queries == [
        {
            "question": "What was discussed?",
            "vault_path": "storage/users/1/indices/1",
        }
    ]


def test_refresh_and_logout_flow(client_with_pipeline):
    client, _ = client_with_pipeline
    tokens = register_and_login(client)

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]

    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout_response.status_code == 200

    revoked_refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert revoked_refresh_response.status_code == 401


def test_upload_rejects_missing_title(client_with_pipeline):
    client, _ = client_with_pipeline
    tokens = register_and_login(client)

    response = client.post(
        "/ingest/upload",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("episode.mp3", b"fake audio bytes", "audio/mpeg")},
    )
    assert response.status_code == 422
