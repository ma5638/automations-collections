import os
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
FETCH_POOL = 15
STATE_NAMESPACE = "automations-collections/seen-articles"
MAX_SEEN = 200


def web_api_headers():
    return {"Authorization": f"Bearer {os.environ['WEB_API_KEY']}"}


def load_seen():
    base_url = os.environ["WEB_API_URL"]
    resp = requests.get(f"{base_url}/state/{STATE_NAMESPACE}", headers=web_api_headers())
    resp.raise_for_status()
    return resp.json().get("value") or []


def save_seen(new_links):
    if not new_links:
        return
    base_url = os.environ["WEB_API_URL"]
    resp = requests.post(
        f"{base_url}/state/{STATE_NAMESPACE}/append",
        headers=web_api_headers(),
        json={"items": new_links, "max_items": MAX_SEEN},
    )
    resp.raise_for_status()


def fetch_feed(name, url, seen_set):
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[warn] Could not fetch {name}: {e}")
        return None

    items = []
    for entry in feed.entries[:FETCH_POOL]:
        link = entry.get("link", "")
        if link in seen_set:
            continue
        items.append({
            "title": entry.get("title", "No title").strip(),
            "link": link,
        })
        if len(items) >= MAX_PER_FEED:
            break
    return items


def build_payload(articles_by_source):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    fields = []

    for source, articles in articles_by_source.items():
        if articles is None:
            continue
        if articles:
            value = "\n".join(f"[{a['title']}]({a['link']})" for a in articles)
        else:
            value = "No new items since last digest."
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

    seen = load_seen()
    seen_set = set(seen)

    articles_by_source = {name: fetch_feed(name, url, seen_set) for name, url in FEEDS.items()}
    payload = build_payload(articles_by_source)

    resp = requests.post(webhook_url, json=payload)
    resp.raise_for_status()
    print(f"Digest sent — HTTP {resp.status_code}")

    posted_links = [
        a["link"]
        for articles in articles_by_source.values()
        if articles
        for a in articles
        if a["link"]
    ]
    save_seen(posted_links)


if __name__ == "__main__":
    main()
