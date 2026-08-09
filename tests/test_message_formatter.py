from zoneinfo import ZoneInfoNotFoundError

import pytest

from app import message_formatter


def test_default_timezone_is_new_york(monkeypatch):
    monkeypatch.delenv("TIMEZONE", raising=False)
    message_formatter.get_timezone.cache_clear()

    try:
        timezone = message_formatter.get_timezone()
    finally:
        message_formatter.get_timezone.cache_clear()

    assert timezone.key == "America/New_York"


def test_format_timestamp_uses_configured_timezone(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "America/New_York")
    message_formatter.get_timezone.cache_clear()

    try:
        formatted = message_formatter.format_timestamp(1_704_067_200_000)
    finally:
        message_formatter.get_timezone.cache_clear()

    assert formatted == "2023-12-31 19:00:00 EST"


def test_invalid_timezone_is_rejected(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Invalid/Timezone")
    message_formatter.get_timezone.cache_clear()

    try:
        with pytest.raises(ZoneInfoNotFoundError):
            message_formatter.validate_message_formatter_configuration()
    finally:
        message_formatter.get_timezone.cache_clear()


def test_notification_message_escapes_dynamic_html():
    payload = {
        "notificationUUID": "uuid<&>",
        "subtype": "sub<&>",
        "data": {
            "bundleId": "com.example.<app>&",
            "environment": "Sandbox<&>",
        },
    }

    message = message_formatter.format_notification_message("UNKNOWN<&>", payload)

    assert "UNKNOWN&lt;&amp;&gt;" in message
    assert "uuid&lt;&amp;&gt;" in message
    assert "sub&lt;&amp;&gt;" in message
    assert "com.example.&lt;app&gt;&amp;" in message
    assert "Sandbox&lt;&amp;&gt;" in message
    assert "uuid<&>" not in message
