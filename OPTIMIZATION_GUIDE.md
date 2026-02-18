# Token Usage Optimization Guide

## Manual Optimization

Run anytime to clear caches and prune context:

```bash
python ~/.openclaw/skills/public/token-usage-tracker/scripts/optimize_token_usage.py
```

**What it does:**
- Clears session logs >30 days old
- Keeps only 10 most recent sessions
- Prunes context to last 50 messages per session
- Removes audit logs >7 days old
- Consolidates old memory files
- Updates cache configuration

**Impact (first run):**
- ~0.18 MB freed
- ~46,000 tokens saved
- ~$0.04 saved

## Automated Optimization

**Weekly Schedule:** Every Sunday at 00:05 UTC

The optimization runs automatically via cron:
- Saves space and tokens
- Reduces context bloat
- Keeps only relevant recent data

## Dashboard Alerts

### Every $5 Milestone
```
💰 Milestone: $5.00 spent ($4.87 total today)
💰 Milestone: $10.00 spent ($10.12 total today)
```

### Cost Warnings
```
⚠ WARNING: Daily cost at 75.2% of limit ($3.76 / $5.00)
⛔ CRITICAL: Daily cost limit at 95.0% ($4.75 / $5.00)
```

## Cost Management Tips

1. **Use Haiku by default** — Fast, cheap, enough for most work
2. **Monitor the dashboard** — Run every 6 hours automatically
3. **Check milestones** — Get alerts at every $5 spent
4. **Optimize weekly** — Automatic cleanup every Sunday
5. **Manual optimization** — Before long sessions to free cache

## Alert Configuration

Located in: `~/.openclaw/skills/public/token-usage-tracker/references/tracking_config.json`

```json
{
  "thresholds": {
    "daily_cost_limit": 5.00,
    "alert_every_dollars": 5.00,
    "alert_level_warning": 0.75,
    "alert_level_critical": 0.95
  }
}
```

Modify values as needed. Changes take effect on next monitor run.

## History Tracking

Cost milestones are tracked in:
- `references/last_alert_cost.json` — Last $5 milestone
- `references/usage_history.jsonl` — Full history
- `references/token_usage_report.txt` — Latest snapshot

## Troubleshooting

**Dashboard shows no data?**
- Wait for first token usage (next cron cycle)
- Manually run: `python ~/.openclaw/skills/public/token-usage-tracker/scripts/track_token_usage.py`

**Alerts not sending?**
- Check Telegram target in config: `"telegram_target": "7642182046"`
- Verify OpenClaw message tool is working: `openclaw status`

**Want to adjust limits?**
- Edit `tracking_config.json`
- Change `alert_every_dollars`, `daily_cost_limit`, etc.
- Changes apply immediately

---

**Keep your tokens lean. Spend wisely. 💰**
