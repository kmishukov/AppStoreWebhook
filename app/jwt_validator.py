"""
Module for validating JWT tokens from App Store Server Notifications.
Apple uses JWT tokens with an X.509 certificate chain (x5c) for signing.
"""
import base64
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import jwt
import requests
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# URL to fetch Apple public keys (if you want to cache/verify the chain)
APPLE_ROOT_CA_URL = "https://www.apple.com/certificateauthority/AppleRootCA-G3.cer"

# In-memory cache for public keys (in production use Redis or another cache)
_key_cache: Dict[str, Any] = {}


def get_apple_public_key(jwt_token: str) -> Optional[Any]:
    """
    Extracts the public key from Apple's JWT token.
    Apple uses x5c (X.509 certificate chain) in the JWT header.
    
    Args:
        jwt_token: JWT token as string
        
    Returns:
        Public key for signature verification or None
    """
    try:
        # Decode JWT header without verifying signature
        header = jwt.get_unverified_header(jwt_token)
        
        # Check that x5c (certificate chain) is present
        if 'x5c' not in header or not header['x5c']:
            logger.error("JWT header does not contain x5c (certificate chain)")
            return None
        
        # Take the first certificate from the chain (leaf certificate)
        cert_der = header['x5c'][0]
        
        # Decode certificate from base64
        cert_bytes = base64.b64decode(cert_der)
        
        # Parse certificate
        cert = x509.load_der_x509_certificate(cert_bytes, default_backend())
        
        # Extract public key
        public_key = cert.public_key()
        
        return public_key
        
    except Exception as e:
        logger.error(f"Error extracting public key: {e}")
        return None


def validate_jwt_token(signed_payload: str) -> Optional[Dict[str, Any]]:
    """
    Validates Apple's JWT token and returns decoded payload.
    
    Args:
        signed_payload: JWT token as string (signedPayload from notification)
        
    Returns:
        Decoded payload or None on error
    """
    try:
        # Get public key from JWT token
        public_key = get_apple_public_key(signed_payload)
        
        if public_key is None:
            logger.error("Failed to get public key from JWT token")
            return None
        
        # Decode and verify JWT token
        # Apple uses ES256 algorithm
        decoded = jwt.decode(
            signed_payload,
            public_key,
            algorithms=["ES256"],
            options={
                "verify_signature": True,
                "verify_exp": True,  # Verify expiration
                "verify_iat": True,  # Verify issued at
            }
        )
        
        logger.info("JWT token successfully validated")
        return decoded
        
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error validating JWT token: {e}")
        return None

