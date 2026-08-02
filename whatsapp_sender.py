from __future__ import annotations

import requests


class WhatsAppSendError(RuntimeError):
    pass


def send_whatsapp_template(
    *,
    access_token: str,
    phone_number_id: str,
    recipient_number: str,
    template_name: str,
    language_code: str,
    message_text: str,
    graph_api_version: str = "v23.0",
) -> None:
    """Send the Telugu briefing through an approved WhatsApp template."""

    url = (
        f"https://graph.facebook.com/{graph_api_version}/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code,
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": message_text,
                        }
                    ],
                }
            ],
        },
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise WhatsAppSendError(
            f"WhatsApp API returned {response.status_code}: "
            f"{response.text}"
        )

    print("Telugu WhatsApp briefing sent successfully.", flush=True)
