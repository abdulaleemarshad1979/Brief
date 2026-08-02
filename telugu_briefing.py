from __future__ import annotations

from typing import Any

import config


SECTION_NAMES = {
    "world": "🌍 ప్రపంచ వార్తలు",
    "india": "🇮🇳 భారతదేశ వార్తలు",
    "andhra_pradesh": "📍 ఆంధ్రప్రదేశ్ వార్తలు",
    "tech": "💻 టెక్నాలజీ మరియు AI",
    "research": "🔬 పరిశోధన మరియు ఆవిష్కరణలు",
}


def _clean_story_data(summaries: dict[str, list[dict[str, Any]]]) -> dict:
    compact: dict[str, list[dict[str, str]]] = {}

    for section, stories in summaries.items():
        if section == "hacker_news":
            continue

        compact[section] = []

        for story in stories[:3]:
            status = story.get("verification_status", "")

            # WhatsApp receives only the strongest stories.
            if status != "verified":
                continue

            compact[section].append(
                {
                    "title": str(story.get("title", "")),
                    "summary": str(story.get("what_happened", "")),
                }
            )

    return compact


def generate_telugu_briefing(
    *,
    summaries: dict[str, list[dict[str, Any]]],
    weather_by_location: list[dict[str, Any]],
    date_text: str,
) -> str:
    """Translate the verified English report into concise Telugu."""

    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required for Telugu generation.")

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)
    compact_news = _clean_story_data(summaries)

    weather_lines = []

    for weather in weather_by_location:
        weather_lines.append(
            {
                "location": weather["name"],
                "minimum_temperature": weather["min_temp"],
                "maximum_temperature": weather["max_temp"],
                "rain_probability": weather["rain_probability"],
                "condition": weather["condition"],
            }
        )

    prompt = f"""
Create a concise Telugu WhatsApp morning briefing.

Date:
{date_text}

Weather:
{weather_lines}

Verified news:
{compact_news}

Strict rules:

1. Write all reader-facing content in natural, simple Telugu.
2. Preserve names of people, organisations and technical products accurately.
3. Do not add or infer facts.
4. Include only stories supplied in the input.
5. Do not include source links.
6. Do not include unverified or single-source stories.
7. Use no more than three stories per section.
8. Keep the complete message below 3,500 characters.
9. Keep temperatures and percentages unchanged.
10. Do not use Markdown tables.
11. Return only the final WhatsApp message.

Use this structure:

శుభోదయం, అబ్దుల్ 👋
{date_text}

🌦️ నేటి వాతావరణం
[One compact line for every location]

🌍 ప్రపంచ వార్తలు
[Numbered stories]

🇮🇳 భారతదేశ వార్తలు
[Numbered stories]

📍 ఆంధ్రప్రదేశ్ వార్తలు
[Numbered stories]

💻 టెక్నాలజీ మరియు AI
[Numbered stories]

🔬 పరిశోధన మరియు ఆవిష్కరణలు
[Numbered stories]

No section should be shown when it contains no stories.
"""

    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional Telugu news editor. "
                    "Translate accurately and never invent information."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=1800,
    )

    message = response.choices[0].message.content or ""
    message = message.strip()

    if not message:
        raise RuntimeError("Groq returned an empty Telugu briefing.")

    return message[:3500]
