import json
import logging
from typing import Any
import config
from news import TRUSTED_SOURCES

logger = logging.getLogger(__name__)


def compute_verification_status(sources: list[str], title: str, summary: str) -> str:
    """Calculate story verification status strictly in Python based on source quality and evidence."""
    clean_sources = [str(s).strip() for s in sources if s and str(s).strip()]

    # Count trusted sources
    trusted_count = sum(
        1 for s in clean_sources
        if any(t.lower() in s.lower() for t in TRUSTED_SOURCES)
    )

    low_text = (title + " " + summary).lower()

    # Rumor / Leak / Speculation detection
    if any(k in low_text for k in ("leak", "leaked", "rumor", "rumoured", "unconfirmed", "speculation", "alleged transcript")):
        return "rumor"

    # Developing / Ongoing investigation detection
    if any(k in low_text for k in ("alleged", "police probe", "investigation", "developing", "casualty count", "protesters allege")):
        return "developing"

    # Official primary sources
    primary = {"pib", "reuters", "ap", "associated press", "bbc", "news on air", "openai", "google", "microsoft", "nvidia", "arxiv"}
    has_primary = any(any(p in s.lower() for p in primary) for s in clean_sources)

    if trusted_count >= 2 or has_primary:
        return "verified"
    elif trusted_count >= 1:
        return "single_source"
    else:
        return "unverified"


def fallback_summaries(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return raw articles formatted as structured summary dicts when AI is disabled or fails."""
    cards = []
    for art in articles:
        sources = [art.get("source", "RSS Feed")]
        title = art.get("title", "Untitled Story")
        summary = art.get("summary") or title
        v_status = compute_verification_status(sources, title, summary)
        cards.append(
            {
                "title": title,
                "what_happened": summary,
                "why_it_matters": "",
                "key_facts": [],
                "sources": sources,
                "url": art.get("url", "#"),
                "verification_status": v_status,
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
                f"    Snippet: {item.get('summary', '')[:400]}\n"
            )

        prompt = f"""You are a strict, quality-first research analyst compiling a morning briefing section for '{category_label}'.
Below is a list of recent articles collected for this section:

{"---".join(material)}

Instructions:
1. QUALITY-FIRST SELECTION: Select ONLY the most important, credible, and well-supported stories.
   - REJECT: rumours, leaks, clickbait, duplicate reports, single-source claims from weak publications, routine congratulatory posts, celebrity/entertainment news, low-value phone launch news, speculative product articles.
   - Include a story ONLY IF at least two trusted independent sources support it, OR one official primary source confirms it.
   - Prefer fewer high-quality stories over many weak stories.
2. STRICT SOURCE GROUNDING: Use ONLY facts explicitly present in the supplied titles, snippets, or body texts above.
   - Do NOT invent casualty numbers, causes, arrests, political motivations, economic effects, or future consequences.
   - If the source material is insufficient, explicitly state: "Available source information is limited."
3. CATEGORY RELEVANCE: Exclude stories that are unrelated to '{category_label}'.
   - For example, do NOT include international or US-Iran news inside India News.
   - For Technology, prioritize AI, cybersecurity, software releases, developer tools, cloud infrastructure, open source, and startups.
4. NO HYPERBOLE: Do not use generic buzzwords such as "significant development", "game-changer", or "has the potential to" unless directly justified by the source text.
5. WHY IT MATTERS: For "why_it_matters", explain a concrete consequence ONLY when supported by the source material. If no meaningful consequence is available, return an empty string "". Do not simply restate the headline.
6. FORMAT RULES: Every item in "key_facts" MUST be a plain text string. Never return dictionaries or objects inside "key_facts".

Return ONLY a valid JSON object with a key "stories" containing a list of 2 to 4 high-quality objects.
Each object MUST strictly follow this JSON schema:
{{
  "title": "Concise factual headline",
  "what_happened": "2-3 factual sentences explaining what occurred",
  "why_it_matters": "1-2 factual sentences on direct impact, or empty string '' if unavailable",
  "key_facts": ["Fact 1 as plain string", "Fact 2 as plain string"],
  "sources": ["Source Name 1", "Source Name 2"],
  "article_index": 1
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
            max_tokens=4096,
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        stories = parsed.get("stories") or parsed.get("data") or []

        cleaned_stories = []
        if isinstance(stories, list):
            for s in stories:
                if not isinstance(s, dict):
                    continue

                # Key facts sanitization
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

                # Map article URL from input articles using article_index
                idx = s.get("article_index", 1)
                url = "#"
                if isinstance(idx, int) and 1 <= idx <= len(articles):
                    url = articles[idx - 1].get("url", "#")
                elif s.get("url"):
                    url = s["url"]
                s["url"] = url

                # Ensure exact JSON key for why_it_matters if model mis-keys it
                if "why_it_matters" not in s:
                    for k in list(s.keys()):
                        if "why" in k or "matters" in k:
                            s["why_it_matters"] = s.pop(k)
                            break
                    else:
                        s["why_it_matters"] = ""

                # Compute verification status strictly in Python
                sources = s.get("sources") or []
                title = s.get("title") or ""
                what = s.get("what_happened") or ""
                s["verification_status"] = compute_verification_status(sources, title, what)

                cleaned_stories.append(s)

        if len(cleaned_stories) > 0:
            return cleaned_stories

    except Exception as exc:
        logger.warning(f"Groq summarization failed for {category_label}: {exc}. Using fallback.")

    return fallback_summaries(articles)
