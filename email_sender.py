from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid


def clean_header_value(value: str) -> str:
    """Remove spaces and dangerous newline characters from email headers."""
    return value.replace("\r", "").replace("\n", "").strip()


def send_email(
    sender: str,
    app_password: str,
    recipient: str,
    subject: str,
    html: str,
) -> None:
    sender = clean_header_value(sender)
    recipient = clean_header_value(recipient)
    subject = clean_header_value(subject)
    app_password = app_password.replace(" ", "").strip()

    if not sender or not app_password or not recipient:
        raise ValueError(
            "Sender, app password and recipient must be configured."
        )

    message = EmailMessage()

    message["From"] = formataddr(
        ("Abdul Morning Briefing", sender)
    )
    message["To"] = recipient
    message["Reply-To"] = sender
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid()

    message.set_content(
        "శుభోదయం. ఇది మీ రోజువారీ తెలుగు వార్తలు మరియు "
        "వాతావరణ సమాచార నివేదిక."
    )

    message.add_alternative(
        html,
        subtype="html",
    )

    print(
        f"Sending email to: {recipient!r}",
        flush=True,
    )

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(sender, app_password)

        refused = smtp.send_message(
            message,
            from_addr=sender,
            to_addrs=[recipient],
        )

        if refused:
            raise RuntimeError(
                f"SMTP refused recipient: {refused}"
            )

    print(
        f"SMTP accepted email for: {recipient!r}",
        flush=True,
    )
