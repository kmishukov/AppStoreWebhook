"""Validation helpers for App Store Server Notifications V2 signed data."""

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import jwt
from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.signed_data_verifier import (
    SignedDataVerifier,
    VerificationException,
)
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

logger = logging.getLogger(__name__)

DEFAULT_ROOT_CA_PATH = Path(__file__).parent / "certificates" / "AppleRootCA-G3.pem"
ENVIRONMENT_NAMES = {
    "production": Environment.PRODUCTION,
    "sandbox": Environment.SANDBOX,
}


class AppleVerifierConfigurationError(ValueError):
    """Raised when the Apple signed-data verifier is not configured correctly."""


@dataclass(frozen=True)
class VerifierSettings:
    root_certificates: tuple[bytes, ...]
    environments: frozenset[Environment]
    enable_online_checks: bool
    allowed_apps: tuple[tuple[str, int], ...] | None


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise AppleVerifierConfigurationError(
        f"{name} must be one of: true, false, 1, 0, yes, no, on, off"
    )


def _load_root_certificates() -> tuple[bytes, ...]:
    configured_paths = os.getenv("APPLE_ROOT_CA_PATHS")
    paths = (
        [
            Path(value.strip())
            for value in configured_paths.split(os.pathsep)
            if value.strip()
        ]
        if configured_paths
        else [DEFAULT_ROOT_CA_PATH]
    )

    if not paths:
        raise AppleVerifierConfigurationError(
            "APPLE_ROOT_CA_PATHS must contain at least one certificate path"
        )

    certificates: list[bytes] = []
    for path in paths:
        try:
            certificate_bytes = path.read_bytes()
            if b"-----BEGIN CERTIFICATE-----" in certificate_bytes:
                certificate = x509.load_pem_x509_certificate(certificate_bytes)
                certificate_bytes = certificate.public_bytes(Encoding.DER)
            else:
                x509.load_der_x509_certificate(certificate_bytes)
            certificates.append(certificate_bytes)
        except (OSError, ValueError) as exc:
            raise AppleVerifierConfigurationError(
                f"Unable to load Apple Root CA certificate from {path}: {exc}"
            ) from exc

    return tuple(certificates)


def _configured_environments() -> frozenset[Environment]:
    configured = os.getenv("APPLE_ENVIRONMENTS", "Production,Sandbox")
    environments: set[Environment] = set()

    for value in configured.split(","):
        name = value.strip().lower()
        if not name:
            continue
        environment = ENVIRONMENT_NAMES.get(name)
        if environment is None:
            raise AppleVerifierConfigurationError(
                "APPLE_ENVIRONMENTS may contain only Production and Sandbox"
            )
        environments.add(environment)

    if not environments:
        raise AppleVerifierConfigurationError(
            "APPLE_ENVIRONMENTS must contain Production, Sandbox, or both"
        )

    return frozenset(environments)


def _configured_allowed_apps() -> tuple[tuple[str, int], ...] | None:
    raw_value = os.getenv("APPLE_ALLOWED_APPS", "").strip()
    if not raw_value:
        return None

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise AppleVerifierConfigurationError(
            "APPLE_ALLOWED_APPS must be a JSON object mapping bundle IDs to Apple IDs"
        ) from exc

    if not isinstance(parsed, dict) or not parsed:
        raise AppleVerifierConfigurationError(
            "APPLE_ALLOWED_APPS must be a non-empty JSON object"
        )

    allowed_apps: list[tuple[str, int]] = []
    for bundle_id, app_apple_id in parsed.items():
        if not isinstance(bundle_id, str) or not bundle_id.strip():
            raise AppleVerifierConfigurationError(
                "APPLE_ALLOWED_APPS bundle IDs must be non-empty strings"
            )
        try:
            numeric_app_id = int(app_apple_id)
        except (TypeError, ValueError) as exc:
            raise AppleVerifierConfigurationError(
                f"Apple ID for {bundle_id!r} must be numeric"
            ) from exc
        allowed_apps.append((bundle_id.strip(), numeric_app_id))

    return tuple(sorted(allowed_apps))


@lru_cache(maxsize=1)
def get_verifier_settings() -> VerifierSettings:
    """Load and cache configuration shared by all application verifiers."""
    return VerifierSettings(
        root_certificates=_load_root_certificates(),
        environments=_configured_environments(),
        enable_online_checks=_read_bool("APPLE_ENABLE_ONLINE_CHECKS", True),
        allowed_apps=_configured_allowed_apps(),
    )


def validate_verifier_configuration() -> None:
    """Fail fast during application startup if shared settings are invalid."""
    get_verifier_settings()


