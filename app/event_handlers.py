"""
Handlers for different event types from App Store Server Notifications.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.tg.alert import send_message
from app.jwt_validator import validate_jwt_token

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


def format_timestamp(timestamp: Optional[int]) -> str:
    """Format Unix timestamp to readable date."""
    if not timestamp:
        return "N/A"
    try:
        return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return str(timestamp)


def format_notification_message(notification_type: str, payload: Dict[str, Any]) -> str:
    """
    Format notification message in unified HTML style.
    
    Args:
        notification_type: Type of notification
        payload: Decoded notification payload
        
    Returns:
        Formatted HTML message
    """
    notification_desc = NOTIFICATION_TYPES.get(notification_type, notification_type)
    notification_uuid = payload.get("notificationUUID", "N/A")
    bundle_id = payload.get("data", {}).get("bundleId", "N/A")
    subtype = payload.get("subtype")
    signed_date = payload.get("signedDate")
    environment = payload.get("data", {}).get("environment", "Unknown")
    
    # Build message header
    message_parts = [
        f"<b>📱 App Store Notification</b>",
        "",
        f"<b>Type:</b> <code>{notification_type}</code>",
        f"<b>Description:</b> {notification_desc}",
    ]
    
    if subtype:
        message_parts.append(f"<b>Subtype:</b> <code>{subtype}</code>")
    
    message_parts.extend([
        f"<b>UUID:</b> <code>{notification_uuid}</code>",
        f"<b>Bundle ID:</b> <code>{bundle_id}</code>",
        f"<b>Environment:</b> <code>{environment}</code>",
        f"<b>Date:</b> <code>{format_timestamp(signed_date)}</code>",
    ])
    
    # Extract transaction info if available
    data = payload.get("data", {})
    if "signedTransactionInfo" in data:
        message_parts.append("")
        message_parts.append("<b>Transaction Info:</b>")
        try:
            transaction_jwt = data.get("signedTransactionInfo")
            if transaction_jwt:
                decoded_tx = validate_jwt_token(transaction_jwt)
                if decoded_tx:
                    tx_id = decoded_tx.get("transactionId", "N/A")
                    product_id = decoded_tx.get("productId", "N/A")
                    purchase_date = decoded_tx.get("purchaseDate")
                    expires_date = decoded_tx.get("expiresDate")
                    message_parts.append(f"<code>Transaction ID:</code> {tx_id}")
                    message_parts.append(f"<code>Product ID:</code> {product_id}")
                    if purchase_date:
                        message_parts.append(f"<code>Purchase:</code> {format_timestamp(purchase_date)}")
                    if expires_date:
                        message_parts.append(f"<code>Expires:</code> {format_timestamp(expires_date)}")
                else:
                    message_parts.append("<i>JWT decode failed</i>")
        except Exception as e:
            logger.warning(f"Failed to decode transaction info: {e}")
            message_parts.append("<i>JWT decode error</i>")
    
    # Extract renewal info if available
    if "signedRenewalInfo" in data:
        message_parts.append("")
        message_parts.append("<b>Renewal Info:</b>")
        try:
            renewal_jwt = data.get("signedRenewalInfo")
            if renewal_jwt:
                decoded_renewal = validate_jwt_token(renewal_jwt)
                if decoded_renewal:
                    auto_renew = decoded_renewal.get("autoRenewStatus", 0)
                    product_id = decoded_renewal.get("autoRenewProductId", "N/A")
                    message_parts.append(f"<code>Auto-renew:</code> {'Enabled' if auto_renew == 1 else 'Disabled'}")
                    message_parts.append(f"<code>Product ID:</code> {product_id}")
                else:
                    message_parts.append("<i>JWT decode failed</i>")
        except Exception as e:
            logger.warning(f"Failed to decode renewal info: {e}")
            message_parts.append("<i>JWT decode error</i>")
    
    return "\n".join(message_parts)


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

