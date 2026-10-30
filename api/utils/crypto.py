"""저장용 대칭 암호화. SECRET_KEY(없으면 JWT_SECRET_KEY) 에서 Fernet 키를 유도한다."""
import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

from utils.error import DataError


def _fernet() -> Fernet:
    secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise DataError("SECRET_KEY is required to encrypt credentials")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_text(plain: str | None) -> str | None:
    if plain is None or plain == "":
        return None
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_text(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise DataError("Stored credential cannot be decrypted (SECRET_KEY changed?)") from e
