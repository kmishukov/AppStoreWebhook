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
    assert '&lt;script&gt;' in widget
    assert '<script>alert' not in widget
    assert "secret-jws" not in widget
    assert len(widget.encode()) <= 32768
    assert len(zlib.compress(widget.encode(), level=9)) <= 4096


def test_widget_rejects_excessive_content():
    payload = _payload()
    payload["data"]["bundleId"] = "".join(
        chr(0x4E00 + i % 20000) for i in range(30000)
    )
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
