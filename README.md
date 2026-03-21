# automations-collections

Personal automation hub. GitHub Actions that run on a schedule and push results to Discord.

---

## Automations

### 🔐 Daily Cybersecurity Digest
Runs every day at 12:00 UTC and posts the latest headlines from 5 security sources to a Discord channel.

**Sources:** The Hacker News · BleepingComputer · Krebs on Security · Dark Reading · SANS ISC

---

## Setup

### 1. Create a Discord Webhook
1. Open Discord on desktop → go to your target channel
2. **Edit Channel** → **Integrations** → **Webhooks** → **New Webhook**
3. Name it (e.g. `CyberWatch`), copy the webhook URL

### 2. Add GitHub Secret
1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `DISCORD_WEBHOOK_URL`
4. Value: paste your webhook URL

### 3. Enable Actions
GitHub Actions will run automatically once the secret is set.
You can also trigger a test run manually: **Actions** tab → **Daily Cybersecurity Digest** → **Run workflow**.
