import os
import tempfile

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class SigningKeyMixin:
    """Generates a throw-away Ed25519 key and points the signer at it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.private_key = ed25519.Ed25519PrivateKey.generate()
        pem = cls.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
        fd, cls.key_path = tempfile.mkstemp(suffix='.pem')
        with os.fdopen(fd, 'wb') as fh:
            fh.write(pem)
        cls.env['ir.config_parameter'].sudo().set_param(
            'techrise_license.signing_key_path', cls.key_path)

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls.key_path)
        finally:
            super().tearDownClass()

    def assertSigned(self, message: bytes, sig_b64: str):
        import base64
        self.private_key.public_key().verify(base64.b64decode(sig_b64), message)
