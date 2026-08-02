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

        material = []
        for idx, item in enumerate(articles[:10], 1):
            material.append(
                f"[{idx}] Title: {item.get('title')}\n"
                f"    Source: {item.get('source')}\n"
                f"    URL: {item.get('url')}\n"
                f"    Snippet/Body: {item.get('summary', '')[:500]}\n"
            )

        prompt = f"""You are a strict, factual research analyst compiling a morning briefing section for '{category_label}'.
Below is a list of recent articles collected for this section:

{"---".join(material)}

Instructions:
1. STRICT SOURCE GROUNDING: Use ONLY facts explicitly present in the supplied titles, snippets, or body texts above.
   - Do NOT invent casualty numbers, causes, arrests, political motivations, economic effects, or future consequences.
   - If the source material is insufficient, explicitly state: "Available source information is limited."
2. CATEGORY RELEVANCE: Exclude stories that are unrelated to '{category_label}'.
   - For example, do NOT include international or US-Iran news inside India News.
   - For Technology, prioritize AI, cybersecurity, software releases, developer tools, startups, and infrastructure. Exclude generic car reviews or unverified gadget rumors.
3. NO HYPERBOLE: Do not use generic buzzwords such as "significant development", "game-changer", or "has the potential to" unless directly justified by the source text.
4. WHY IT MATTERS: For "why_it_matters", explain a concrete consequence ONLY when supported by the source material. If no meaningful consequence is available, return an empty string "". Do not simply restate the headline.
5. FORMAT RULES: Every item in "key_facts" MUST be a plain text string. Never return dictionaries or objects inside "key_facts".

Return ONLY a valid JSON object with a key "stories" containing a list of 2 to 5 high-quality objects.
Each object MUST strictly follow this JSON schema:
{{
  "title": "Concise factual headline",
  "what_happened": "2-3 factual sentences explaining what occurred",
  "why_it_matters": "1-2 factual sentences on direct impact, or empty string '' if unavailable",
  "key_facts": ["Fact or statistic 1 as a plain string", "Fact 2 as a plain string"],
  "sources": ["Source Name 1", "Source Name 2"],
  "url": "Primary URL"
}}
"""

        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional factual research analyst. Output strictly valid JSON without fluff.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2048,
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        stories = parsed.get("stories") or parsed.get("data") or []

        # Sanitize key_facts in returned stories to guarantee all key_facts items are strings
        cleaned_stories = []
        if isinstance(stories, list):
            for s in stories:
                if not isinstance(s, dict):
                    continue
                raw_facts = s.get("key_facts") or []
                clean_facts = []
                if isinstance(raw_facts, list):
                    for f in raw_facts:
                        if isinstance(f, dict):
                            if "value" in f and "label" in f:
                                clean_facts.append(f"{f['label']}: {f['value']}")
                            elif "bullet" in f:
                                clean_facts.append(str(f["bullet"]))
                            else:
                                clean_facts.append(" · ".join(str(v) for v in f.values()))
                        elif f:
                            clean_facts.append(str(f))
                s["key_facts"] = clean_facts
                cleaned_stories.append(s)

        if len(cleaned_stories) > 0:
            return cleaned_stories

    except Exception as exc:
        logger.warning(f"Groq summarization failed for {category_label}: {exc}. Using fallback.")

    return fallback_summaries(articles)
