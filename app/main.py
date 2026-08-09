import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.event_handlers import process_notification
from app.jwt_validator import validate_jwt_token, validate_verifier_configuration
from app.message_formatter import NOTIFICATION_TYPES

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Validate Apple verification settings before accepting webhooks."""
    validate_verifier_configuration()
    yield


app = FastAPI(
    title="App Store Webhook Handler",
    description="Webhook handler for App Store Server Notifications",
    version="1.0.0",
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
        # Read raw body for logging
        body = await request.body()
        logger.info(f"Received notification from App Store. Size: {len(body)} bytes")

        # Parse JSON
        try:
            data = await request.json()
        except Exception as e:  # noqa: BLE001 — untrusted request body, any parse failure is a 400
            logger.error(f"Error parsing JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format"
            )

        # Log incoming request (without sensitive data)
        logger.info(
            f"Incoming notification: {json.dumps({k: v for k, v in data.items() if k != 'signedPayload'}, indent=2)}"
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

        # Log decoded payload
        logger.info(
            f"Decoded payload: {json.dumps(decoded_payload, indent=2, default=str)}"
        )

        # Extract notification type
        notification_type = decoded_payload.get("notificationType")

        if not notification_type:
            logger.error("Missing 'notificationType' in payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'notificationType' in payload",
            )

        # Log notification type
        notification_description = NOTIFICATION_TYPES.get(
            notification_type, f"Unknown type: {notification_type}"
        )
        logger.info(
            f"Notification type: {notification_type} - {notification_description}"
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
