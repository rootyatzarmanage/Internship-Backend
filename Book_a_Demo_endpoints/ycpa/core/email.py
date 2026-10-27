import logging
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from ycpa.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_tls_context() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    try:
        ctx.load_default_certs()
    except Exception:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


async def send_email(to: str, subject: str, html_body: str, cc: list[str] | None = None) -> bool:

    try:
        cc = [c for c in (cc or []) if c and c.lower() != to.lower()]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = settings.SMTP_FROM
        msg["To"]      = to
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            msg,
            recipients=[to, *cc],
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
            tls_context=_build_tls_context(),
        )
        logger.info(f"Email sent to {to}", extra={"subject": subject, "cc": cc})
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to}", extra={"error": str(e)}, exc_info=True)
        return False


def build_share_email(
        sharer_name: str,
        recipient_name: str,
        item_type: str,
        item_name: str,
        can_edit: bool,
        cde_link: str,
        is_new_user: bool,
        message: str | None = None,
) -> str:
    permission_label = "edit" if can_edit else "view"
    item_label = item_type.capitalize()  # "File" | "Folder"
    cta_text = "Create your free account" if is_new_user else f"Open {item_label} in CDE"

    new_user_note = ""
    if is_new_user:
        new_user_note = f"""
        <tr>
          <td style="padding:0 32px 20px;">
            <p style="margin:0;font-size:13px;color:#605e5c;line-height:1.6;">
              You'll need a free YCPA account to access it.
              Sign up with <strong>{recipient_name}</strong> and the {item_label}
              will appear automatically in your CDE dashboard.
            </p>
          </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{sharer_name} shared a {item_type} with you</title>
</head>
<body style="margin:0;padding:0;background:#f3f2f1;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f2f1;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #edebe9;border-radius:2px;">

          <!-- Header -->
          <tr>
            <td style="background:#0078d4;padding:20px 32px;">
              <p style="margin:0;font-size:18px;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">
                YCPA
              </p>
              <p style="margin:4px 0 0;font-size:11px;color:rgba(255,255,255,0.75);text-transform:uppercase;letter-spacing:0.06em;">
                Common Data Environment
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 32px 20px;">
              <p style="margin:0 0 16px;font-size:15px;font-weight:600;color:#323130;">
                {sharer_name} shared a {item_type} with you
              </p>
              <p style="margin:0;font-size:14px;color:#605e5c;line-height:1.6;">
                Hi {recipient_name},
              </p>
              <p style="margin:12px 0 0;font-size:14px;color:#605e5c;line-height:1.6;">
                <strong style="color:#323130;">{sharer_name}</strong> has shared the
                {item_type} <strong style="color:#323130;">{item_name}</strong> with you
                on YCPA. You have <strong>{permission_label}</strong> access.
              </p>
            </td>
          </tr>

          <!-- What they can do -->
          <tr>
            <td style="padding:0 32px 20px;">
              <table cellpadding="0" cellspacing="0" style="background:#faf9f8;border:1px solid #edebe9;width:100%;">
                <tr>
                  <td style="padding:14px 16px;">
                    <p style="margin:0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#a19f9d;">
                      {item_label} Details
                    </p>
                    <p style="margin:8px 0 0;font-size:13px;color:#323130;">
                      <strong>Name:</strong> {item_name}
                    </p>
                    <p style="margin:4px 0 0;font-size:13px;color:#323130;">
                      <strong>Access:</strong> {permission_label.capitalize()} only
                    </p>
                    <p style="margin:4px 0 0;font-size:13px;color:#323130;">
                      <strong>Shared by:</strong> {sharer_name}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {new_user_note}

          <!-- CTA -->
          <tr>
            <td style="padding:0 32px 32px;" align="center">
              <a href="{cde_link}"
                 style="display:inline-block;padding:10px 28px;background:#0078d4;color:#ffffff;
                        font-size:13px;font-weight:600;text-decoration:none;border-radius:2px;">
                {cta_text}
              </a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:16px 32px;border-top:1px solid #edebe9;">
              <p style="margin:0;font-size:11px;color:#a19f9d;line-height:1.6;">
                You received this email because {sharer_name} shared content with your
                email address on YCPA. If you didn't expect this, you can safely ignore it.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

def build_invite_email(
    inviter_name: str,
    project_name: str,
    workspace_name: str,
    role_name: str,
    invite_link: str,
    expires_in_hours: int = 48,
    message: str | None = None,
) -> str:
    """Returns HTML email body for project invitation."""

    import html as html_lib
    safe_message = html_lib.escape(message) if message else None

    personal_note_html = ""
    if safe_message:
        personal_note_html = f"""
    <div style="background: #fef3c7; border-radius: 6px; padding: 14px 18px; margin: 0 0 20px;">
      <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.6;">
        <strong>Personal note from {inviter_name}:</strong>


        {safe_message}
      </p>
    </div>
    """

    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 24px;">
  <div style="max-width: 520px; margin: auto; background: white; border-radius: 8px; padding: 32px;">

    <h2 style="color: #1a1a1a;">You've been invited to a project</h2>

    <p style="color: #444; font-size: 15px;">
      <strong>{inviter_name}</strong> has invited you to join
      <strong>{project_name}</strong> in the <strong>{workspace_name}</strong> workspace
      as <strong>{role_name}</strong>.
    </p>

    {personal_note_html}

    <a href="{invite_link}"
       style="display:inline-block; margin: 24px 0; padding: 12px 28px;
              background: #2563eb; color: white; border-radius: 6px;
              text-decoration: none; font-size: 15px; font-weight: bold;">
      Accept Invitation
    </a>

    <p style="color: #888; font-size: 13px;">
      This invitation expires in {expires_in_hours} hours.

      If you didn't expect this email, you can safely ignore it.
    </p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
    <p style="color: #aaa; font-size: 12px;">YCPA Platform</p>
  </div>
</body>
</html>
"""


