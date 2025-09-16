"""
ATECC608 Secure Element interface for ECDSA P-256 signing
"""
import hashlib
import logging
from typing import Optional, Tuple
import binascii

try:
    from cryptoauthlib import *
    CRYPTOAUTHLIB_AVAILABLE = True
except ImportError:
    CRYPTOAUTHLIB_AVAILABLE = False

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ATECC608SecureElement:
    """Production-ready ATECC608 interface for secure signing"""

    def __init__(self, i2c_address: int = 0x60, key_slot: int = 0):
        """
        Initialize ATECC608 secure element

        Args:
            i2c_address: I2C address of ATECC608
            key_slot: Key slot to use for signing (0-15)
        """
        self.i2c_address = i2c_address
        self.key_slot = key_slot
        self._device = None
        self._is_hardware = False
        self._fallback_private_key = None

    def initialize(self) -> bool:
        """Initialize connection to ATECC608"""
        if CRYPTOAUTHLIB_AVAILABLE:
            try:
                # Try hardware ATECC608 first
                cfg = cfg_ateccx08a_i2c_default()
                cfg.cfg.atcai2c.slave_address = self.i2c_address

                if atcab_init(cfg) == ATCA_SUCCESS:
                    info = bytearray(4)
                    if atcab_info(info) == ATCA_SUCCESS:
                        self._device = cfg
                        self._is_hardware = True
                        logger.info(f"ATECC608 hardware initialized at 0x{self.i2c_address:02x}")
                        return True
            except Exception as e:
                logger.warning(f"Hardware ATECC608 initialization failed: {e}")

        # Fallback to software crypto
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                self._fallback_private_key = ec.generate_private_key(ec.SECP256R1())
                self._is_hardware = False
                logger.warning("Using software crypto fallback for ATECC608")
                return True
            except Exception as e:
                logger.error(f"Software crypto fallback failed: {e}")

        logger.error("No crypto backend available")
        return False

    def get_public_key(self) -> Optional[bytes]:
        """Get the public key for verification"""
        if self._is_hardware and self._device:
            try:
                public_key = bytearray(64)
                if atcab_get_pubkey(self.key_slot, public_key) == ATCA_SUCCESS:
                    return bytes(public_key)
            except Exception as e:
                logger.error(f"Failed to get hardware public key: {e}")

        elif self._fallback_private_key:
            try:
                public_key = self._fallback_private_key.public_key()
                return public_key.public_bytes(
                    encoding=serialization.Encoding.X962,
                    format=serialization.PublicFormat.UncompressedPoint
                )
            except Exception as e:
                logger.error(f"Failed to get software public key: {e}")

        return None

    def sign_data(self, data: bytes) -> Optional[Tuple[bytes, bytes]]:
        """
        Sign data with P-256 ECDSA

        Args:
            data: Data to sign

        Returns:
            Tuple of (signature, hash) or None if failed
        """
        # Hash the data with SHA-256
        digest = hashlib.sha256(data).digest()

        if self._is_hardware and self._device:
            try:
                signature = bytearray(64)
                if atcab_sign(self.key_slot, digest, signature) == ATCA_SUCCESS:
                    return bytes(signature), digest
            except Exception as e:
                logger.error(f"Hardware signing failed: {e}")

        elif self._fallback_private_key:
            try:
                signature = self._fallback_private_key.sign(
                    digest,
                    ec.ECDSA(hashes.SHA256())
                )
                # Convert DER signature to raw R,S format
                r, s = self._der_to_raw(signature)
                raw_sig = r + s
                return raw_sig, digest
            except Exception as e:
                logger.error(f"Software signing failed: {e}")

        return None

    def _der_to_raw(self, der_signature: bytes) -> Tuple[bytes, bytes]:
        """Convert DER signature to raw R,S components"""
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
        r, s = decode_dss_signature(der_signature)

        # Convert to 32-byte big-endian format
        r_bytes = r.to_bytes(32, byteorder='big')
        s_bytes = s.to_bytes(32, byteorder='big')

        return r_bytes, s_bytes

    def verify_signature(self, data: bytes, signature: bytes, public_key: bytes = None) -> bool:
        """
        Verify a signature (for testing)

        Args:
            data: Original data
            signature: 64-byte signature
            public_key: Public key bytes (optional, uses device key if None)

        Returns:
            True if signature is valid
        """
        if public_key is None:
            public_key = self.get_public_key()

        if not public_key:
            return False

        digest = hashlib.sha256(data).digest()

        if self._is_hardware and self._device:
            try:
                is_verified = ctypes.c_bool()
                result = atcab_verify_extern(digest, signature, public_key, is_verified)
                return result == ATCA_SUCCESS and is_verified.value
            except Exception as e:
                logger.error(f"Hardware verification failed: {e}")

        elif CRYPTOGRAPHY_AVAILABLE:
            try:
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

                # Convert raw signature back to DER format
                r = int.from_bytes(signature[:32], byteorder='big')
                s = int.from_bytes(signature[32:], byteorder='big')
                der_sig = encode_dss_signature(r, s)

                # Reconstruct public key
                public_key_obj = ec.EllipticCurvePublicKey.from_encoded_point(
                    ec.SECP256R1(), public_key
                )

                public_key_obj.verify(der_sig, digest, ec.ECDSA(hashes.SHA256()))
                return True
            except Exception as e:
                logger.error(f"Software verification failed: {e}")

        return False

    def get_device_info(self) -> dict:
        """Get device information"""
        info = {
            'is_hardware': self._is_hardware,
            'i2c_address': f"0x{self.i2c_address:02x}",
            'key_slot': self.key_slot
        }

        if self._is_hardware and self._device:
            try:
                device_info = bytearray(4)
                if atcab_info(device_info) == ATCA_SUCCESS:
                    info['device_revision'] = binascii.hexlify(device_info).decode()
            except Exception:
                pass

        return info

    def is_connected(self) -> bool:
        """Check if device is responding"""
        if self._is_hardware and self._device:
            try:
                info = bytearray(4)
                return atcab_info(info) == ATCA_SUCCESS
            except Exception:
                return False

        return self._fallback_private_key is not None

    def cleanup(self):
        """Clean up resources"""
        if self._is_hardware and self._device:
            try:
                atcab_release()
            except Exception:
                pass
        logger.info("ATECC608 cleaned up")