def _normalize_app_apple_id(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise AppleVerifierConfigurationError(
            f"Invalid appAppleId in Apple payload: {value!r}"
        ) from exc


def _parse_environment(value: Any) -> Environment:
    for environment in (Environment.PRODUCTION, Environment.SANDBOX):
        if value == environment.value:
            return environment
    raise AppleVerifierConfigurationError(
        f"Unsupported or missing Apple environment: {value!r}"
    )


@lru_cache(maxsize=256)
def get_signed_data_verifier(
    environment: Environment,
    bundle_id: str,
    app_apple_id: int | None,
) -> SignedDataVerifier:
    """Build and cache a verifier for one app and environment."""
    settings = get_verifier_settings()
    if environment not in settings.environments:
        raise AppleVerifierConfigurationError(
            f"{environment.value} verification is not enabled"
        )

    expected_app_id = app_apple_id
    if settings.allowed_apps is not None:
        allowed_apps = dict(settings.allowed_apps)
        if bundle_id not in allowed_apps:
            raise AppleVerifierConfigurationError(
                f"Bundle ID {bundle_id!r} is not present in APPLE_ALLOWED_APPS"
            )
        expected_app_id = allowed_apps[bundle_id]
        if environment == Environment.PRODUCTION and app_apple_id != expected_app_id:
            raise AppleVerifierConfigurationError(
                f"appAppleId does not match APPLE_ALLOWED_APPS for {bundle_id!r}"
            )

    if environment == Environment.PRODUCTION and expected_app_id is None:
        raise AppleVerifierConfigurationError(
            "Production Apple payload does not contain appAppleId"
        )

    return SignedDataVerifier(
        list(settings.root_certificates),
        settings.enable_online_checks,
        environment,
        bundle_id,
        expected_app_id if environment == Environment.PRODUCTION else None,
    )


def _decode_unverified(signed_payload: str) -> dict[str, Any]:
    payload = jwt.decode(
        signed_payload,
        options={"verify_signature": False, "verify_exp": False, "verify_iat": False},
    )
    if not isinstance(payload, dict):
        raise jwt.InvalidTokenError("JWT payload is not an object")
    return payload


def _notification_identity(
    payload: dict[str, Any],
) -> tuple[Environment, str, int | None]:
    container: dict[str, Any] | None = None
    for container_name in ("data", "summary", "appData", "externalPurchaseToken"):
        candidate = payload.get(container_name)
        if isinstance(candidate, dict):
            container = candidate
            break

    if container is None:
        raise AppleVerifierConfigurationError(
            "Apple notification does not contain application identity data"
        )

    bundle_id = container.get("bundleId")
    if not isinstance(bundle_id, str) or not bundle_id:
        raise AppleVerifierConfigurationError(
            "Apple notification does not contain bundleId"
        )

    environment_value = container.get("environment")
    if container is payload.get("externalPurchaseToken"):
        external_purchase_id = container.get("externalPurchaseId")
        if isinstance(external_purchase_id, str):
            environment_value = (
                Environment.SANDBOX.value
                if external_purchase_id.startswith("SANDBOX")
                else Environment.PRODUCTION.value
            )

    return (
        _parse_environment(environment_value),
        bundle_id,
        _normalize_app_apple_id(container.get("appAppleId")),
    )


def validate_jwt_token(signed_payload: str) -> dict[str, Any] | None:
    """Verify and decode an App Store Server Notification signedPayload."""
    try:
        payload = _decode_unverified(signed_payload)
        identity = _notification_identity(payload)
        get_signed_data_verifier(*identity).verify_and_decode_notification(
            signed_payload
        )
        logger.info("App Store notification JWS successfully validated")
        return payload
    except VerificationException as exc:
        logger.warning("Apple JWS verification failed: %s", exc.status.name)
    except (AppleVerifierConfigurationError, jwt.InvalidTokenError) as exc:
        logger.warning("Apple JWS validation failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error while validating Apple notification JWS")
    return None


def _get_context_verifier(
    bundle_id: str,
    app_apple_id: int | None,
    environment: str,
) -> SignedDataVerifier:
    if not bundle_id:
        raise AppleVerifierConfigurationError(
            "Parent notification does not contain bundleId"
        )
    return get_signed_data_verifier(
        _parse_environment(environment),
        bundle_id,
        _normalize_app_apple_id(app_apple_id),
    )


def validate_transaction_token(
    signed_payload: str,
    bundle_id: str,
    app_apple_id: int | None,
    environment: str,
) -> dict[str, Any] | None:
    """Verify and decode signedTransactionInfo for its parent app."""
    try:
        payload = _decode_unverified(signed_payload)
        verifier = _get_context_verifier(bundle_id, app_apple_id, environment)
        verifier.verify_and_decode_signed_transaction(signed_payload)
        return payload
    except VerificationException as exc:
        logger.warning("Apple transaction JWS verification failed: %s", exc.status.name)
    except (AppleVerifierConfigurationError, jwt.InvalidTokenError) as exc:
        logger.warning("Apple transaction JWS validation failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error while validating Apple transaction JWS")
    return None


def validate_renewal_info_token(
    signed_payload: str,
    bundle_id: str,
    app_apple_id: int | None,
    environment: str,
) -> dict[str, Any] | None:
    """Verify and decode signedRenewalInfo for its parent app."""
    try:
        payload = _decode_unverified(signed_payload)
        verifier = _get_context_verifier(bundle_id, app_apple_id, environment)
        verifier.verify_and_decode_renewal_info(signed_payload)
        return payload
    except VerificationException as exc:
        logger.warning("Apple renewal JWS verification failed: %s", exc.status.name)
    except (AppleVerifierConfigurationError, jwt.InvalidTokenError) as exc:
        logger.warning("Apple renewal JWS validation failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error while validating Apple renewal JWS")
    return None
