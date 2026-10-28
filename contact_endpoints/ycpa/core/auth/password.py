import logging
import bcrypt
# from passlib.context import CryptContext

logger = logging.getLogger(__name__)

class LocalPasswordHasher:
    def __init__(self)->None:
        pass

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_bytes.decode("utf-8")
    
    def verify_password(
        self,
        password :str,
        password_hash :str
    )-> bool :
        try :
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification failed due to internal error {e}")
            return False

_password_hasher: LocalPasswordHasher | None = None

def get_password_hasher() -> LocalPasswordHasher:
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = LocalPasswordHasher()
    return _password_hasher