"""
Handlers for different event types from App Store Server Notifications.
"""
import logging
from typing import Dict, Any
from app.tg.alert import send_message
from app.message_formatter import format_notification_message

logger = logging.getLogger(__name__)


def handle_initial_buy(payload: Dict[str, Any]) -> None:
    """Handle initial subscription purchase."""
    logger.info("Handling INITIAL_BUY: first-time subscription purchase")
    message = format_notification_message("INITIAL_BUY", payload)
    send_message(message)


def handle_did_renew(payload: Dict[str, Any]) -> None:
    """Handle subscription renewal."""
    logger.info("Handling DID_RENEW: subscription successfully renewed")
    message = format_notification_message("DID_RENEW", payload)
    send_message(message)


def handle_did_fail_to_renew(payload: Dict[str, Any]) -> None:
    """Handle failed subscription renewal."""
    logger.warning("Handling DID_FAIL_TO_RENEW: failed to renew subscription")
    message = format_notification_message("DID_FAIL_TO_RENEW", payload)
    send_message(message)


def handle_did_change_renewal_pref(payload: Dict[str, Any]) -> None:
    """Handle change of renewal preferences."""
    logger.info("Handling DID_CHANGE_RENEWAL_PREF: renewal preferences changed")
    message = format_notification_message("DID_CHANGE_RENEWAL_PREF", payload)
    send_message(message)


def handle_did_change_renewal_status(payload: Dict[str, Any]) -> None:
    """Handle change of auto-renewal status."""
    logger.info("Handling DID_CHANGE_RENEWAL_STATUS: auto-renewal status changed")
    message = format_notification_message("DID_CHANGE_RENEWAL_STATUS", payload)
    send_message(message)


def handle_expired(payload: Dict[str, Any]) -> None:
    """Handle subscription expiration."""
    logger.warning("Handling EXPIRED: subscription expired")
    message = format_notification_message("EXPIRED", payload)
    send_message(message)


def handle_grace_period_expired(payload: Dict[str, Any]) -> None:
    """Handle grace period expiration."""
    logger.warning("Handling GRACE_PERIOD_EXPIRED: grace period expired")
    message = format_notification_message("GRACE_PERIOD_EXPIRED", payload)
    send_message(message)


def handle_refund(payload: Dict[str, Any]) -> None:
    """Handle refund event."""
    logger.warning("Handling REFUND: refund issued")
    message = format_notification_message("REFUND", payload)
    send_message(message)


def handle_revoke(payload: Dict[str, Any]) -> None:
    """Handle subscription revocation."""
    logger.warning("Handling REVOKE: subscription revoked")
    message = format_notification_message("REVOKE", payload)
    send_message(message)


def handle_test(payload: Dict[str, Any]) -> None:
    """Handle test notification."""
    logger.info("Handling TEST: received test notification from Apple")
    message = format_notification_message("TEST", payload)
    send_message(message)


# Mapping of notification types to handlers
EVENT_HANDLERS = {
    "INITIAL_BUY": handle_initial_buy,
    "DID_RENEW": handle_did_renew,
    "DID_FAIL_TO_RENEW": handle_did_fail_to_renew,
    "DID_CHANGE_RENEWAL_PREF": handle_did_change_renewal_pref,
    "DID_CHANGE_RENEWAL_STATUS": handle_did_change_renewal_status,
    "EXPIRED": handle_expired,
    "GRACE_PERIOD_EXPIRED": handle_grace_period_expired,
    "REFUND": handle_refund,
    "REVOKE": handle_revoke,
    "TEST": handle_test,
}


def process_notification(notification_type: str, payload: Dict[str, Any]) -> None:
    """
    Process incoming notification depending on its type.
    
    Args:
        notification_type: Notification type (e.g. "INITIAL_BUY")
        payload: Decoded notification payload
    """
    handler = EVENT_HANDLERS.get(notification_type)
    
    if handler:
        try:
            handler(payload)
            logger.info(f"Successfully processed notification of type {notification_type}")
        except Exception as e:
            logger.error(f"Error while processing notification {notification_type}: {e}", exc_info=True)
    else:
        logger.warning(f"Unknown notification type: {notification_type}")

