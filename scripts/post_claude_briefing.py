import os
import sys
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK_URL_ENV = "DISCORD_WEBHOOK_URL"
BRIEFING_FILE = "briefing_output.md"

MAX_EMBED_LEN = 4096
MAX_MESSAGES = 4


def split_into_chunks(text, max_len=MAX_EMBED_LEN, max_chunks=MAX_MESSAGES):
    """Split text on paragraph boundaries, respecting max_len per chunk."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = []

    for para in paragraphs:
        candidate = "\n\n".join(current + [para])
        if len(candidate) > max_len and current:
            chunks.append("\n\n".join(current))
            current = [para]
        else:
            current.append(para)

        if len(chunks) == max_chunks - 1:
            # Last allowed chunk — dump everything remaining into it
            break

    if current:
        chunks.append("\n\n".join(current))

    return chunks[:max_chunks]


def build_payload(chunk, part, total):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    title = f"🤖 Claude AI Threat Briefing — {today}"
    if total > 1:
        title += f" ({part}/{total})"

    return {
        "username": "CyberWatch",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2092/2092757.png",
        "embeds": [
            {
                "title": title,
                "description": chunk,
                "color": 0xEB459E,
                "footer": {
                    "text": "Powered by Claude Haiku 4.5 (Claude Code) • automations-collections"
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }


def main():
    webhook_url = os.environ.get(DISCORD_WEBHOOK_URL_ENV)
    if not webhook_url:
        raise ValueError(f"{DISCORD_WEBHOOK_URL_ENV} is not set")

    if not os.path.exists(BRIEFING_FILE):
        print(f"[error] {BRIEFING_FILE} was not written — Claude may have failed", file=sys.stderr)
        sys.exit(1)

    with open(BRIEFING_FILE) as f:
        briefing = f.read().strip()

    if not briefing:
        print(f"[error] {BRIEFING_FILE} is empty", file=sys.stderr)
        sys.exit(1)

    chunks = split_into_chunks(briefing)
    total = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        payload = build_payload(chunk, part=i, total=total)
        resp = requests.post(webhook_url, json=payload)
        resp.raise_for_status()
        print(f"Claude briefing sent — part {i}/{total} — HTTP {resp.status_code}")


if __name__ == "__main__":
    main()
