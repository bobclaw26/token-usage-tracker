# Token Usage Tracker

Monitor AI model token usage and costs across OpenClaw sessions to prevent overspending.

## Configuration

### Model Pricing (`references/model_prices.json`)

Currently configured:

- **Haiku (Primary)**: $0.0008/1k input, $0.0024/1k output
- **Codex (Fallback)**: $0.0005/1k input, $0.0015/1k output

### Tracking Limits (`references/tracking_config.json`)

- **Daily Limit**: $5.00
- **Weekly Limit**: $30.00
- **Monthly Limit**: $100.00
- **Alerts**: Telegram notifications at 75% and 95% of daily limit

## Usage

### Run Dashboard

```bash
python scripts/monitor_token_usage.py
```

Generates:
- Real-time usage dashboard
- Cost breakdown by model
- Daily/weekly/monthly tracking
- Alert status
- Spending recommendations

### Run Basic Report

```bash
python scripts/track_token_usage.py
```

Simple token count and cost estimate.

## Scheduled Monitoring

Set up cron job to run dashboard every 6 hours:

```bash
# Via OpenClaw cron
openclaw cron add \
  --name "token-usage-check" \
  --schedule "0 */6 * * *" \
  --task "python ~/.openclaw/skills/public/token-usage-tracker/scripts/monitor_token_usage.py"
```

## Alerts

Alerts are sent to Telegram when:
- Daily cost reaches 75% of limit → **WARNING**
- Daily cost reaches 95% of limit → **CRITICAL**
- Model-specific limits exceeded
- Unusual spending patterns detected

Target: `7642182046`

## Files

- `SKILL.md` — Technical documentation
- `references/model_prices.json` — Current pricing
- `references/tracking_config.json` — Cost limits & alert settings
- `references/token_usage_report.txt` — Latest report
- `references/dashboard.txt` — Current dashboard
- `references/usage_history.jsonl` — Historical tracking data
- `scripts/track_token_usage.py` — Basic tracker
- `scripts/monitor_token_usage.py` — Advanced dashboard & alerts

## Model Strategy

✅ **Use Haiku by default** — Fast, cheap, sufficient for most tasks  
⚠️ **Use Codex sparingly** — Only for complex reasoning tasks  
❌ **Avoid Sonnet** — Too expensive for routine work

---

**Current Status**: Configured, tracking enabled, alerts active.
