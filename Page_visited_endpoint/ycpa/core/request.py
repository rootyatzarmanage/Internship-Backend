import logging
from fastapi import Request
from ycpa.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_client_ip(request: Request) -> str | None:
    """Extracts the client host IP address from an incoming FastAPI Request instance."""
    try:
        if request.client is None:
            logger.warning("Could not resolve client IP: request.client is None")
            return None

        client_ip = request.client.host
        logger.info(f"Successfully resolved client IP: {client_ip}")
        return client_ip

    except Exception as e:
        logger.error(
            "Failed to extract client IP address from request context",
            extra={"error": str(e)},
            exc_info=True,
        )
        return None