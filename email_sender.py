from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


def send_email(
    sender: str,
    app_password: str,
    recipient: str,
    subject: str,
    html: str,
) -> None:
    sender = (sender or "").strip().replace("\r", "").replace("\n", "")
    app_password = (app_password or "").strip().replace("\r", "").replace("\n", "")
    recipient = (recipient or "").strip().replace("\r", "").replace("\n", "")
    subject = (subject or "").strip().replace("\r", "").replace("\n", "")

    if not sender or not app_password or not recipient:
        raise ValueError(
            "Sender, app password and recipient must be configured."
        )

    message = EmailMessage()

    message["From"] = f"Abdul Morning Briefing <{sender}>"
    message["To"] = recipient
    message["Reply-To"] = sender
    message["Subject"] = subject

    # Important standard email headers
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain="gmail.com")

    message.set_content(
        "శుభోదయం. ఇది మీ రోజువారీ తెలుగు వార్తలు మరియు "
        "వాతావరణ సమాచార నివేదిక."
    )

    message.add_alternative(
        html,
        subtype="html",
    )

    print(
        f"SMTP sending to exact address: {recipient!r}",
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
                f"Recipient refused by SMTP server: {refused}"
            )

    print(
        f"SMTP accepted email delivery for: {recipient!r}",
        flush=True,
    )
