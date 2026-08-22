"""
Data models for App Store Server Notifications.
"""

from typing import Any

from pydantic import BaseModel, Field


class TransactionInfo(BaseModel):
    """Transaction information."""

    transaction_id: str = Field(..., alias="transactionId")
    original_transaction_id: str = Field(..., alias="originalTransactionId")
    product_id: str = Field(..., alias="productId")
    in_app_ownership_type: str | None = Field(None, alias="inAppOwnershipType")
    purchase_date: int = Field(..., alias="purchaseDate")
    expires_date: int | None = Field(None, alias="expiresDate")
    quantity: int = 1
    type: str = "Auto-Renewable Subscription"
    environment: str = "Production"  # or "Sandbox"
    signed_date: int = Field(..., alias="signedDate")


class RenewalInfo(BaseModel):
    """Subscription renewal information."""

    expiration_intent: str | None = Field(None, alias="expirationIntent")
    auto_renew_status: int = Field(..., alias="autoRenewStatus")
    auto_renew_product_id: str | None = Field(None, alias="autoRenewProductId")
    is_in_billing_retry_period: bool | None = Field(
        None, alias="isInBillingRetryPeriod"
    )
    product_id: str | None = Field(None, alias="productId")
    price_consent_status: int | None = Field(None, alias="priceConsentStatus")


class NotificationPayload(BaseModel):
    """Main notification payload from Apple."""

    notification_type: str = Field(..., alias="notificationType")
    subtype: str | None = None
    notification_uuid: str = Field(..., alias="notificationUUID")
    data: dict[str, Any] = Field(..., alias="data")
    version: str = "2.0"
    signed_date: int = Field(..., alias="signedDate")

    # Additional derived fields from `data`
    @property
    def transaction_info(self) -> TransactionInfo | None:
        """Extracts transaction info from `data`."""
        bundle_id = self.data.get("bundleId")
        if bundle_id and "signedTransactionInfo" in self.data:
            # In reality you should decode `signedTransactionInfo` (JWT)
            # For now we return None; in production implement full decoding
            return None
        return None

    @property
    def renewal_info(self) -> RenewalInfo | None:
        """Extracts renewal info from `data`."""
        bundle_id = self.data.get("bundleId")
        if bundle_id and "signedRenewalInfo" in self.data:
            # In reality you should decode `signedRenewalInfo` (JWT)
            return None
        return None


class AppStoreNotification(BaseModel):
    """Incoming notification model from App Store."""

    signed_payload: str = Field(..., alias="signedPayload")

    # Decoded payload (after JWT validation)
    payload: NotificationPayload | None = None

    class Config:
        allow_population_by_field_name = True
