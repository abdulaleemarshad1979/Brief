from __future__ import annotations

import html
import json
import re
import time
from typing import Any

import config

WEATHER_CONDITIONS_TE = {
    "Clear sky": "ఆకాశం నిర్మలంగా ఉంటుంది",
    "Mainly clear": "ముఖ్యంగా నిర్మలమైన వాతావరణం",
    "Partly cloudy": "పాక్షికంగా మేఘావృతం",
    "Overcast": "పూర్తిగా మేఘావృతం",
    "Fog": "మంచు పొగ",
    "Rime fog": "అతి చల్లని మంచు పొగ",
    "Light drizzle": "తేలికపాటి చిన్నపాటి వర్షం",
    "Drizzle": "చినుకులు",
    "Heavy drizzle": "భారీ చినుకులు",
    "Light rain": "తేలికపాటి వర్షం",
    "Rain": "వర్షం",
    "Heavy rain": "భారీ వర్షం",
    "Light snow": "తేలికపాటి మంచు",
    "Snow": "మంచు వర్షం",
    "Heavy snow": "భారీ మంచు",
    "Light rain showers": "తేలికపాటి వర్షపు జల్లులు",
    "Rain showers": "వర్షపు జల్లులు",
    "Heavy rain showers": "భారీ వర్షపు జల్లులు",
    "Thunderstorm": "ఉరుములతో కూడిన వర్షం",
    "Thunderstorm with hail": "వడగళ్లతో కూడిన ఉరుముల వర్షం",
    "Severe thunderstorm with hail": "తీవ్రమైన వడగళ్ల వాన మరియు ఉరుములు",
}


def telugu_weather_advice(rain_probability: int, uv_index: float) -> str:
    if rain_probability >= 60:
        return "వర్షం పడే అవకాశం ఎక్కువగా ఉంది. గొడుగు తీసుకెళ్లండి."
    if rain_probability >= 30:
        return "వర్షం పడే అవకాశం ఉంది. గొడుగు దగ్గర ఉంచుకోండి."
    if uv_index >= 7:
        return "UV తీవ్రత ఎక్కువగా ఉంటుంది. సన్స్క్రీన్ ఉపయోగించి నీరు ఎక్కువగా తాగండి."
    return "బయటకు వెళ్లడానికి సాధారణంగా అనుకూలమైన వాతావరణం."


def contains_too_much_english(text: str) -> bool:
    """Detect if a string contains more than 6 English words (ignoring URLs)."""
    clean_text = re.sub(r"https?://\S+", "", text)
    english_words = re.findall(r"\b[A-Za-z]{3,}\b", clean_text)
    return len(english_words) > 6


