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
            "Google News – Tech & Software",
            "https://news.google.com/rss/search?q="
            + quote_plus(
                "(artificial intelligence OR cybersecurity OR software OR cloud "
                "OR developer tools OR open source OR startup funding) when:1d"
            )
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

TRUSTED_SOURCES = {
    "Reuters",
    "Associated Press",
    "AP",
    "BBC",
    "BBC World",
    "The Hindu",
    "The Indian Express",
    "NDTV",
    "PIB",
    "News On AIR",
    "OpenAI",
    "Google",
    "Microsoft",
    "NVIDIA",
    "The Verge",
    "TechCrunch",
    "Ars Technica",
    "Wired",
    "Hacker News",
    "arXiv",
    "Navbharat Times",
    "The Times of India",
    "Times of India",
    "Hindustan Times",
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
                500,
            )
            if summary.lower() == title.lower():
                summary = ""

            # Attempt fetching article body content if summary is short
            if len(summary) < 100 and link and not link.startswith("https://news.google.com/rss/articles/"):
                extracted = extract_article_content(link, max_chars=800)
                if extracted:
                    summary = clean_text(extracted, 500)

            # Filter out heavy non-ASCII / non-English content
            ascii_letters = sum(ch.isascii() and ch.isalpha() for ch in title)
            all_letters = sum(ch.isalpha() for ch in title)
            if all_letters and ascii_letters / all_letters < 0.72:
                continue

            low_title = title.lower()

            # Tech section filtering: Exclude generic car reviews & speculative rumor leaks
            if category == "tech":
                if any(k in low_title for k in ("car review", "hot hatch", "leaks reveal", "release date, price", "price changes")):
                    continue

            # India section filtering: Exclude pure international stories & PIB greetings
            if category == "india":
                if source == "PIB" and any(k in low_title for k in ("congratulates", "congratulated", "greets", "wishes")):
                    continue
                # If headline is purely about US/Trump/Iran/Gaza without any India context
                if any(k in low_title for k in ("trump cancels", "iran strikes", "ceuta", "idaho shooting")) and "india" not in low_title:
                    continue

            candidates.append(
                {
                    "title": title,
                    "summary": summary if summary else title,
                    "url": link,
                    "source": source,
                    "published": published,
                    "is_trusted": any(t.lower() in source.lower() for t in TRUSTED_SOURCES),
                }
            )

            if len(candidates) >= limit * 2:
                break

    # Sort candidates so trusted sources come first, keeping original order within each group
    candidates.sort(key=lambda x: 0 if x["is_trusted"] else 1)
    return candidates[:limit]


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