def build_contact_email(name: str, email: str, subject: str, message: str) -> str:
    import html as html_lib
    safe_name = html_lib.escape(name)
    safe_subject = html_lib.escape(subject)
    safe_message = html_lib.escape(message)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>New contact message: {subject}</title>
</head>
<body style="margin:0;padding:0;background:#f3f2f1;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f2f1;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #edebe9;border-radius:2px;">
          <tr>
            <td style="background:#4f46e5;padding:20px 32px;">
              <p style="margin:0;font-size:18px;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">Yatzar Manage</p>
              <p style="margin:4px 0 0;font-size:11px;color:rgba(255,255,255,0.75);text-transform:uppercase;letter-spacing:0.06em;">Contact Form</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 20px;">
              <p style="margin:0 0 16px;font-size:15px;font-weight:600;color:#323130;">New contact message</p>
              <p style="margin:0;font-size:14px;color:#605e5c;line-height:1.6;">
                <strong style="color:#323130;">Name:</strong> {safe_name}

                <strong style="color:#323130;">Email:</strong> {email}

                <strong style="color:#323130;">Subject:</strong> {safe_subject}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px;">
              <div style="background:#faf9f8;border:1px solid #edebe9;border-radius:6px;padding:16px 20px;">
                <p style="margin:0;font-size:14px;color:#323130;line-height:1.6;white-space:pre-wrap;">{safe_message}</p>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px;border-top:1px solid #edebe9;">
              <p style="margin:0;font-size:11px;color:#a19f9d;line-height:1.6;">Sent from the Yatzar Manage contact form.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_otp_email(otp_code: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Password Reset Code</title>
</head>
<body style="margin:0;padding:0;background:#f3f2f1;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f2f1;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #edebe9;border-radius:2px;">
          <tr>
            <td style="background:#0078d4;padding:20px 32px;">
              <p style="margin:0;font-size:18px;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">YCPA</p>
              <p style="margin:4px 0 0;font-size:11px;color:rgba(255,255,255,0.75);text-transform:uppercase;letter-spacing:0.06em;">Password Reset</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 20px;">
              <p style="margin:0 0 16px;font-size:15px;font-weight:600;color:#323130;">Reset your password</p>
              <p style="margin:0;font-size:14px;color:#605e5c;line-height:1.6;">
                Use the verification code below to reset your password. This code expires in 10 minutes.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px;" align="center">
              <div style="display:inline-block;background:#f0f5ff;border:2px dashed #0078d4;border-radius:8px;padding:16px 40px;letter-spacing:8px;font-size:32px;font-weight:700;color:#0078d4;font-family:monospace;">
                {otp_code}
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px;">
              <p style="margin:0;font-size:13px;color:#a19f9d;line-height:1.6;">
                If you didn't request a password reset, you can safely ignore this email.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px;border-top:1px solid #edebe9;">
              <p style="margin:0;font-size:11px;color:#a19f9d;line-height:1.6;">YCPA Platform</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_file_share_invite_email(
    inviter_name: str,
    filename: str,
    register_link: str,
) -> str:
    """Returns HTML email body for CDE file share invite to unregistered user."""
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 24px;">
  <div style="max-width: 520px; margin: auto; background: white; border-radius: 8px; padding: 32px;">

    <h2 style="color: #1a1a1a;">A file has been shared with you</h2>

    <p style="color: #444; font-size: 15px;">
      <strong>{inviter_name}</strong> has shared a file with you on YCPA:
    </p>

    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 16px; margin: 16px 0;">
      <p style="margin: 0; color: #1a1a1a; font-size: 15px;">📄 {filename}</p>
    </div>

    <p style="color: #444; font-size: 15px;">
      Create a free YCPA account to view and collaborate on this file.
    </p>

    <a href="{register_link}"
       style="display:inline-block; margin: 24px 0; padding: 12px 28px;
              background: #2563eb; color: white; border-radius: 6px;
              text-decoration: none; font-size: 15px; font-weight: bold;">
      Create Account &amp; View File
    </a>

    <p style="color: #888; font-size: 13px;">
      If you didn't expect this email, you can safely ignore it.
    </p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
    <p style="color: #aaa; font-size: 12px;">YCPA Platform</p>
  </div>
</body>
</html>
"""



 
def build_notification_email(title: str, rows: dict) -> str:
    import html as html_lib
    cells = "".join(
        f'<tr><td style="padding:6px 12px;font-weight:600;color:#323130;">{html_lib.escape(str(k))}</td>'
        f'<td style="padding:6px 12px;color:#605e5c;">{html_lib.escape(str(v if v is not None else "-"))}</td></tr>'
        for k, v in rows.items()
    )
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#f3f2f1;font-family:'Segoe UI',Arial,sans-serif;">
<table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid #edebe9;margin:auto;">
<tr><td style="background:#0078d4;padding:16px 24px;color:#fff;font-size:16px;font-weight:700;">{html_lib.escape(title)}</td></tr>
<tr><td style="padding:16px 12px;"><table width="100%" cellpadding="0" cellspacing="0">{cells}</table></td></tr>
</table></body></html>"""


def build_demo_confirmation_email(name: str, scheduled_for: str, timezone_name: str, booking_id: str | None) -> str:
    import html as html_lib
    safe_name = html_lib.escape(name)
    safe_when = html_lib.escape(scheduled_for)
    safe_tz = html_lib.escape(timezone_name)
    safe_id = html_lib.escape(booking_id or "-")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Your Yatzar Manage demo is booked</title>
</head>
<body style="margin:0;padding:0;background:#f3f2f1;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f2f1;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #edebe9;border-radius:2px;">
          <tr>
            <td style="background:#0078d4;padding:20px 32px;">
              <p style="margin:0;font-size:18px;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">Yatzar Manage</p>
              <p style="margin:4px 0 0;font-size:11px;color:rgba(255,255,255,0.75);text-transform:uppercase;letter-spacing:0.06em;">Demo Booking</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 20px;">
              <p style="margin:0 0 16px;font-size:15px;font-weight:600;color:#323130;">Your demo is booked</p>
              <p style="margin:0;font-size:14px;color:#605e5c;line-height:1.6;">Hi {safe_name},</p>
              <p style="margin:12px 0 0;font-size:14px;color:#605e5c;line-height:1.6;">
                Thanks for your interest in Yatzar Manage. Our team will walk you through the platform at the time below
                and will contact you before the session.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 24px;">
              <table cellpadding="0" cellspacing="0" style="background:#faf9f8;border:1px solid #edebe9;width:100%;">
                <tr>
                  <td style="padding:14px 16px;">
                    <p style="margin:0;font-size:13px;color:#323130;"><strong>When:</strong> {safe_when}</p>
                    <p style="margin:4px 0 0;font-size:13px;color:#323130;"><strong>Timezone:</strong> {safe_tz}</p>
                    <p style="margin:4px 0 0;font-size:13px;color:#323130;"><strong>Booking ID:</strong> {safe_id}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px;border-top:1px solid #edebe9;">
              <p style="margin:0;font-size:11px;color:#a19f9d;line-height:1.6;">
                You received this email because a demo was requested with your address on Yatzar Manage.
                If this wasn't you, you can safely ignore it.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


# Calendar invite (.ics)
import asyncio
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage


def _ics_escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def _ics_fold(line: str) -> str:
    """RFC 5545: lines are at most 75 octets; continuation lines start with a space."""
    b, parts, limit = line.encode(), [], 75
    while len(b) > limit:
        cut = limit
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        parts.append(b[:cut].decode())
        b, limit = b[cut:], 74
    parts.append(b.decode())
    return "\r\n ".join(parts)


def build_ics(uid: str, starts_at: datetime, ends_at: datetime, summary: str, description: str,
              location: str, organizer_email: str, attendee_name: str, attendee_email: str) -> str:
    fmt = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
    cn = "".join(ch for ch in attendee_name if ch not in '\";:,')
    lines = [
        "BEGIN:VCALENDAR", "PRODID:-//Yatzar Manage//Demo Booking//EN", "VERSION:2.0", "CALSCALE:GREGORIAN",
        "METHOD:REQUEST", "BEGIN:VEVENT",
        f"UID:{uid}", f"DTSTAMP:{fmt(datetime.now(timezone.utc))}",
        f"DTSTART:{fmt(starts_at)}", f"DTEND:{fmt(ends_at)}",
        "SEQUENCE:0", "STATUS:CONFIRMED", "TRANSP:OPAQUE",
        f"SUMMARY:{_ics_escape(summary)}", f"DESCRIPTION:{_ics_escape(description)}",
        *([f"LOCATION:{_ics_escape(location)}"] if location else []),
        f"ORGANIZER;CN=Yatzar Manage:mailto:{organizer_email}",
        f'ATTENDEE;CN="{cn}";ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{attendee_email}',
        "BEGIN:VALARM", "TRIGGER:-PT30M", "ACTION:DISPLAY", "DESCRIPTION:Yatzar Manage demo", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR",
    ]
    return "\r\n".join(_ics_fold(line) for line in lines) + "\r\n"


def build_invite_message(to: str, subject: str, html: str, ics: str, sender: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, sender, to
    msg.set_content("Your Yatzar Manage demo is booked. The calendar invite is attached.")
    msg.add_alternative(html, subtype="html")
    msg.add_alternative(ics, subtype="calendar", params={"method": "REQUEST", "charset": "UTF-8"})
    msg.add_attachment(ics.encode("utf-8"), maintype="text", subtype="calendar", filename="invite.ics",
                       params={"method": "REQUEST", "charset": "UTF-8"})
    return msg


async def send_email_with_ics(to: str, subject: str, html: str, ics: str) -> None:
    s = get_settings()

    def _send() -> None:
        msg = build_invite_message(to, subject, html, ics, s.SMTP_FROM)
        if s.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(s.SMTP_HOST, s.SMTP_PORT, timeout=20) as smtp:
                smtp.login(s.SMTP_USER, s.SMTP_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(s.SMTP_HOST, s.SMTP_PORT, timeout=20) as smtp:
                smtp.starttls()
                smtp.login(s.SMTP_USER, s.SMTP_PASSWORD)
                smtp.send_message(msg)

    await asyncio.to_thread(_send)
