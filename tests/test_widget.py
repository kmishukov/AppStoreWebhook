"""Tests for the opt-in Telegram HTML widget transport."""

import asyncio
import zlib

import pytest

from app.tg import widget_sender
from app.tg.widget import render_notification_widget


def _payload():
    return {
        "notificationType": "ONE_TIME_CHARGE",
        "notificationUUID": "test-uuid",
        "subtype": "INITIAL_BUY",
        "data": {
            "bundleId": "com.example.app",
            "environment": "Sandbox",
            "signedTransactionInfo": "secret-jws",
        },
    }


def test_widget_escapes_untrusted_values():
    payload = _payload()
    payload["data"]["bundleId"] = '<script>alert("x")</script>'
    widget = render_notification_widget(payload)
    assert "&lt;script&gt;" in widget
    assert "<script>alert" not in widget
    assert "secret-jws" not in widget
    assert len(widget.encode()) <= 32768
    assert len(zlib.compress(widget.encode(), level=9)) <= 4096


def test_widget_rejects_excessive_content():
    payload = _payload()
    payload["data"]["bundleId"] = "".join(chr(0x4E00 + i % 20000) for i in range(30000))
    with pytest.raises(ValueError, match="size limits"):
        render_notification_widget(payload)


def test_mode_defaults_to_text(monkeypatch):
    monkeypatch.delenv("TELEGRAM_MESSAGE_MODE", raising=False)
    assert widget_sender.get_message_mode() == "text"


def test_mode_invalid_fails_fast(monkeypatch):
    monkeypatch.setenv("TELEGRAM_MESSAGE_MODE", "other")
    with pytest.raises(ValueError, match="TELEGRAM_MESSAGE_MODE"):
        widget_sender.get_message_mode()


def test_text_mode_uses_legacy_sender(monkeypatch):
    sent = []
    monkeypatch.setenv("TELEGRAM_MESSAGE_MODE", "text")
    monkeypatch.setattr(widget_sender, "send_message", sent.append)
    widget_sender.send_notification("legacy message", _payload())
    assert sent == ["legacy message"]


def test_failed_widget_delivery_falls_back_to_text(monkeypatch):
    sent = []

    class FakeResponse:
        def raise_for_status(self):
            raise RuntimeError("unexpected server response")

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def post(self, *_args, **_kwargs):
            return FakeResponse()

    class FakeConfig:
        def get_token(self):
            return "test-token"

        def get_chat_id(self):
            return 123456

    monkeypatch.setattr(widget_sender, "Configuration", FakeConfig)
    monkeypatch.setattr(widget_sender.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(widget_sender, "send_message", sent.append)

    asyncio.run(widget_sender._send_widget_with_fallback("legacy", "<b>widget</b>"))
    assert sent == ["legacy"]


def test_purchase_title_navy_design_and_disclosure():
    markup = render_notification_widget(_payload())
    assert "<h1>Purchase</h1>" in markup
    assert "#003764" in markup
    assert "radial-gradient" in markup
    assert "<details>" in markup
    assert "ONE_TIME_CHARGE" in markup
    assert "secret-jws" not in markup


@pytest.mark.parametrize(
    ("event_type", "expected"),
    [
        ("SUBSCRIBED", "<h1>New subscription</h1>"),
        ("DID_RENEW", "<h1>Renewal</h1>"),
        ("REFUND", "<h1>Refund</h1>"),
        ("SOME_NEW_EVENT", "<h1>Some New Event</h1>"),
    ],
)
def test_human_readable_event_labels(event_type, expected):
    payload = _payload()
    payload["notificationType"] = event_type
    assert expected in render_notification_widget(payload)


def test_verified_transaction_information(monkeypatch):
    def fake_verify(*_args):
        return {
            "productId": "com.example.app.unlock_pro",
            "storefront": "USA",
            "inAppOwnershipType": "FAMILY_SHARED",
        }

    monkeypatch.setattr("app.tg.widget.validate_transaction_token", fake_verify)
    markup = render_notification_widget(_payload())
    assert "Unlock Pro" in markup
    assert "Family Sharing" in markup
    assert "USA" in markup
    assert "com.example.app.unlock_pro" in markup
