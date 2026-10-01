import httpx
from ycpa.core.config.settings import get_settings

settings = get_settings()

class IPLocationService:

    BASE_URL = settings.HACKMYIP_LOOKUP_URL
    MY_IP_URL = settings.HACKMYIP_MY_IP_URL
    async def get_location(
        self,
        ip_address: str,
    ) -> dict:

        try:
            async with httpx.AsyncClient(
                timeout=3.0
            ) as client:

                response = await client.get(
                    self.BASE_URL,
                    params={
                        "ip": ip_address,
                    },
                )

            if response.status_code != 200:
                return {}

            data = response.json()

            if not data.get("success"):
                return {}

            location = data.get(
                "data",
                {},
            ).get(
                "location",
                {},
            )

            return {
                "country_name": location.get("country_name"),
                "region": location.get("region"),
                "city": location.get("city"),
                "pincode": location.get("postal_code"),
                "time_zone": location.get("timezone"),
            }

        except (
            httpx.RequestError,
            ValueError,
        ):
            return {}

    async def get_my_public_location(self) -> dict:

        try:
            async with httpx.AsyncClient(
                timeout=3.0
            ) as client:

                response = await client.get(
                    self.MY_IP_URL
                )

            if response.status_code != 200:
                return {}

            data = response.json()

            if not data.get("success"):
                return {}

            result = data.get("data", {})
            location = result.get("location", {})

            return {
                "ip_address": result.get("ip"),
                "country_name": location.get("country_name"),
                "region": location.get("region"),
                "city": location.get("city"),
                "pincode": location.get("postal_code"),
                "time_zone": location.get("timezone"),
            }

        except (
            httpx.RequestError,
            ValueError,
        ):
            return {}