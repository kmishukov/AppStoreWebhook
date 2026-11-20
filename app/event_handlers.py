"""
Handlers for different event types from App Store Server Notifications.
"""

import logging
from typing import Any

from app.message_formatter import format_notification_message
from app.tg.alert import send_message

logger = logging.getLogger(__name__)


def handle_subscribed(payload: dict[str, Any]) -> None:
    """Handle subscription activation (including resubscribe)."""
    subtype = payload.get("subtype", "")
    logger.info(f"Handling SUBSCRIBED: subscription activated (subtype: {subtype})")
    message = format_notification_message("SUBSCRIBED", payload)
    send_message(message)


def handle_did_renew(payload: dict[str, Any]) -> None:
    """Handle subscription renewal."""
    logger.info("Handling DID_RENEW: subscription successfully renewed")
    message = format_notification_message("DID_RENEW", payload)
    send_message(message)


def handle_did_fail_to_renew(payload: dict[str, Any]) -> None:
    """Handle failed subscription renewal."""
    logger.warning("Handling DID_FAIL_TO_RENEW: failed to renew subscription")
    message = format_notification_message("DID_FAIL_TO_RENEW", payload)
    send_message(message)


def handle_did_change_renewal_pref(payload: dict[str, Any]) -> None:
    """Handle change of renewal preferences."""
    logger.info("Handling DID_CHANGE_RENEWAL_PREF: renewal preferences changed")
    message = format_notification_message("DID_CHANGE_RENEWAL_PREF", payload)
    send_message(message)


def handle_did_change_renewal_status(payload: dict[str, Any]) -> None:
    """Handle change of auto-renewal status."""
    logger.info("Handling DID_CHANGE_RENEWAL_STATUS: auto-renewal status changed")
    message = format_notification_message("DID_CHANGE_RENEWAL_STATUS", payload)
    send_message(message)


def handle_expired(payload: dict[str, Any]) -> None:
    """Handle subscription expiration."""
    logger.warning("Handling EXPIRED: subscription expired")
    message = format_notification_message("EXPIRED", payload)
    send_message(message)


def handle_grace_period_expired(payload: dict[str, Any]) -> None:
    """Handle grace period expiration."""
    logger.warning("Handling GRACE_PERIOD_EXPIRED: grace period expired")
    message = format_notification_message("GRACE_PERIOD_EXPIRED", payload)
    send_message(message)


def handle_refund(payload: dict[str, Any]) -> None:
    """Handle refund event."""
    logger.warning("Handling REFUND: refund issued")
    message = format_notification_message("REFUND", payload)
    send_message(message)


def handle_revoke(payload: dict[str, Any]) -> None:
    """Handle subscription revocation."""
    logger.warning("Handling REVOKE: subscription revoked")
    message = format_notification_message("REVOKE", payload)
    send_message(message)


def handle_test(payload: dict[str, Any]) -> None:
    """Handle test notification."""
    logger.info("Handling TEST: received test notification from Apple")
    message = format_notification_message("TEST", payload)
    send_message(message)


def handle_consumption_request(payload: dict[str, Any]) -> None:
    """Handle consumption request for refund."""
    logger.info("Handling CONSUMPTION_REQUEST: App Store requesting consumption data")
    message = format_notification_message("CONSUMPTION_REQUEST", payload)
    send_message(message)


def handle_external_purchase_token(payload: dict[str, Any]) -> None:
    """Handle external purchase token notification."""
    logger.info(
        "Handling EXTERNAL_PURCHASE_TOKEN: external purchase token notification"
    )
    message = format_notification_message("EXTERNAL_PURCHASE_TOKEN", payload)
    send_message(message)


def handle_metadata_update(payload: dict[str, Any]) -> None:
    """Handle subscription metadata update."""
    logger.info("Handling METADATA_UPDATE: subscription metadata changed")
    message = format_notification_message("METADATA_UPDATE", payload)
    send_message(message)


def handle_migration(payload: dict[str, Any]) -> None:
    """Handle subscription migration."""
    logger.info("Handling MIGRATION: subscription migrated to Advanced Commerce API")
    message = format_notification_message("MIGRATION", payload)
    send_message(message)


def handle_offer_redeemed(payload: dict[str, Any]) -> None:
    """Handle offer redemption."""
    logger.info("Handling OFFER_REDEEMED: customer redeemed subscription offer")
    message = format_notification_message("OFFER_REDEEMED", payload)
    send_message(message)


def handle_one_time_charge(payload: dict[str, Any]) -> None:
    """Handle one-time charge (consumable/non-consumable purchase)."""
    logger.info("Handling ONE_TIME_CHARGE: one-time purchase")
    message = format_notification_message("ONE_TIME_CHARGE", payload)
    send_message(message)


