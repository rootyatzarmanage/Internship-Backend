import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError,jwt
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

class LocalJWTGenerator:
    def __init__(self)-> None:
        self.settings = get_settings()

    def create_access_token(self,user_id:str)->str:
        settings = self.settings
        secret = settings.JWT_SECRET.get_secret_value()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES    
        )
        payload = {
            "sub" : user_id,
            "exp" : expire
        }
        try :
            token = jwt.encode(
                payload,
                secret,
                algorithm=settings.JWT_ALGORITHM
            )
            return token    
        except JWTError as e:
            logger.error(f"Token generation failed: {e}")
            raise ValueError(f"Failed to sign token: {e}") from e
_jwt_generator: LocalJWTGenerator | None = None

def get_jwt_generator() -> LocalJWTGenerator:
    global _jwt_generator
    if _jwt_generator is None:
        _jwt_generator = LocalJWTGenerator()
    return _jwt_generator    