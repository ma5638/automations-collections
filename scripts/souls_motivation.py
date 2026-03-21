import os
import requests
import anthropic
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

CHARACTERS = [
    "a world-weary knight who has died a thousand times but rises still",
    "a blind seer who speaks in riddles at the edge of a dying flame",
    "a fading lord who once held great power but chose to walk among the unkindled",
    "a blacksmith who has forged weapons for heroes long since turned to ash",
    "a wandering warrior with no memory of their past, only the path ahead",
]


def get_motivation():
    import random
    character = random.choice(CHARACTERS)

    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"You are {character} in a dark, souls-like world. "
                f"Speak a single motivational line (1-2 sentences maximum) to a fellow Undead "
                f"who is about to face an impossible challenge. "
                f"Your tone is cryptic, poetic, and melancholic — yet deeply encouraging. "
                f"Draw on themes of perseverance, flame, ash, cycles, and the will to endure. "
                f"Do not break character. Do not use modern language. Speak only as this character would."
            ),
        }],
    )

    text = next((b.text for b in response.content if b.type == "text"), "")
    return text, character


def build_payload(message, character):
    return {
        "username": "The Bonfire Keeper",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/3522/3522681.png",
        "embeds": [{
            "description": f"*{message}*",
            "color": 0xB34700,
            "footer": {
                "text": f"— {character.capitalize()} • automations-collections"
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


def main():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL is not set")
    if not os.environ.get("CLAUDE_API_KEY"):
        raise ValueError("CLAUDE_API_KEY is not set")

    print("Summoning wisdom from the dark...")
    message, character = get_motivation()
    print(f"Character: {character}")
    print(f"Message: {message}")

    payload = build_payload(message, character)
    resp = requests.post(webhook_url, json=payload)
    resp.raise_for_status()
    print(f"Motivation sent — HTTP {resp.status_code}")


if __name__ == "__main__":
    main()
