import jwt as pyjwt
import pytest
from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.signed_data_verifier import (
    VerificationException,
    VerificationStatus,
)

from app import jwt_validator


class SuccessfulVerifier:
    def __init__(self):
        self.notification_token = None
        self.transaction_token = None
        self.renewal_token = None

    def verify_and_decode_notification(self, token):
        self.notification_token = token

    def verify_and_decode_signed_transaction(self, token):
        self.transaction_token = token

    def verify_and_decode_renewal_info(self, token):
        self.renewal_token = token


class FailingVerifier:
    def verify_and_decode_notification(self, _token):
        raise VerificationException(VerificationStatus.INVALID_APP_IDENTIFIER)


def _sandbox_payload(bundle_id="com.example.app"):
    return {
        "notificationType": "TEST",
        "notificationUUID": "abc-123",
        "data": {
            "bundleId": bundle_id,
            "environment": "Sandbox",
        },
    }


def _production_payload(bundle_id, app_apple_id):
    return {
        "notificationType": "TEST",
        "notificationUUID": "abc-123",
        "data": {
            "bundleId": bundle_id,
            "appAppleId": app_apple_id,
            "environment": "Production",
        },
    }


def _clear_verifier_caches():
    jwt_validator.get_verifier_settings.cache_clear()
    jwt_validator.get_signed_data_verifier.cache_clear()


def test_validate_jwt_token_success(monkeypatch, signed_payload_factory):
    verifier = SuccessfulVerifier()
    monkeypatch.setattr(
        jwt_validator,
        "get_signed_data_verifier",
        lambda *_identity: verifier,
    )
    token = signed_payload_factory(_sandbox_payload())

    decoded = jwt_validator.validate_jwt_token(token)

    assert decoded is not None
    assert decoded["notificationType"] == "TEST"
    assert decoded["notificationUUID"] == "abc-123"
    assert verifier.notification_token == token


def test_notifications_for_multiple_apps_get_separate_verifiers(
    monkeypatch, signed_payload_factory
):
    requested_identities = []

    def verifier_for_app(environment, bundle_id, app_apple_id):
        requested_identities.append((environment, bundle_id, app_apple_id))
        return SuccessfulVerifier()

    monkeypatch.setattr(
        jwt_validator,
        "get_signed_data_verifier",
        verifier_for_app,
    )
    first_token = signed_payload_factory(_production_payload("com.example.one", 111))
    second_token = signed_payload_factory(_production_payload("com.example.two", 222))

    assert jwt_validator.validate_jwt_token(first_token) is not None
    assert jwt_validator.validate_jwt_token(second_token) is not None
    assert requested_identities == [
        (Environment.PRODUCTION, "com.example.one", 111),
        (Environment.PRODUCTION, "com.example.two", 222),
    ]


def test_validate_jwt_token_rejects_self_signed_certificate(
    monkeypatch, signed_payload_factory
):
    monkeypatch.setenv("APPLE_ENVIRONMENTS", "Sandbox")
    monkeypatch.setenv("APPLE_ENABLE_ONLINE_CHECKS", "false")
    monkeypatch.delenv("APPLE_ALLOWED_APPS", raising=False)
    _clear_verifier_caches()
    token = signed_payload_factory(_sandbox_payload())

    try:
        assert jwt_validator.validate_jwt_token(token) is None
    finally:
        _clear_verifier_caches()


def test_validate_jwt_token_rejects_verifier_failure(
    monkeypatch, signed_payload_factory
):
    monkeypatch.setattr(
        jwt_validator,
        "get_signed_data_verifier",
        lambda *_identity: FailingVerifier(),
    )
    token = signed_payload_factory(_sandbox_payload())

    assert jwt_validator.validate_jwt_token(token) is None


def test_optional_allowlist_rejects_unknown_app(monkeypatch):
    monkeypatch.setenv("APPLE_ENVIRONMENTS", "Production")
    monkeypatch.setenv("APPLE_ENABLE_ONLINE_CHECKS", "false")
    monkeypatch.setenv("APPLE_ALLOWED_APPS", '{"com.example.allowed":111}')
    _clear_verifier_caches()

    try:
        with pytest.raises(jwt_validator.AppleVerifierConfigurationError):
            jwt_validator.get_signed_data_verifier(
                Environment.PRODUCTION, "com.example.other", 222
            )
    finally:
        _clear_verifier_caches()


def test_validate_transaction_token_uses_parent_app_verifier(
    monkeypatch, signed_payload_factory
):
    verifier = SuccessfulVerifier()
    identities = []

    def verifier_for_app(*identity):
        identities.append(identity)
        return verifier

    monkeypatch.setattr(
        jwt_validator,
        "get_signed_data_verifier",
        verifier_for_app,
    )
    token = signed_payload_factory({"transactionId": "123", "environment": "Sandbox"})

    decoded = jwt_validator.validate_transaction_token(
        token, "com.example.app", None, "Sandbox"
    )

    assert decoded == {"transactionId": "123", "environment": "Sandbox"}
    assert identities == [(Environment.SANDBOX, "com.example.app", None)]
    assert verifier.transaction_token == token


def test_validate_renewal_token_uses_parent_app_verifier(
    monkeypatch, signed_payload_factory
):
    verifier = SuccessfulVerifier()
    monkeypatch.setattr(
        jwt_validator,
        "get_signed_data_verifier",
        lambda *_identity: verifier,
    )
    token = signed_payload_factory({"autoRenewStatus": 1, "environment": "Sandbox"})

    decoded = jwt_validator.validate_renewal_info_token(
        token, "com.example.app", None, "Sandbox"
    )

    assert decoded == {"autoRenewStatus": 1, "environment": "Sandbox"}
    assert verifier.renewal_token == token


def test_validate_jwt_token_missing_x5c(monkeypatch):
    monkeypatch.setenv("APPLE_ENVIRONMENTS", "Sandbox")
    monkeypatch.setenv("APPLE_ENABLE_ONLINE_CHECKS", "false")
    monkeypatch.delenv("APPLE_ALLOWED_APPS", raising=False)
    _clear_verifier_caches()
    token = pyjwt.encode(_sandbox_payload(), "secret", algorithm="HS256")

    try:
        assert jwt_validator.validate_jwt_token(token) is None
    finally:
        _clear_verifier_caches()


def test_validate_jwt_token_malformed_string():
    assert jwt_validator.validate_jwt_token("not-a-jwt") is None
