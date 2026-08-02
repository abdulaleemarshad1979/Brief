import json
import logging
from typing import Any
import config

logger = logging.getLogger(__name__)


def fallback_summaries(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return raw articles formatted as structured summary dicts when AI is disabled or fails."""
    cards = []
    for art in articles:
        cards.append(
            {
                "title": art.get("title", "Untitled Story"),
                "what_happened": art.get("summary") or art.get("title", ""),
                "why_it_matters": "Developing story from daily RSS feeds.",
                "key_facts": [],
                "sources": [art.get("source", "RSS Feed")],
                "url": art.get("url", "#"),
            }
        )
    return cards


def summarize_section_with_groq(
    category_label: str, articles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Synthesize raw articles into structured research summaries using Groq API."""
    if not config.GROQ_API_KEY or not articles:
        return fallback_summaries(articles)

    try:
        from groq import Groq

        client = Groq(api_key=config.GROQ_API_KEY)

        # Prepare material for Groq prompt
        material = []
        for idx, item in enumerate(articles[:8], 1):
            material.append(
                f"[{idx}] Title: {item.get('title')}\n"
                f"    Source: {item.get('source')}\n"
                f"    URL: {item.get('url')}\n"
                f"    Snippet: {item.get('summary', '')[:400]}\n"
            )

        prompt = f"""You are an expert news research assistant compiling a morning briefing section for '{category_label}'.
Below is a list of recent articles:

{"---".join(material)}

Synthesize these articles into a concise list of top 3 to 5 distinct, high-impact story cards. Combine duplicates covering the same event into a single researched card listing multiple sources.

Return ONLY a valid JSON object with a key "stories" containing a list of objects. Each object MUST have:
- "title": Concise headline of what happened
- "what_happened": 2-3 sentences explaining the event clearly
- "why_it_matters": 1-2 sentences on impact and future context
- "key_facts": A list of 1-3 key numbers, statistics, or bullet points
- "sources": A list of source names covering this story (e.g. ["BBC", "Reuters"])
- "url": Primary article link URL
"""

        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional research analyst. Respond ONLY with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2048,
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        stories = parsed.get("stories") or parsed.get("data") or []

        if isinstance(stories, list) and len(stories) > 0:
            return stories

    except Exception as exc:
        logger.warning(f"Groq summarization failed for {category_label}: {exc}. Using fallback.")

    return fallback_summaries(articles)
