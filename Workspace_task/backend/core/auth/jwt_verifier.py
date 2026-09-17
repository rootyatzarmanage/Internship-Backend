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

    def verify_access_token(
        self,
        token: str
    ) -> str:
        settings = self.settings
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token claims")
            return user_id

        except JWTError as e:
            logger.error(
                f"Access token verification failed: {e}"
            )
            raise ValueError(
                "Invalid or expired access token"
            ) from e
            
    def create_reset_token(
        self,
        user_id : str
    ) -> str:
        settings = self.settings
        expire = datetime.now(timezone.utc) + timedelta(
        minutes = 15
        )
        payload = {
            "sub" : user_id,
            "type" : "password_reset",
            "exp" : expire
        }

        try:
            token = jwt.encode(
                payload,
                settings.JWT_SECRET.get_secret_value(),
                algorithm = settings.JWT_ALGORITHM
            )
            return token
        
        except JWTError as e:
            logger.error(
                f"Reset token generation failed: {e}"
            )
            raise ValueError(
                f"Failed to generate reset token: {e}"
            ) from e
    def verify_reset_token(
        self,
        token: str
    ) -> str:
        settings = self.settings
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "password_reset":
                raise ValueError("Invalid reset token")
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid reset token")
            return user_id
        except JWTError as e:
            logger.error(
                f"Reset token verification failed: {e}"
            )
            raise ValueError(
                "Invalid or expired reset token"
            ) from e
        
_jwt_generator: LocalJWTGenerator | None = None

def get_jwt_generator() -> LocalJWTGenerator:
    global _jwt_generator
    if _jwt_generator is None:
        _jwt_generator = LocalJWTGenerator()
    return _jwt_generator    