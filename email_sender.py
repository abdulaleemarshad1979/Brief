from __future__ import annotations

import smtplib
from email.message import EmailMessage


def send_email(
    sender: str,
    app_password: str,
    recipient: str,
    subject: str,
    html: str,
) -> None:
    if not sender or not app_password or not recipient:
        raise ValueError(
            "EMAIL_ADDRESS, EMAIL_APP_PASSWORD and RECIPIENT_EMAIL must be configured."
        )

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content("Your email client does not support the HTML morning briefing.")
    message.add_alternative(html, subtype="html")

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(sender, app_password)
        smtp.send_message(message)
