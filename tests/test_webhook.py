from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "appstore-webhook"}


def test_webhook_invalid_json():
    response = client.post(
        "/v1/webhook", content=b"not-json", headers={"content-type": "application/json"}
    )

    assert response.status_code == 400


def test_webhook_missing_signed_payload():
    response = client.post("/v1/webhook", json={})

    assert response.status_code == 400
    assert "signedPayload" in response.json()["detail"]


def test_webhook_invalid_jwt():
    response = client.post("/v1/webhook", json={"signedPayload": "not-a-jwt"})

    assert response.status_code == 401


def test_webhook_missing_notification_type(monkeypatch):
    monkeypatch.setattr(
        "app.main.validate_jwt_token",
        lambda _token: {"notificationUUID": "abc-123"},
    )

    response = client.post("/v1/webhook", json={"signedPayload": "valid-token"})

    assert response.status_code == 400


def test_webhook_success(monkeypatch):
    monkeypatch.setattr("app.main.process_notification", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "app.main.validate_jwt_token",
        lambda _token: {
            "notificationType": "TEST",
            "notificationUUID": "abc-123",
        },
    )

    response = client.post("/v1/webhook", json={"signedPayload": "valid-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["notification_type"] == "TEST"
