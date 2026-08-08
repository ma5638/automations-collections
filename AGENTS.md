# AGENTS.md — automations-collections

Scheduled GitHub Actions that post cybersecurity news to Discord. See `README.md` for the user-facing setup guide; this file covers agent-relevant workflow internals and the pending migration to shared server-side state.

## Workflows

| Workflow | File | Schedule | What it does |
|---|---|---|---|
| Daily Cybersecurity Digest | `.github/workflows/cybersec-digest.yml` | `0 6 * * *` (06:00 UTC daily) | `scripts/cybersec_digest.py` fetches 5 RSS feeds (Hacker News, BleepingComputer, Krebs, Dark Reading, SANS ISC), dedupes against previously-posted items, posts new ones to Discord via `DISCORD_WEBHOOK_URL` |
| Weekly Claude AI Threat Briefing | `.github/workflows/claude-briefing.yml` | `30 6 * * 1` (Monday 06:30 UTC) | Uses `anthropics/claude-code-action` (subscription OAuth via `CLAUDE_CODE_OAUTH_TOKEN`, NOT a raw API key — see "Why Claude Code Action" below) with `WebSearch` to research the week's threats, writes `briefing_output.md`, then `scripts/post_claude_briefing.py` posts it to Discord |

Both actions are pinned to commit SHAs, not floating tags (`stefanzweifel/git-auto-commit-action@4a55954c...`, `anthropics/claude-code-action@6b082c41...`) — supply-chain safety. Update the SHA comment alongside the SHA when bumping versions.

## Current state storage (personal-generic-server)

Both workflows dedupe against state held by **`ma5638/personal-generic-server`**, a shared cross-project FastAPI service on Cloud Run + Firestore (see that repo's `AGENTS.md` for full deploy/ops details). It exposes:

```
GET    /state/{namespace}
PUT    /state/{namespace}
DELETE /state/{namespace}
POST   /state/{namespace}/append   # dedupe + trim to max_items, returns the new list
```

- `automations-collections/seen-articles` — last 200 posted article URLs (digest), read/written from `scripts/cybersec_digest.py`
- `automations-collections/claude-briefing-seen-links` — last 100 links Claude has already cited (`MAX_SEEN = 100` in `scripts/post_claude_briefing.py`), fetched in the "Load previously shared links" step of `claude-briefing.yml` and injected into the next week's prompt so it doesn't repeat sources

Two things wire each workflow step to the service:
- Repo variable `WEB_API_URL` — the Cloud Run base URL (non-secret, so it's a `vars.*` entry, not a secret)
- Repo secret `WEB_API_KEY` — same value as the `personal-generic-server-api-key` Secret Manager secret, sent as `Authorization: Bearer ${WEB_API_KEY}`

Neither workflow needs `contents: write` or `git-auto-commit-action` anymore — nothing is git-committed at runtime.

## Gotchas already hit in this repo

- **RSS feed staleness is real, not a bug**: Krebs/SANS ISC and similar sources sometimes carry as few as ~10 items spanning weeks — dedup will correctly show "no new items" on quiet days rather than reposting. Don't chase "freshness" the source itself doesn't have.
- **CRLF/LF is inconsistent across most files in this repo** (pre-existing, unrelated to any of this work). Don't touch/stage files outside your intended edit scope. If you do intentionally edit a drifted file, normalize just that file to LF to match how it's actually stored in git (`git show HEAD:<file> | file -` to check), not the other way around.
- **Claude Code Action, not a raw Anthropic API key**: Anthropic's Consumer Terms restrict OAuth tokens from Free/Pro/Max/Team/Enterprise subscriptions to "ordinary use of Claude Code and other native Anthropic applications" — a custom script calling the API directly with a subscription-derived token is out of ToS. `claude-code-action` with `claude_code_oauth_token` is the sanctioned path for subscription billing in a workflow; a Console API key would be the alternative if subscription billing weren't desired.
- **A workflow stuck "queued" with zero jobs**, with valid YAML and Actions enabled, was actually a missing `CLAUDE_CODE_OAUTH_TOKEN` repo secret — check secrets first, not YAML syntax, when a scheduled workflow silently never starts.