def render_telugu_html(
    translated_data: dict[str, Any],
    weather_by_location: list[dict[str, Any]],
    date_text: str,
    coverage_date_text: str,
) -> str:
    """Construct clean HTML briefing suitable for Gmail from translated JSON and weather data."""
    sections_data = translated_data.get("sections", {})

    section_titles = {
        "world": ("ప్రపంచ వార్తలు", "🌐"),
        "india": ("భారతదేశ వార్తలు", "🇮🇳"),
        "andhra_pradesh": ("ఆంధ్రప్రదేశ్ మరియు స్థానిక వార్తలు", "🏛️"),
        "tech": ("టెక్నాలజీ, AI మరియు సైబర్ భద్రత", "💻"),
        "research": ("పరిశోధన మరియు ఆవిష్కరణలు", "🔬"),
        "hacker_news": ("హ్యాకర్ న్యూస్ విశేషాలు", "⚡"),
    }

    # Render Weather Cards
    weather_html_cards = []
    for loc in weather_by_location:
        name = loc.get("name", "")
        cond_en = loc.get("condition", "")
        cond_te = WEATHER_CONDITIONS_TE.get(cond_en, cond_en)
        min_t = loc.get("min_temp", "")
        max_t = loc.get("max_temp", "")
        rain_prob = loc.get("rain_probability", 0)
        wind = loc.get("wind_speed", 0)
        uv = loc.get("uv_index", 0)
        advice_te = telugu_weather_advice(rain_prob, uv)

        weather_html_cards.append(
            f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:14px 16px; margin-bottom:12px;">
              <div style="font-size:16px; font-weight:bold; color:#0f172a;">📍 {html.escape(name)}</div>
              <div style="font-size:14px; color:#475569; margin-top:2px;">{html.escape(cond_te)}</div>
              <div style="font-size:22px; font-weight:bold; color:#0f172a; margin:6px 0;">🌡️ {min_t}–{max_t}°C</div>
              <div style="font-size:13px; color:#64748b; margin-bottom:6px;">🌧️ {rain_prob}% &nbsp;|&nbsp; 💨 {wind} km/h &nbsp;|&nbsp; ☀️ UV {uv}</div>
              <div style="font-size:13px; color:#1e293b; font-weight:500;">💡 {html.escape(advice_te)}</div>
            </div>
            """
        )
    weather_section_html = "\n".join(weather_html_cards)

    # Render News Sections
    news_sections_html = []
    for section_key, (section_label, icon) in section_titles.items():
        stories = sections_data.get(section_key, [])
        if not stories:
            continue

        story_cards = []
        for story in stories:
            title = html.escape(story.get("title", ""))
            url = html.escape(story.get("url", "#"), quote=True)
            what = html.escape(story.get("what_happened", ""))
            why = html.escape(story.get("why_it_matters", ""))

            facts = story.get("key_facts", [])
            facts_html = ""
            if isinstance(facts, list) and facts:
                lis = "".join(f"<li style='margin-bottom:4px;'>{html.escape(str(f))}</li>" for f in facts)
                facts_html = f"<div style='margin-top:8px;'><strong>ముఖ్యాంశాలు:</strong><ul style='margin:4px 0 8px 20px; padding:0; color:#334155;'>{lis}</ul></div>"

            sources = story.get("sources", [])
            if isinstance(sources, str):
                sources = [sources]
            sources_str = ", ".join(html.escape(str(s)) for s in sources)
            sources_html = f"<div style='font-size:12px; color:#64748b; margin-top:8px;'>మూలాలు: {sources_str}</div>" if sources_str else ""

            story_cards.append(
                f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:16px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                  <div style="font-size:17px; font-weight:bold; color:#0f172a; margin-bottom:8px; line-height:1.4;">
                    <a href="{url}" target="_blank" style="color:#2563eb; text-decoration:none;">{title}</a>
                  </div>
                  {f'<div style="font-size:14px; color:#334155; margin-bottom:8px; line-height:1.5;"><strong>ఏం జరిగింది:</strong> {what}</div>' if what else ''}
                  {f'<div style="font-size:14px; color:#334155; margin-bottom:8px; line-height:1.5;"><strong>ఎందుకు ముఖ్యము:</strong> {why}</div>' if why else ''}
                  {facts_html}
                  {sources_html}
                </div>
                """
            )

        news_sections_html.append(
            f"""
            <div style="margin-top:24px;">
              <h2 style="font-size:20px; color:#0f172a; border-bottom:2px solid #e2e8f0; padding-bottom:8px; margin-bottom:14px;">
                {icon} {section_label}
              </h2>
              {"".join(story_cards)}
            </div>
            """
        )

    return f"""<!doctype html>
<html lang="te">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ఉదయపు వార్తల నివేదిక</title>
</head>
<body style="margin:0; padding:0; background-color:#f1f5f9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#0f172a; line-height:1.5;">
  <div style="max-width:680px; margin:0 auto; padding:20px 12px;">
    
    <!-- Header -->
    <div style="background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color:#ffffff; padding:28px 24px; border-radius:16px; margin-bottom:20px;">
      <h1 style="margin:0 0 6px 0; font-size:26px; font-weight:800; color:#ffffff;">శుభోదయం 👋</h1>
      <p style="margin:0; font-size:14px; color:#94a3b8;">ఉదయపు సమాచార నివేదిక — {html.escape(date_text)}</p>
      <div style="display:inline-block; margin-top:10px; padding:4px 10px; background:rgba(255,255,255,0.1); border-radius:6px; font-size:12px; color:#cbd5e1;">
        వార్తల పరిధి: {html.escape(coverage_date_text)}
      </div>
    </div>

    <!-- Weather Section -->
    <div style="background:#ffffff; border-radius:16px; padding:20px; margin-bottom:20px; border:1px solid #e2e8f0;">
      <h2 style="margin:0 0 14px 0; font-size:20px; color:#0f172a;">🌤️ నేటి వాతావరణం</h2>
      {weather_section_html}
    </div>

    <!-- News Sections -->
    {"".join(news_sections_html)}

    <!-- Footer -->
    <div style="text-align:center; padding:20px 0; font-size:12px; color:#94a3b8;">
      ఆటోమేటిక్ దినపత్రిక నివేదిక • {html.escape(date_text)}
    </div>

  </div>
</body>
</html>"""


