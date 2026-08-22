import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_startup_rejects_missing_telegram_configuration(monkeypatch):
    monkeypatch.delenv("TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(ValueError, match="TOKEN"), TestClient(app):
        pass


def test_httpx_request_logging_is_suppressed():
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING


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


def test_webhook_logs_only_safe_notification_metadata(monkeypatch, caplog):
    monkeypatch.setattr("app.main.process_notification", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "app.main.validate_jwt_token",
        lambda _token: {
            "notificationType": "DID_RENEW",
            "notificationUUID": "abc-123",
            "subtype": "INITIAL_BUY",
            "data": {
                "bundleId": "com.example.app",
                "environment": "Sandbox",
                "signedTransactionInfo": "sensitive-transaction-jws",
            },
        },
    )

    with caplog.at_level(logging.INFO, logger="app.main"):
        response = client.post(
            "/v1/webhook", json={"signedPayload": "sensitive-notification-jws"}
        )

    assert response.status_code == 200
    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "uuid=abc-123" in messages
    assert "type=DID_RENEW" in messages
    assert "bundle_id=com.example.app" in messages
    assert "environment=Sandbox" in messages
    assert "sensitive-notification-jws" not in messages
    assert "sensitive-transaction-jws" not in messages
