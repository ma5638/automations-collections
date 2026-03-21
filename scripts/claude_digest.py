import os
import requests
import anthropic
from datetime import datetime, timezone


def get_claude_briefing():
    """Ask Claude to search the web for today's top cybersecurity news."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    messages = [{
        "role": "user",
        "content": (
            f"Today is {today}. Search the web for the top cybersecurity news and threats "
            f"from the last 24 hours. Find 5-7 significant stories covering major vulnerabilities, "
            f"breaches, ransomware, malware campaigns, nation-state activity, or security advisories. "
            f"For each story write a 1-2 sentence summary explaining what happened and why it matters, "
            f"and include the source URL. Present as a clean numbered list."
        ),
    }]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]

    all_text = []
    for _ in range(5):  # handle pause_turn continuations
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

        for block in response.content:
            if block.type == "text":
                all_text.append(block.text)

        if response.stop_reason in ("end_turn", "max_tokens"):
            break

        # pause_turn: server-side tool loop hit its limit — append and retry
        messages.append({"role": "assistant", "content": response.content})

    return "\n\n".join(all_text) if all_text else "No briefing available."


def build_payload(briefing_text):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    if len(briefing_text) > 4096:
        briefing_text = briefing_text[:4090] + "..."

    return {
        "username": "CyberWatch",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2092/2092757.png",
        "embeds": [{
            "title": f"🤖 Claude AI Threat Briefing — {today}",
            "description": briefing_text,
            "color": 0xEB459E,
            "footer": {"text": "Powered by Claude Opus 4.6 • automations-collections"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }


def main():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL is not set")
    if not os.environ.get("CLAUDE_API_KEY"):
        raise ValueError("CLAUDE_API_KEY is not set")

    print("Asking Claude to search for today's cybersecurity news...")
    briefing = get_claude_briefing()

    payload = build_payload(briefing)
    resp = requests.post(webhook_url, json=payload)
    resp.raise_for_status()
    print(f"Claude briefing sent — HTTP {resp.status_code}")


if __name__ == "__main__":
    main()
