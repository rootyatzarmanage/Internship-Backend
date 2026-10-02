import logging
import traceback
from datetime import datetime, timezone
from email.message import EmailMessage

import aiosmtplib
from fastapi import Request

from ycpa.services.analytics.user_agent_parser import UserAgentParser
from ycpa.services.analytics.ip_location import IPLocationService
from ycpa.core.config import get_settings

logger = logging.getLogger(__name__)


async def send_error_alert(
    request: Request,
    status_code: int,
    exception: Exception,
):
    if status_code == 404:
        logger.info("404 error excluded from email alert")
        return

    try:
        settings = get_settings()

        smtp_host = getattr(settings, "ERROR_SMTP_HOST", "")
        smtp_port = getattr(settings, "ERROR_SMTP_PORT", 587)
        smtp_user = getattr(settings, "ERROR_SMTP_USER", "")
        smtp_password = getattr(settings, "ERROR_SMTP_PASSWORD", "")
        smtp_from = getattr(settings, "ERROR_SMTP_FROM", "")
        recipient = getattr(settings, "ERROR_ALERT_EMAIL", "")

        if not smtp_host or not recipient or not smtp_from:
            logger.error("Error alert SMTP is not configured")
            return
        current_url = str(request.url)

        previous_url = request.headers.get(
            "referer",
            "Not available",
        )

        request_method = request.method

        connection_ip = (
            request.client.host
            if request.client
            else "Unknown"
        )
        ip_service = IPLocationService()
        public_location = await ip_service.get_my_public_location()
        public_ip = public_location.get(
            "ip_address",
            "Not available",
        )
        country = public_location.get("country_name", "Unknown")
        region = public_location.get("region", "Unknown")
        city = public_location.get("city", "Unknown")
        pincode = public_location.get("pincode", "Unknown")
        timezone_name = public_location.get("time_zone", "Unknown")

        user_agent = request.headers.get("user-agent", "Not available")
        browser = UserAgentParser.get_browser(user_agent)
        operating_system = UserAgentParser.get_operating_system(user_agent)
        device_type = UserAgentParser.get_device_type(user_agent)
        timestamp = datetime.now(timezone.utc).isoformat()
        exception_type = type(exception).__name__
        error_details = str(exception)
        error_traceback = "".join(
            traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__,
            )
        )
        message_body = f"""
APPLICATION ERROR ALERT

ERROR INFORMATION :

Status Code: {status_code}
Exception Type: {exception_type}
Error Details: {error_details}

REQUEST INFORMATION :

Current URL: {current_url}
Previous URL: {previous_url}
Request Method: {request_method}
Timestamp (UTC): {timestamp}
Client IP: {connection_ip}
Public IP: {public_ip}

LOCATION INFORMATION :

Country: {country}
Region: {region}
City: {city}
Pincode: {pincode}
Timezone: {timezone_name}

BROWSER AND DEVICE INFORMATION :

Browser: {browser}
Operating System: {operating_system}
Device Type: {device_type}
User-Agent: {user_agent}


TRACEBACK : 

{error_traceback}
"""
        message = EmailMessage()

        message["Subject"] = (
            f"YCPA Application Error - HTTP {status_code}"
        )

        message["From"] = smtp_from
        message["To"] = recipient

        message.set_content(message_body)

        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
            timeout=15,
        )

        logger.info(
            "Error alert email sent successfully",
            extra={"status_code": status_code},
        )

    except Exception:
        logger.exception("Failed to send error alert email")