from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import config
from email_sender import send_email
from news import get_all_news
from weather import get_weather


def article_cards(articles: list[dict]) -> str:
    if not articles:
        return '<div class="empty">No recent stories were available from the configured feeds.</div>'

    cards = []
    for article in articles:
        summary = (
            f'<p>{html.escape(article["summary"])}</p>'
            if article.get("summary")
            else ""
        )
        cards.append(
            f"""
            <div class="story">
              <a href="{html.escape(article['url'], quote=True)}">{html.escape(article['title'])}</a>
              {summary}
              <span>{html.escape(article['source'])}</span>
            </div>
            """
        )
    return "\n".join(cards)


def build_email(news: dict, weather: dict, date_text: str) -> str:
    template = Path("templates/briefing.html").read_text(encoding="utf-8")
    replacements = {
        "{{USER_NAME}}": html.escape(config.USER_NAME),
        "{{DATE}}": html.escape(date_text),
        "{{CITY}}": html.escape(config.CITY_NAME),
        "{{CONDITION}}": html.escape(weather["condition"]),
        "{{MAX_TEMP}}": str(weather["max_temp"]),
        "{{MIN_TEMP}}": str(weather["min_temp"]),
        "{{RAIN}}": str(weather["rain_probability"]),
        "{{WIND}}": str(weather["wind_speed"]),
        "{{UV}}": str(weather["uv_index"]),
        "{{SUNRISE}}": weather["sunrise"],
        "{{SUNSET}}": weather["sunset"],
        "{{ADVICE}}": html.escape(weather["advice"]),
        "{{WORLD_NEWS}}": article_cards(news["world"]),
        "{{INDIA_NEWS}}": article_cards(news["india"]),
        "{{AP_NEWS}}": article_cards(news["andhra_pradesh"]),
        "{{TECH_NEWS}}": article_cards(news["tech"]),
        "{{HN_NEWS}}": article_cards(news["hacker_news"]),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def main() -> None:
    now = datetime.now(ZoneInfo(config.TIMEZONE))
    limits = {
        "world": config.MAX_WORLD,
        "india": config.MAX_INDIA,
        "andhra_pradesh": config.MAX_AP,
        "tech": config.MAX_TECH,
        "hacker_news": config.MAX_HN,
    }

    news = get_all_news(limits)
    weather = get_weather(config.LATITUDE, config.LONGITUDE, config.TIMEZONE)
    date_text = now.strftime("%A, %d %B %Y")
    email_html = build_email(news, weather, date_text)

    subject = f"Morning Briefing — {now.strftime('%d %b %Y')}"
    send_email(
        config.EMAIL_ADDRESS,
        config.EMAIL_APP_PASSWORD,
        config.RECIPIENT_EMAIL,
        subject,
        email_html,
    )
    print("Morning briefing sent successfully.")


if __name__ == "__main__":
    main()
