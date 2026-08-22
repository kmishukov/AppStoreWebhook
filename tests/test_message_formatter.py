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


@pytest.mark.parametrize("ownership_type", ["PURCHASED", "FAMILY_SHARED"])
def test_notification_message_includes_transaction_ownership(
    monkeypatch, ownership_type
):
    payload = {
        "notificationUUID": "notification-id",
        "signedDate": 1_704_067_200_000,
        "data": {
            "bundleId": "com.example.app",
            "appAppleId": 123456789,
            "environment": "Production",
            "signedTransactionInfo": "signed-transaction",
        },
    }
    monkeypatch.setattr(
        message_formatter,
        "validate_transaction_token",
        lambda *_args: {
            "transactionId": "transaction-id",
            "productId": "product-id",
            "inAppOwnershipType": ownership_type,
        },
    )

    message = message_formatter.format_notification_message("ONE_TIME_CHARGE", payload)

    assert "or received a non-consumable through Family Sharing" in message
    assert f"<code>Ownership:</code> {ownership_type}" in message