def handle_price_change(payload: dict[str, Any]) -> None:
    """Handle subscription price change."""
    logger.info("Handling PRICE_CHANGE: subscription price changed")
    message = format_notification_message("PRICE_CHANGE", payload)
    send_message(message)


def handle_price_increase(payload: dict[str, Any]) -> None:
    """Handle subscription price increase notification."""
    logger.info("Handling PRICE_INCREASE: customer informed of price increase")
    message = format_notification_message("PRICE_INCREASE", payload)
    send_message(message)


def handle_refund_declined(payload: dict[str, Any]) -> None:
    """Handle declined refund request."""
    logger.warning("Handling REFUND_DECLINED: refund request declined")
    message = format_notification_message("REFUND_DECLINED", payload)
    send_message(message)


def handle_refund_reversed(payload: dict[str, Any]) -> None:
    """Handle reversed refund."""
    logger.warning("Handling REFUND_REVERSED: previously granted refund reversed")
    message = format_notification_message("REFUND_REVERSED", payload)
    send_message(message)


def handle_renewal_extended(payload: dict[str, Any]) -> None:
    """Handle subscription renewal date extension."""
    logger.info("Handling RENEWAL_EXTENDED: subscription renewal date extended")
    message = format_notification_message("RENEWAL_EXTENDED", payload)
    send_message(message)


def handle_renewal_extension(payload: dict[str, Any]) -> None:
    """Handle renewal extension attempt."""
    logger.info("Handling RENEWAL_EXTENSION: renewal date extension attempt")
    message = format_notification_message("RENEWAL_EXTENSION", payload)
    send_message(message)


def handle_rescind_consent(payload: dict[str, Any]) -> None:
    """Handle consent withdrawal for child's app usage."""
    logger.warning("Handling RESCIND_CONSENT: parent/guardian withdrew consent")
    message = format_notification_message("RESCIND_CONSENT", payload)
    send_message(message)


# Mapping of notification types to handlers
EVENT_HANDLERS = {
    "CONSUMPTION_REQUEST": handle_consumption_request,
    "DID_CHANGE_RENEWAL_PREF": handle_did_change_renewal_pref,
    "DID_CHANGE_RENEWAL_STATUS": handle_did_change_renewal_status,
    "DID_FAIL_TO_RENEW": handle_did_fail_to_renew,
    "DID_RENEW": handle_did_renew,
    "EXPIRED": handle_expired,
    "EXTERNAL_PURCHASE_TOKEN": handle_external_purchase_token,
    "GRACE_PERIOD_EXPIRED": handle_grace_period_expired,
    "METADATA_UPDATE": handle_metadata_update,
    "MIGRATION": handle_migration,
    "OFFER_REDEEMED": handle_offer_redeemed,
    "ONE_TIME_CHARGE": handle_one_time_charge,
    "PRICE_CHANGE": handle_price_change,
    "PRICE_INCREASE": handle_price_increase,
    "REFUND": handle_refund,
    "REFUND_DECLINED": handle_refund_declined,
    "REFUND_REVERSED": handle_refund_reversed,
    "RENEWAL_EXTENDED": handle_renewal_extended,
    "RENEWAL_EXTENSION": handle_renewal_extension,
    "RESCIND_CONSENT": handle_rescind_consent,
    "REVOKE": handle_revoke,
    "SUBSCRIBED": handle_subscribed,
    "TEST": handle_test,
}


def handle_unknown(payload: dict[str, Any], notification_type: str) -> None:
    """Handle unknown notification type."""
    logger.warning(f"Handling unknown notification type: {notification_type}")
    message = format_notification_message(notification_type, payload)
    send_message(message)


def process_notification(notification_type: str, payload: dict[str, Any]) -> None:
    """
    Process incoming notification depending on its type.

    Args:
        notification_type: Notification type (e.g. "SUBSCRIBED")
        payload: Decoded notification payload
    """
    handler = EVENT_HANDLERS.get(notification_type)

    if handler:
        try:
            handler(payload)
            logger.info(
                f"Successfully processed notification of type {notification_type}"
            )
        except Exception:
            logger.exception(f"Error while processing notification {notification_type}")
    else:
        # Handle unknown types - still send notification to Telegram
        logger.warning(
            f"Unknown notification type: {notification_type}, sending anyway"
        )
        try:
            handle_unknown(payload, notification_type)
        except Exception:
            logger.exception(
                f"Error while handling unknown notification type {notification_type}"
            )
