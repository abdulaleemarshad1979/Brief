from __future__ import annotations

import html
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import config
import news
from ai_summarizer import summarize_section_with_groq
from email_sender import send_email
from news import get_all_news, INVALID_SOURCES
from weather import get_weather


def format_fact(fact) -> str:
    if isinstance(fact, dict):
        if "value" in fact and "label" in fact:
            return f'{fact["label"]}: {fact["value"]}'
        if "bullet" in fact:
            return str(fact["bullet"])
        return " · ".join(str(value) for value in fact.values())
    return str(fact)


def render_ai_cards(stories: list[dict]) -> str:
    if not stories:
        return '<div class="empty">No recent stories were available from the configured feeds.</div>'

    cards = []
    for item in stories:
        title = html.escape(item.get("title", "Untitled"))
        url = html.escape(item.get("url", "#"), quote=True)
        what = html.escape(item.get("what_happened", ""))
        why = html.escape(item.get("why_it_matters", ""))

        facts_html = ""
        key_facts = item.get("key_facts") or []
        if isinstance(key_facts, list) and len(key_facts) > 0:
            lis = "".join(f"<li>{html.escape(format_fact(fact))}</li>" for fact in key_facts)
            facts_html = f'<ul class="key-facts">{lis}</ul>'

        status = item.get("verification_status", "unverified")
        badge_labels = {
            "verified": "✅ Verified",
            "developing": "🟡 Developing",
            "single_source": "⚠️ Single source",
            "unverified": "❓ Unverified",
            "rumor": "🗣️ Rumour / leak",
        }
        badge_text = badge_labels.get(status, "❓ Unverified")
        status_badge_html = f'<span class="status-badge badge-{html.escape(status)}">{badge_text}</span>'

        raw_sources = item.get("sources") or []
        if isinstance(raw_sources, str):
            raw_sources = [raw_sources]

        clean_sources = []
        for s in raw_sources:
            st = str(s).strip()
            if not st or any(inv.lower() in st.lower() for inv in INVALID_SOURCES):
                continue
            if st not in clean_sources:
                clean_sources.append(st)

        source_str = ", ".join(clean_sources)
        meta_html = f'<span class="meta-tag">Sources: {html.escape(source_str)}</span>' if source_str else ""

        cards.append(
            f"""
            <div class="ai-card">
              <h3>{status_badge_html}<a href="{url}" target="_blank" rel="noopener">{title}</a></h3>
              {f'<p><strong>What happened:</strong> {what}</p>' if what else ''}
              {f'<p><strong>Why it matters:</strong> {why}</p>' if why else ''}
              {facts_html}
              {meta_html}
            </div>
            """
        )
    return "\n".join(cards)


def weather_cards(weather_by_location: list[dict]) -> str:
    cards = []
    for weather in weather_by_location:
        cards.append(
            f"""
            <div class="weather-card">
              <h3>{html.escape(weather['name'])}</h3>
              <div class="condition">{html.escape(weather['condition'])}</div>
              <div class="temp">{weather['min_temp']}–{weather['max_temp']}°C</div>
              <div class="weather-details">
                <span>🌧️ {weather['rain_probability']}%</span>
                <span>💨 {weather['wind_speed']} km/h</span>
                <span>☀️ UV {weather['uv_index']}</span>
              </div>
              <p>{html.escape(weather['advice'])}</p>
            </div>
            """
        )
    return "\n".join(cards)


def build_briefing_html(
    summaries: dict[str, list[dict]],
    weather_by_location: list[dict],
    date_text: str,
    coverage_date_text: str,
) -> str:
    template = Path("templates/briefing.html").read_text(encoding="utf-8")
    replacements = {
        "{{USER_NAME}}": html.escape(config.USER_NAME),
        "{{DATE}}": html.escape(date_text),
        "{{COVERAGE_DATE}}": html.escape(coverage_date_text),
        "{{WEATHER_CARDS}}": weather_cards(weather_by_location),
        "{{WORLD_NEWS}}": render_ai_cards(summaries["world"]),
        "{{INDIA_NEWS}}": render_ai_cards(summaries["india"]),
        "{{AP_NEWS}}": render_ai_cards(summaries["andhra_pradesh"]),
        "{{TECH_NEWS}}": render_ai_cards(summaries["tech"]),
        "{{RESEARCH_NEWS}}": render_ai_cards(summaries["research"]),
        "{{HN_NEWS}}": render_ai_cards(summaries["hacker_news"]),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def main() -> None:
    now = datetime.now(ZoneInfo(config.TIMEZONE))
    yesterday = now - timedelta(days=1)

    date_text = now.strftime("%d %B %Y")
    coverage_date_text = yesterday.strftime("%d %B %Y")

    limits = {
        "world": config.MAX_WORLD,
        "india": config.MAX_INDIA,
        "andhra_pradesh": config.MAX_AP,
        "tech": config.MAX_TECH,
        "research": config.MAX_RESEARCH,
        "hacker_news": config.MAX_HN,
    }

    print("Collecting news feeds and articles...")
    raw_news = get_all_news(limits)

    print("Synthesizing AI research summaries with Groq...")
    summaries = {
        "world": summarize_section_with_groq("World News", raw_news["world"]),
        "india": summarize_section_with_groq("India News", raw_news["india"]),
        "andhra_pradesh": summarize_section_with_groq("Andhra Pradesh News", raw_news["andhra_pradesh"]),
        "tech": summarize_section_with_groq("Technology & AI", raw_news["tech"]),
        "research": summarize_section_with_groq("Research & Papers", raw_news["research"]),
        "hacker_news": summarize_section_with_groq("Hacker News", raw_news["hacker_news"]),
    }

    print("Fetching weather forecasts for 4 locations...")
    weather_by_location = []
    for location in config.LOCATIONS:
        result = get_weather(location["latitude"], location["longitude"], config.TIMEZONE)
        result["name"] = location["name"]
        weather_by_location.append(result)

    briefing_html = build_briefing_html(
        summaries, weather_by_location, date_text, coverage_date_text
    )

    # Ensure output directory exists and write briefing.html artifact
    output_file = Path(config.OUTPUT_PATH)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(briefing_html, encoding="utf-8")
    print(f"Briefing HTML generated successfully at {output_file}")

    # Conditionally send email if credentials are present
    if config.EMAIL_ADDRESS and config.EMAIL_APP_PASSWORD:
        subject = f"Morning Briefing — {now.strftime('%d %b %Y')}"
        send_email(
            config.EMAIL_ADDRESS,
            config.EMAIL_APP_PASSWORD,
            config.RECIPIENT_EMAIL,
            subject,
            briefing_html,
        )
        print("Morning briefing email sent successfully.")
    else:
        print("Skipping email delivery (no EMAIL_APP_PASSWORD configured). Output saved to artifact.")


if __name__ == "__main__":
    main()
