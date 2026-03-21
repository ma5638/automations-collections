import os
import json
import feedparser
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

FEEDS = {
    "The Hacker News":  "https://feeds.feedburner.com/TheHackersNews",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "Dark Reading":     "https://www.darkreading.com/rss.xml",
    "SANS ISC":         "https://isc.sans.edu/rssfeed.xml",
}

MAX_PER_FEED = 3


def fetch_feed(name, url):
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:MAX_PER_FEED]:
            items.append({
                "title": entry.get("title", "No title").strip(),
                "link":  entry.get("link", ""),
            })
        return items
    except Exception as e:
        print(f"[warn] Could not fetch {name}: {e}")
        return []


def build_payload(articles_by_source):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    fields = []

    for source, articles in articles_by_source.items():
        if not articles:
            continue
        value = "\n".join(f"[{a['title']}]({a['link']})" for a in articles)
        fields.append({
            "name": f"📰 {source}",
            "value": value[:1024],
            "inline": False,
        })

    return {
        "username": "CyberWatch",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2092/2092757.png",
        "embeds": [{
            "title": f"🔐 Daily Cybersecurity Digest — {today}",
            "color": 0x5865F2,
            "fields": fields,
            "footer": {"text": "automations-collections • GitHub Actions"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


def main():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL is not set")

    articles_by_source = {name: fetch_feed(name, url) for name, url in FEEDS.items()}
    payload = build_payload(articles_by_source)

    resp = requests.post(webhook_url, json=payload)
    resp.raise_for_status()
    print(f"Digest sent — HTTP {resp.status_code}")


if __name__ == "__main__":
    main()
