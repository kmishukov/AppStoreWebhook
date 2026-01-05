"""
Message formatter for App Store Server Notifications.
Formats notification data into HTML messages for Telegram.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo
from app.jwt_validator import validate_jwt_token

logger = logging.getLogger(__name__)

# Notification types from Apple (human‑readable descriptions)
# Based on: https://developer.apple.com/documentation/appstoreservernotifications/notificationtype
NOTIFICATION_TYPES = {
    "CONSUMPTION_REQUEST": "Customer initiated refund request, App Store requesting consumption data",
    "DID_CHANGE_RENEWAL_PREF": "Customer changed subscription plan (upgrade/downgrade)",
    "DID_CHANGE_RENEWAL_STATUS": "Customer changed subscription renewal status",
    "DID_FAIL_TO_RENEW": "Subscription failed to renew due to billing issue",
    "DID_RENEW": "Subscription successfully renewed",
    "EXPIRED": "Subscription expired",
    "EXTERNAL_PURCHASE_TOKEN": "External Purchase API notification",
    "GRACE_PERIOD_EXPIRED": "Billing grace period ended without renewal",
    "METADATA_UPDATE": "Subscription metadata changed (Advanced Commerce API)",
    "MIGRATION": "Subscription migrated to Advanced Commerce API",
    "OFFER_REDEEMED": "Customer redeemed subscription offer",
    "ONE_TIME_CHARGE": "Customer purchased consumable/non-consumable/non-renewing subscription",
    "PRICE_CHANGE": "Subscription price changed (Advanced Commerce API)",
    "PRICE_INCREASE": "System informed customer of subscription price increase",
    "REFUND": "App Store successfully refunded a transaction",
    "REFUND_DECLINED": "App Store declined a refund request",
    "REFUND_REVERSED": "App Store reversed a previously granted refund",
    "RENEWAL_EXTENDED": "App Store extended subscription renewal date",
    "RENEWAL_EXTENSION": "Subscription renewal date extension attempt",
    "RESCIND_CONSENT": "Parent/guardian withdrew consent for child's app usage",
    "REVOKE": "In-App Purchase no longer available through Family Sharing",
    "SUBSCRIBED": "Customer subscribed to auto-renewable subscription",
    "TEST": "Test notification from App Store",
}


def format_timestamp(timestamp: Optional[int]) -> str:
    """Format Unix timestamp to readable date in Moscow timezone (UTC+3)."""
    if not timestamp:
        return "N/A"
    try:
        # Convert to seconds (Apple timestamps are in milliseconds)
        dt_utc = datetime.fromtimestamp(timestamp / 1000, tz=ZoneInfo("UTC"))
        # Convert to Moscow timezone
        dt_moscow = dt_utc.astimezone(ZoneInfo("Europe/Moscow"))
        return dt_moscow.strftime("%Y-%m-%d %H:%M:%S MSK")
    except (ValueError, OSError) as e:
        logger.warning(f"Failed to format timestamp {timestamp}: {e}")
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
                    storefront = decoded_tx.get("storefront")  # Country/region code (e.g., "RUS", "USA")
                    storefront_id = decoded_tx.get("storefrontId")  # Storefront ID
                    
                    message_parts.append(f"<code>Transaction ID:</code> {tx_id}")
                    message_parts.append(f"<code>Product ID:</code> {product_id}")
                    if storefront:
                        message_parts.append(f"<code>Storefront:</code> {storefront}")
                    if storefront_id:
                        message_parts.append(f"<code>Storefront ID:</code> {storefront_id}")
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

