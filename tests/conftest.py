import base64
import datetime

import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def _generate_signing_material():
    """Self-signed EC key pair + certificate, standing in for Apple's x5c chain."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Signer")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    return private_key, cert_der


@pytest.fixture
def signed_payload_factory():
    """Returns a function that signs a payload dict like Apple would (ES256 + x5c header)."""

    def _make(payload: dict, headers: dict | None = None) -> str:
        private_key, cert_der = _generate_signing_material()
        cert_b64 = base64.b64encode(cert_der).decode("ascii")
        jwt_headers = {"x5c": [cert_b64]}
        if headers:
            jwt_headers.update(headers)
        return jwt.encode(payload, private_key, algorithm="ES256", headers=jwt_headers)

    return _make
