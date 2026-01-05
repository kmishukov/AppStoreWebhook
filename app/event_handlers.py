"""
Handlers for different event types from App Store Server Notifications.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Notification types from Apple (human‑readable descriptions)
NOTIFICATION_TYPES = {
    "INITIAL_BUY": "First-time subscription purchase",
    "DID_RENEW": "Subscription renewed",
    "DID_FAIL_TO_RENEW": "Failed to renew subscription",
    "DID_CHANGE_RENEWAL_PREF": "Renewal preferences changed",
    "DID_CHANGE_RENEWAL_STATUS": "Auto-renewal status changed",
    "EXPIRED": "Subscription expired",
    "GRACE_PERIOD_EXPIRED": "Grace period expired",
    "REFUND": "Refund issued",
    "REVOKE": "Subscription revoked",
    "TEST": "Test notification",
}


def handle_initial_buy(payload: Dict[str, Any]) -> None:
    """Handle initial subscription purchase."""
    logger.info("Handling INITIAL_BUY: first-time subscription purchase")
    # TODO: Persist new subscription information
    # TODO: Enable premium features for the user
    pass


def handle_did_renew(payload: Dict[str, Any]) -> None:
    """Handle subscription renewal."""
    logger.info("Handling DID_RENEW: subscription successfully renewed")
    # TODO: Update subscription expiration date
    # TODO: Keep premium features enabled
    pass


def handle_did_fail_to_renew(payload: Dict[str, Any]) -> None:
    """Handle failed subscription renewal."""
    logger.warning("Handling DID_FAIL_TO_RENEW: failed to renew subscription")
    # TODO: Mark billing issue
    # TODO: Notify the user about payment problem
    pass


def handle_did_change_renewal_pref(payload: Dict[str, Any]) -> None:
    """Handle change of renewal preferences."""
    logger.info("Handling DID_CHANGE_RENEWAL_PREF: renewal preferences changed")
    # TODO: Update subscription product information
    pass


def handle_did_change_renewal_status(payload: Dict[str, Any]) -> None:
    """Handle change of auto-renewal status."""
    logger.info("Handling DID_CHANGE_RENEWAL_STATUS: auto-renewal status changed")
    # TODO: Update auto-renewal status
    pass


def handle_expired(payload: Dict[str, Any]) -> None:
    """Handle subscription expiration."""
    logger.warning("Handling EXPIRED: subscription expired")
    # TODO: Disable premium features
    # TODO: Notify the user about expiration
    pass


def handle_grace_period_expired(payload: Dict[str, Any]) -> None:
    """Handle grace period expiration."""
    logger.warning("Handling GRACE_PERIOD_EXPIRED: grace period expired")
    # TODO: Fully deactivate subscription if not renewed
    pass


def handle_refund(payload: Dict[str, Any]) -> None:
    """Handle refund event."""
    logger.warning("Handling REFUND: refund issued")
    # TODO: Deactivate subscription
    # TODO: Store refund information
    pass


def handle_revoke(payload: Dict[str, Any]) -> None:
    """Handle subscription revocation."""
    logger.warning("Handling REVOKE: subscription revoked")
    # TODO: Deactivate subscription
    pass


def handle_test(payload: Dict[str, Any]) -> None:
    """Handle test notification."""
    logger.info("Handling TEST: received test notification from Apple")
    # Test notifications usually require logging only
    pass


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

