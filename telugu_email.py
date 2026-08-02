from __future__ import annotations

from typing import Any

import config


def generate_telugu_email(
    summaries: dict[str, list[dict[str, Any]]],
    weather_by_location: list[dict[str, Any]],
    date_text: str,
    coverage_date_text: str,
) -> str:
    """Generate a full Telugu HTML briefing from verified English data."""

    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required.")

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)

    verified_news = {}

    for section, stories in summaries.items():
        verified_news[section] = []

        for story in stories:
            if story.get("verification_status") != "verified":
                continue

            verified_news[section].append(
                {
                    "title": story.get("title", ""),
                    "what_happened": story.get("what_happened", ""),
                    "why_it_matters": story.get("why_it_matters", ""),
                    "key_facts": story.get("key_facts", []),
                    "sources": story.get("sources", []),
                    "url": story.get("url", "#"),
                }
            )

    weather_data = [
        {
            "location": item["name"],
            "condition": item["condition"],
            "minimum_temperature": item["min_temp"],
            "maximum_temperature": item["max_temp"],
            "rain_probability": item["rain_probability"],
            "wind_speed": item["wind_speed"],
            "uv_index": item["uv_index"],
            "advice": item["advice"],
        }
        for item in weather_by_location
    ]

    prompt = f"""
Create a complete Telugu morning briefing as clean HTML.

Today's date:
{date_text}

News coverage date:
{coverage_date_text}

Weather:
{weather_data}

Verified news:
{verified_news}

Rules:
1. Write all reader-facing content in clear, natural Telugu.
2. Do not invent or expand facts.
3. Use only the supplied verified information.
4. Preserve names, company names, product names and source names accurately.
5. Keep URLs unchanged.
6. Do not include unverified or single-source stories.
7. Keep source names in English.
8. Translate weather conditions and advice into Telugu.
9. Return only complete HTML suitable for Gmail.
10. Use inline CSS because email clients may remove external styles.

Use these Telugu sections:

శుభోదయం, అక్బర్ బాషా గారు 👋
వార్తల పరిధి
నేటి వాతావరణం
ప్రపంచ వార్తలు
భారతదేశ వార్తలు
ఆంధ్రప్రదేశ్ మరియు స్థానిక వార్తలు
టెక్నాలజీ, AI మరియు సైబర్ భద్రత
పరిశోధన మరియు ఆవిష్కరణలు

For every story show:
- headline
- ఏం జరిగింది
- ఎందుకు ముఖ్యము, only when meaningful
- ముఖ్యాంశాలు
- మూలాలు
"""

    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional Telugu news editor. "
                    "Return accurate HTML only and never invent facts."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=5000,
    )

    html_content = response.choices[0].message.content or ""
    html_content = html_content.strip()

    if not html_content:
        raise RuntimeError("Groq returned an empty Telugu email.")

    return html_content
