# Update Cost Limits

When you hit the 95% daily cost threshold, I'll ask: **"Would you like to raise the daily limit?"**

## Quick Response Guide

### Set to a specific amount
```
15        → Daily limit becomes $15
20        → Daily limit becomes $20
```

### Increase by an amount
```
+5        → Increase by $5 (e.g., $10 → $15)
+10       → Increase by $10
```

### Keep current
```
keep      → No change
no        → No change
```

### Disable critical alerts
```
disable   → Turn off 95% alert (warning still active at 75%)
```

---

## Manual Update (Direct Command)

If you want to update limits without waiting for an alert:

```bash
python ~/.openclaw/skills/public/token-usage-tracker/scripts/handle_limit_response.py "15"
python ~/.openclaw/skills/public/token-usage-tracker/scripts/handle_limit_response.py "+5"
python ~/.openclaw/skills/public/token-usage-tracker/scripts/handle_limit_response.py "keep"
```

## What Gets Updated

When you change the daily limit, weekly and monthly limits scale proportionally:

**Example: Change from $10/day to $15/day**

| Period | Before | After |
|--------|--------|-------|
| Daily | $10.00 | $15.00 |
| Weekly | $60.00 | $90.00 |
| Monthly | $200.00 | $300.00 |

## Warnings vs Critical

- **⚠ WARNING**: At 75% of daily limit
- **⛔ CRITICAL**: At 95% of daily limit (asks to raise)

You can disable critical alerts with `disable` but warnings stay active.

---

**Respond quickly to alerts. Keep your budgets flexible. 💰**
