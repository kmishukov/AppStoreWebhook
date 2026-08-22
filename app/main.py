import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.event_handlers import process_notification
from app.jwt_validator import validate_jwt_token, validate_verifier_configuration
from app.message_formatter import validate_message_formatter_configuration
from app.tg.config import validate_telegram_configuration

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# HTTPX includes the full Telegram Bot API URL in its INFO request log. The URL
# contains the bot token, so request logging must stay disabled.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Validate configuration before accepting webhooks."""
    validate_telegram_configuration()
    validate_verifier_configuration()
    validate_message_formatter_configuration()
    yield


def _notification_identity(payload: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive app metadata for structured logging."""
    for field in ("data", "summary", "appData", "externalPurchaseToken"):
        value = payload.get(field)
        if isinstance(value, dict):
            return value
    return {}


app = FastAPI(
    title="App Store Webhook Handler",
    description="Webhook handler for App Store Server Notifications",
    version="1.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"ok": True, "service": "appstore-webhook"}


@app.post("/v1/webhook")
async def appstore_webhook(request: Request):
    """
    Main endpoint for receiving App Store Server Notifications.

    Apple sends POST requests with JSON body containing a 'signedPayload'
    field with a JWT token that must be validated and decoded.
    """
    try:
        # Read raw body so its size can be included in the metadata log.
        body = await request.body()

        # Parse JSON
        try:
            data = await request.json()
        except Exception as e:  # noqa: BLE001 — untrusted request body, any parse failure is a 400
            logger.error("Error parsing JSON: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format"
            )

        # Ensure signedPayload is present
        if "signedPayload" not in data:
            logger.error("Missing 'signedPayload' field in request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'signedPayload' field",
            )

        signed_payload = data["signedPayload"]

        # Validate JWT token
        decoded_payload = validate_jwt_token(signed_payload)

        if decoded_payload is None:
            logger.error("Failed to validate JWT token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT token",
            )

        # Extract notification type
        notification_type = decoded_payload.get("notificationType")

        if not notification_type:
            logger.error("Missing 'notificationType' in payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'notificationType' in payload",
            )

        identity = _notification_identity(decoded_payload)
        environment = identity.get("environment", "Unknown")
        external_purchase_id = identity.get("externalPurchaseId")
        if environment == "Unknown" and isinstance(external_purchase_id, str):
            environment = (
                "Sandbox"
                if external_purchase_id.startswith("SANDBOX")
                else "Production"
            )

        logger.info(
            "Notification received: uuid=%s type=%s subtype=%s bundle_id=%s "
            "environment=%s size_bytes=%d",
            decoded_payload.get("notificationUUID", "N/A"),
            notification_type,
            decoded_payload.get("subtype") or "-",
            identity.get("bundleId", "N/A"),
            environment,
            len(body),
        )

        # Process notification
        try:
            process_notification(notification_type, decoded_payload)
        except Exception:
            logger.exception("Error while processing notification")
            # Return 200 OK even on processing error
            # so that Apple does not keep retrying
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "error",
                    "message": "Error processing notification",
                    "notification_type": notification_type,
                },
            )

        # Return successful response
        # Apple expects 200 OK within 20 seconds
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "notification_type": notification_type,
                "message": "Notification processed successfully",
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions as is
        raise
    except Exception:
        logger.exception("Unexpected error while handling webhook")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
