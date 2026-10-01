import httpx

from app.core.config import settings


class CrispService:

    BASE_URL = "https://api.crisp.chat/v1"

    async def send_message(
        self,
        session_id: str,
        message: str
    ):

        url = (
            f"{self.BASE_URL}/website/"
            f"{settings.CRISP_WEBSITE_ID}/conversation/"
            f"{session_id}/message"
        )

        headers = {
            "X-Crisp-Tier": "website",
            "Content-Type": "application/json"
        }

        payload = {
            "type": "text",
            "from": "operator",
            "origin": "chat",
            "content": message
        }

        async with httpx.AsyncClient(timeout=15.0) as client:

            response = await client.post(
                url,
                auth=(
                    settings.CRISP_IDENTIFIER,
                    settings.CRISP_KEY
                ),
                headers=headers,
                json=payload
            )

            response.raise_for_status()

            return response.json()