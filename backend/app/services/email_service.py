import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

settings = get_settings()


def send_email(to_email: str, subject: str, body: str) -> bool:
    if not settings.smtp_host or not settings.smtp_sender:
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
    except Exception:
        return False

    return True


def send_approval_email(to_email: str, full_name: str, approved: bool, reason: str | None = None) -> bool:

    status = "Approved" if approved else "Rejected"
    body = [
        f"Hello {full_name},",
        "",
        f"Your attendance registration has been {status}.",
    ]
    if reason:
        body.append(f"Reason: {reason}")
    body.append("\nYou can contact your administrator for assistance.")

    return send_email(
        to_email=to_email,
        subject=f"Registration {status}",
        body="\n".join(body),
    )