def generate_telugu_email(
    summaries: dict[str, list[dict[str, Any]]],
    weather_by_location: list[dict[str, Any]],
    date_text: str,
    coverage_date_text: str,
) -> str:
    """Generate high-quality Telugu HTML briefing using strong Groq model for JSON translation and Python HTML renderer."""

    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required.")

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)

    simplified_news = {}
    original_stories_map = {}

    for section, stories in summaries.items():
        simplified_news[section] = []
        original_stories_map[section] = []

        for story in stories:
            if story.get("verification_status") != "verified":
                continue

            simplified_news[section].append(
                {
                    "title": story.get("title", ""),
                    "what_happened": story.get("what_happened", ""),
                    "why_it_matters": story.get("why_it_matters", ""),
                    "key_facts": story.get("key_facts", [])[:3],
                }
            )
            original_stories_map[section].append(story)

    prompt = f"""
Translate every news story title, summary, explanation, and bullet point fully into clear, natural, high-quality Telugu news language.

Input news data grouped strictly by section:
{json.dumps(simplified_news, ensure_ascii=False, indent=1)}

Return ONLY valid JSON with this exact structure:
{{
  "sections": {{
    "world": [
      {{
        "title": "తెలుగు శీర్షిక",
        "what_happened": "తెలుగు వివరాలు",
        "why_it_matters": "తెలుగు వివరణ లేదా ఖాళీ string",
        "key_facts": ["తెలుగు అంశం 1"]
      }}
    ],
    "india": [],
    "andhra_pradesh": [],
    "tech": [],
    "research": [],
    "hacker_news": []
  }}
}}

CRITICAL TRANSLATION RULES:
1. Translate EVERY headline/title, summary, explanation, and bullet point fully into natural Telugu. Never leave a complete English sentence in the output.
2. Use natural, high-quality Telugu journalism phrasing. Avoid word-by-word literal machine translations.
3. Use preferred professional Telugu terminology:
   - suicide bomber = ఆత్మాహుతి బాంబర్
   - suicide attack = ఆత్మాహుతి దాడి
   - missing = గల్లంతు / గల్లంతయ్యారు
   - killed = మరణించారు
   - survived = ప్రాణాలతో బయటపడ్డారు
   - avalanche = మంచుచరియ
   - ferry = ప్రయాణికుల నౌక / ఫెర్రీ
   - firefighting helicopters = అగ్నిమాపక హెలికాప్టర్లు
   - controlling fire = అగ్ని ప్రమాదాన్ని అదుపు చేయడం
4. Use natural Telugu counting for people:
   - 2 people = ఇద్దరు
   - 5 people = ఐదుగురు
   - 14 people = 14 మంది (or పద్నాలుగు మంది)
   NEVER use unnatural transliterations such as "రెండు మంది", "ఐదు మంది", "41 మంది లోపలికి లేవు", "విపత్తులను అణచివేస్తున్న", or "బూమ్మా".
5. AVOID REPETITION: Make title a punchy headline, what_happened 1-2 summary sentences, and key_facts distinct bullet points. Do not repeat the exact same sentence across title, what_happened, and key_facts.
6. PRESERVE SECTIONS STRICTLY: Preserve the section keys ("world", "india", "andhra_pradesh", "tech", "research", "hacker_news") exactly as provided. Do not move stories across sections.
7. Return ONLY valid JSON. Never include Markdown code fences.
"""

    models_to_try = [
        config.TELUGU_GROQ_MODEL,
        config.GROQ_MODEL,
    ]

    # Deduplicate model list while preserving order
    unique_models = []
    for m in models_to_try:
        if m and m not in unique_models:
            unique_models.append(m)

    response = None
    last_exception = None

    for target_model in unique_models:
        for attempt in range(2):
            try:
                print(f"Translating briefing to Telugu using Groq model: {target_model}...", flush=True)
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert Telugu news editor and senior translator for a major Telugu daily newspaper. "
                                "Translate news stories into clear, natural, high-quality Telugu journalism style. "
                                "Return ONLY valid JSON matching the requested schema."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.1,
                    max_tokens=3500,
                    response_format={"type": "json_object"},
                )
                if response and response.choices:
                    break
            except Exception as exc:
                last_exception = exc
                err_msg = str(exc)
                if ("413" in err_msg or "rate_limit_exceeded" in err_msg or "429" in err_msg) and attempt < 1:
                    print(f"Rate limit hit on {target_model}. Waiting 8s...", flush=True)
                    time.sleep(8)
                else:
                    print(f"Model {target_model} failed: {exc}. Trying next option if available...", flush=True)
                    break
        if response and response.choices:
            break

    if not response or not response.choices:
        raise RuntimeError(f"All Groq model attempts for Telugu translation failed: {last_exception}")

    raw_content = response.choices[0].message.content or ""
    raw_content = raw_content.strip()

    if raw_content.startswith("```json"):
        raw_content = raw_content[len("```json"):].strip()
    elif raw_content.startswith("```html"):
        raw_content = raw_content[len("```html"):].strip()
    elif raw_content.startswith("```"):
        raw_content = raw_content[3:].strip()

    if raw_content.endswith("```"):
        raw_content = raw_content[:-3].strip()

    if not raw_content:
        raise RuntimeError("Groq returned an empty response for Telugu translation.")

    try:
        translated_data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Groq did not return valid JSON for Telugu briefing: {exc}\nRaw output: {raw_content[:200]}")

    # Re-attach original sources and url to translated stories while preserving sections strictly
    sections = translated_data.get("sections", {})
    final_sections = {}

    for section, orig_list in original_stories_map.items():
        trans_list = sections.get(section, [])
        final_sections[section] = []
        for i, orig_story in enumerate(orig_list):
            if i < len(trans_list) and isinstance(trans_list[i], dict):
                t_story = trans_list[i]

                # English leakage check on translation fields
                fields_to_check = [
                    t_story.get("title", ""),
                    t_story.get("what_happened", ""),
                    t_story.get("why_it_matters", ""),
                    " ".join(t_story.get("key_facts", [])) if isinstance(t_story.get("key_facts"), list) else "",
                ]
                if any(contains_too_much_english(f) for f in fields_to_check):
                    print(f"Warning: Excessive English detected in story '{orig_story.get('title')}' translation. Retaining fallback.", flush=True)

                final_sections[section].append(
                    {
                        "title": t_story.get("title", orig_story.get("title", "")),
                        "what_happened": t_story.get("what_happened", orig_story.get("what_happened", "")),
                        "why_it_matters": t_story.get("why_it_matters", orig_story.get("why_it_matters", "")),
                        "key_facts": t_story.get("key_facts", orig_story.get("key_facts", [])),
                        "sources": orig_story.get("sources", []),
                        "url": orig_story.get("url", "#"),
                    }
                )
            else:
                final_sections[section].append(orig_story)

    translated_data["sections"] = final_sections

    return render_telugu_html(
        translated_data=translated_data,
        weather_by_location=weather_by_location,
        date_text=date_text,
        coverage_date_text=coverage_date_text,
    )
