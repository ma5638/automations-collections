import os
import requests
import anthropic
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


def get_claude_briefing():
    """Ask Claude to search the web for today's top cybersecurity news."""
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    messages = [
        {
            "role": "user",
            "content": (
                f"Today is {today}. Search the web for today's top cybersecurity threats and risks "
                f"from the last 24 hours. Find exactly 5 items total: 1-2 must be specific vulnerabilities "
                f"(CVEs, patches, exploits), and the remaining 3-4 must be broader risks or threats "
                f"(breaches, ransomware, malware campaigns, nation-state activity, advisories). "
                f"For each item write a 1-2 sentence summary explaining what happened and why it matters, "
                f"and include the source URL. Present as a clean numbered list."
            ),
        }
    ]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]

    all_text = []
    search_queries = []
    for _ in range(5):  # handle pause_turn continuations
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

        print(f"[debug] stop_reason: {response.stop_reason}")
        print(f"[debug] response.content: {len(response.content)}")

        for block in response.content:
            if block.type == "text":
                all_text.append(block.text)
            elif block.type == "server_tool_use" and block.name == "web_search":
                query = block.input.get("query", "")
                if query:
                    search_queries.append(query)

        if response.stop_reason in ("end_turn", "max_tokens"):
            break

        # pause_turn: server-side tool loop hit its limit — append and retry
        messages.append({"role": "assistant", "content": response.content})

    briefing = "\n\n".join(all_text) if all_text else "No briefing available."
    if search_queries:
        briefing += "\n\n🔍 **Searches:** " + " · ".join(f"`{q}`" for q in search_queries)
    return briefing


def build_payload(briefing_text):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    if len(briefing_text) > 4096:
        briefing_text = briefing_text[:4090] + "..."

    return {
        "username": "CyberWatch",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2092/2092757.png",
        "embeds": [
            {
                "title": f"🤖 Claude AI Threat Briefing — {today}",
                "description": briefing_text,
                "color": 0xEB459E,
                "footer": {
                    "text": "Powered by Claude Opus 4.6 • automations-collections"
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
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
