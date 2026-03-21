import os
import sys
import requests
import anthropic
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def fetch_article_requests(url):
    from urllib.parse import urlparse
    session = requests.Session()
    origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    session.get(origin, headers={**HEADERS, "Referer": "https://www.google.com/"}, timeout=15)
    resp = session.get(url, headers={**HEADERS, "Referer": origin + "/"}, timeout=15)
    resp.raise_for_status()
    return resp.text


def fetch_article_playwright(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        html = page.content()
        browser.close()
    return html


def fetch_article(url):
    try:
        html = fetch_article_requests(url)
        print("[fetch] requests succeeded")
    except Exception as e:
        print(f"[fetch] requests failed ({e}), falling back to Playwright...")
        html = fetch_article_playwright(url)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)[:12000]


def summarize(url, article_text):
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"Summarize the following article from {url}.\n\n"
                f"Provide:\n"
                f"1. A one-sentence TL;DR\n"
                f"2. 3-5 key points as bullet points\n"
                f"3. Why it matters (1-2 sentences)\n\n"
                f"Article content:\n{article_text}"
            ),
        }],
    )

    text_blocks = [b.text for b in response.content if b.type == "text"]
    return "\n\n".join(text_blocks) if text_blocks else "No summary available."


def main():
    if len(sys.argv) < 2:
        print("Usage: python summarize_url.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"Fetching: {url}\n")

    article_text = fetch_article(url)
    print("Summarizing with Claude...\n")

    summary = summarize(url, article_text)
    print(summary)


if __name__ == "__main__":
    main()
