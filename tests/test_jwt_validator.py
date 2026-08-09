import jwt as pyjwt

from app.jwt_validator import get_apple_public_key, validate_jwt_token


def test_validate_jwt_token_success(signed_payload_factory):
    payload = {"notificationType": "TEST", "notificationUUID": "abc-123"}
    token = signed_payload_factory(payload)

    decoded = validate_jwt_token(token)

    assert decoded is not None
    assert decoded["notificationType"] == "TEST"
    assert decoded["notificationUUID"] == "abc-123"


def test_validate_jwt_token_tampered_signature(signed_payload_factory):
    token = signed_payload_factory({"notificationType": "TEST"})
    header, payload, signature = token.rsplit(".", 2)
    tampered = f"{header}.{payload}.{signature[:-4]}AAAA"

    assert validate_jwt_token(tampered) is None


def test_validate_jwt_token_expired(signed_payload_factory):
    payload = {
        "notificationType": "TEST",
        "iat": 1000,
        "exp": 2000,
    }
    token = signed_payload_factory(payload)

    assert validate_jwt_token(token) is None


def test_get_apple_public_key_missing_x5c():
    token = pyjwt.encode({"foo": "bar"}, "secret", algorithm="HS256")

    assert get_apple_public_key(token) is None


def test_validate_jwt_token_malformed_string():
    assert validate_jwt_token("not-a-jwt") is None
