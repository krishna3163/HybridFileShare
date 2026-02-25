"""
SecurityManager: Handles E2EE, ephemeral keys, and secure handshakes.
"""

import os
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

class SecurityManager:
    """
    Manages end-to-end encryption using AES-256-GCM.
    
    Features:
    - ECDH for ephemeral session key exchange
    - Ephemeral keys per transfer
    - AES-256-GCM for authenticated encryption
    - Secure handshake support
    """

    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.shared_key = None
        self.aes_gcm = None

    def generate_key_pair(self) -> bytes:
        """Generate ECDH key pair and return serialized public key."""
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        return self.public_key.public_bytes(
            encoding=hashes.serialization.Encoding.X962,
            format=hashes.serialization.PublicFormat.Uncompressed
        )

    def derive_shared_key(self, remote_public_key_bytes: bytes):
        """Derive shared session key from remote public key."""
        remote_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), remote_public_key_bytes
        )
        shared_secret = self.private_key.exchange(ec.ECDH(), remote_public_key)
        
        # Derive key using HKDF
        self.shared_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"hybridlink-session",
        ).derive(shared_secret)
        
        self.aes_gcm = AESGCM(self.shared_key)
        logger.info("Shared session key derived successfully")

    def encrypt(self, data: bytes) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-GCM, returns (nonce, ciphertext)."""
        if not self.aes_gcm:
            raise RuntimeError("Secret key not established")
        
        nonce = os.urandom(12)
        ciphertext = self.aes_gcm.encrypt(nonce, data, None)
        return nonce, ciphertext

    def decrypt(self, nonce: bytes, ciphertext: bytes) -> bytes:
        """Decrypt data using AES-GCM."""
        if not self.aes_gcm:
            raise RuntimeError("Secret key not established")
        
        return self.aes_gcm.decrypt(nonce, ciphertext, None)

    def reset(self):
        """Clear session keys."""
        self.private_key = None
        self.public_key = None
        self.shared_key = None
        self.aes_gcm = None
