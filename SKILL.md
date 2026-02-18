---
name: token-usage-tracker
description: Track and analyze AI model token usage across different providers. Monitors input and output tokens, calculates cost estimates, and provides insights into AI model consumption for OpenClaw sessions.
---

# Token Usage Tracker

## Overview

Track token usage and cost estimates for AI models used in OpenClaw sessions.

## Features

- Track tokens for Anthropic and OpenAI models
- Calculate cost based on model-specific pricing
- Persistent logging of token usage
- Generate usage reports

## Configuration

Create `references/model_prices.json`:

```json
{
  "anthropic/claude-3-5-haiku-20241022": {
    "input_price_per_1k_tokens": 0.25,
    "output_price_per_1k_tokens": 1.25
  },
  "anthropic/claude-sonnet-4-20250514": {
    "input_price_per_1k_tokens": 0.50,
    "output_price_per_1k_tokens": 2.50
  },
  "openai/gpt-5.1-codex": {
    "input_price_per_1k_tokens": 0.03,
    "output_price_per_1k_tokens": 0.06
  }
}
```

## Usage

Run tracking script:

```bash
python track_token_usage.py
```

Schedule periodic tracking with OpenClaw cron:

```bash
openclaw cron add --name "token-usage-check" \
  --schedule "0 */4 * * *" \
  --payload "python /path/to/track_token_usage.py"
```

## Troubleshooting

- Ensure accurate model pricing configuration
- Check filesystem permissions
- Verify OpenClaw session logging is enabled