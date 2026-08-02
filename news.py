from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

FEEDS = {
    "world": [
        (
            "Google News – World",
            "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-IN&gl=IN&ceid=IN:en",
        ),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ],
    "india": [
        (
            "Google News – India",
            "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
        ),
        ("PIB", "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"),
    ],
    "andhra_pradesh": [
        (
            "Google News – Andhra Pradesh",
            "https://news.google.com/rss/search?q="
            + quote_plus("Andhra Pradesh OR Rajahmundry OR Kakinada when:1d")
            + "&hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ],
    "tech": [
        (
            "Google News – Technology",
            "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en",
        ),
        (
            "Google News – AI & Cybersecurity",
            "https://news.google.com/rss/search?q="
            + quote_plus("(artificial intelligence OR cybersecurity OR software OR startups) when:1d")
            + "&hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ],
    "research": [
        ("arXiv AI Research", "http://export.arxiv.org/rss/cs.AI"),
        (
            "Google News – Research & Papers",
            "https://news.google.com/rss/search?q="
            + quote_plus("(AI research OR paper OR Google Research OR OpenAI) when:1d")
            + "&hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ],
}


def clean_text(value: str, limit: int = 400) -> str:
    text = BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0] + "…"
    return text


def extract_article_content(url: str, max_chars: int = 1200) -> str:
    """Fetch freely accessible article URL and extract main paragraph text."""
    if not url or "news.google.com" in url or "arxiv.org" in url:
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        # Strip script, style, nav, footer, header
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
        text = " ".join(paragraphs)
        return text[:max_chars] if text else ""
    except Exception:
        return ""


def published_datetime(entry) -> datetime:
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            pass
    return datetime.now(timezone.utc)


def normalized_title(title: str) -> str:
    title = re.sub(r"\s+-\s+[^-]{2,50}$", "", title)
    title = re.sub(r"[^a-z0-9 ]", "", title.lower())
    stop = {"the", "a", "an", "of", "to", "in", "for", "on", "and", "with", "from"}
    return " ".join(word for word in title.split() if word not in stop)


def is_duplicate(title: str, existing: list[dict]) -> bool:
    current = set(normalized_title(title).split())
    if not current:
        return True
    for article in existing:
        previous = set(normalized_title(article["title"]).split())
        overlap = len(current & previous) / max(1, min(len(current), len(previous)))
        if overlap >= 0.72:
            return True
    return False


def collect_category(category: str, limit: int) -> list[dict]:
    india_timezone = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(india_timezone)

    yesterday_start_ist = (now_ist - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    cutoff = yesterday_start_ist.astimezone(timezone.utc)
    current_time_utc = now_ist.astimezone(timezone.utc)
    candidates: list[dict] = []

    for fallback_source, url in FEEDS[category]:
        parsed = feedparser.parse(url, request_headers=HEADERS)
        for entry in parsed.entries:
            published = published_datetime(entry)
            if published < cutoff or published > current_time_utc:
                continue

            title = clean_text(entry.get("title", ""), 180)
            if not title or is_duplicate(title, candidates):
                continue

            source = fallback_source
            if isinstance(entry.get("source"), dict):
                source = entry.source.get("title") or fallback_source

            link = entry.get("link") or ""
            summary = clean_text(
                entry.get("summary") or entry.get("description") or "",
                400,
            )

            if "Google News" in fallback_source:
                summary = ""
            if summary.lower() == title.lower():
                summary = ""

            # Filter out heavy non-ASCII / non-English content
            ascii_letters = sum(ch.isascii() and ch.isalpha() for ch in title)
            all_letters = sum(ch.isalpha() for ch in title)
            if all_letters and ascii_letters / all_letters < 0.72:
                continue

            low_title = title.lower()
            if category == "india" and source == "PIB" and any(
                phrase in low_title
                for phrase in ("congratulates", "congratulated", "greets", "wishes")
            ):
                continue

            candidates.append(
                {
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "source": source,
                    "published": published,
                }
            )

            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break

    return candidates


def collect_hacker_news(limit: int = 4) -> list[dict]:
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=15,
            headers=HEADERS,
        ).json()[:30]

        stories = []
        for story_id in ids:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                timeout=10,
                headers=HEADERS,
            ).json()
            if not item or item.get("type") != "story" or not item.get("title"):
                continue
            stories.append(
                {
                    "title": clean_text(item["title"], 180),
                    "summary": f'{item.get("score", 0)} points · {item.get("descendants", 0)} comments',
                    "url": item.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                    "source": "Hacker News",
                    "published": datetime.fromtimestamp(item.get("time", 0), timezone.utc),
                }
            )
            if len(stories) >= limit:
                break
        return stories
    except (requests.RequestException, ValueError, TypeError):
        return []


def get_all_news(limits: dict[str, int]) -> dict[str, list[dict]]:
    return {
        "world": collect_category("world", limits["world"]),
        "india": collect_category("india", limits["india"]),
        "andhra_pradesh": collect_category("andhra_pradesh", limits["andhra_pradesh"]),
        "tech": collect_category("tech", limits["tech"]),
        "research": collect_category("research", limits.get("research", 4)),
        "hacker_news": collect_hacker_news(limits["hacker_news"]),
    }
