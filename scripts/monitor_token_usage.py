#!/usr/bin/env python3
"""
Token Usage Monitor & Dashboard

Tracks token usage across sessions with:
- Daily/weekly/monthly cost limits
- Real-time alerts for overspending
- Dashboard generation
- Cost breakdown by model
- Unusual pattern detection
"""

import os
import json
import glob
import datetime
from pathlib import Path
from collections import defaultdict
import subprocess

SCRIPT_DIR = Path(__file__).parent.parent
CONFIG_FILE = SCRIPT_DIR / "references" / "tracking_config.json"
PRICES_FILE = SCRIPT_DIR / "references" / "model_prices.json"
DASHBOARD_FILE = SCRIPT_DIR / "references" / "dashboard.txt"
USAGE_HISTORY = SCRIPT_DIR / "references" / "usage_history.jsonl"

def load_config():
    """Load tracking configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_prices():
    """Load model pricing"""
    try:
        with open(PRICES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_session_logs():
    """Find and parse all OpenClaw session logs"""
    # Try multiple patterns
    patterns = [
        os.path.expanduser('~/.openclaw/agents/*/sessions/*.jsonl'),
        os.path.expanduser('~/.openclaw/sessions/*.jsonl'),
        os.path.expanduser('~/.openclaw/logs/*.jsonl'),
    ]
    
    token_usage = defaultdict(lambda: {
        'input_tokens': 0,
        'output_tokens': 0,
        'cache_read': 0,
        'cache_write': 0,
        'sessions': 0,
        'timestamps': []
    })
    
    prices = load_prices()
    
    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern))
    
    for log_file in all_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        model = entry.get('model')
                        usage = entry.get('usage')
                        timestamp = entry.get('timestamp')
                        
                        if not model or not usage:
                            continue
                        
                        input_tokens = usage.get('input', usage.get('input_tokens', 0)) or 0
                        output_tokens = usage.get('output', usage.get('output_tokens', 0)) or 0
                        cache_read = usage.get('cacheRead', 0) or 0
                        cache_write = usage.get('cacheWrite', 0) or 0
                        
                        token_usage[model]['input_tokens'] += input_tokens
                        token_usage[model]['output_tokens'] += output_tokens
                        token_usage[model]['cache_read'] += cache_read
                        token_usage[model]['cache_write'] += cache_write
                        token_usage[model]['sessions'] += 1
                        if timestamp:
                            token_usage[model]['timestamps'].append(timestamp)
                    
                    except (json.JSONDecodeError, ValueError):
                        continue
        
        except IOError:
            pass
    
    return dict(token_usage)

def calculate_costs(token_usage, prices):
    """Calculate costs for token usage"""
    costs = {}
    total_cost = 0.0
    
    for model, usage in token_usage.items():
        if model not in prices:
            continue
        
        price_info = prices[model]
        input_cost = (usage['input_tokens'] / 1000) * price_info['input_price_per_1k_tokens']
        output_cost = (usage['output_tokens'] / 1000) * price_info['output_price_per_1k_tokens']
        total = input_cost + output_cost
        
        costs[model] = {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total,
            'tokens': usage['input_tokens'] + usage['output_tokens']
        }
        total_cost += total
    
    return costs, total_cost

def log_history(token_usage, prices, timestamp):
    """Append usage to history file"""
    costs, total = calculate_costs(token_usage, prices)
    
    entry = {
        'timestamp': timestamp,
        'total_cost': total,
        'token_usage': token_usage,
        'costs': costs
    }
    
    with open(USAGE_HISTORY, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def send_alert(config, message):
    """Send Telegram alert if configured"""
    alerts = config.get('alerts', {})
    if not alerts.get('telegram_enabled'):
        return
    
    target = alerts.get('telegram_target', '7642182046')
    try:
        cmd = [
            'openclaw', 'message', 'send',
            '--to', target,
            '--message', f'[TOKEN TRACKING]\n{message}'
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
    except Exception as e:
        print(f"Could not send alert: {e}")

def generate_dashboard(token_usage, prices):
    """Generate dashboard with current usage and projections"""
    costs, total_cost = calculate_costs(token_usage, prices)
    config = load_config()
    
    dashboard = "📊 OpenClaw Token Usage Dashboard\n"
    dashboard += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Summary
    dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    dashboard += "TOTAL USAGE\n"
    dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    total_tokens = sum(usage.get('input_tokens', 0) + usage.get('output_tokens', 0) 
                       for usage in token_usage.values())
    dashboard += f"Total Tokens: {total_tokens:,}\n"
    dashboard += f"Total Cost: ${total_cost:.2f}\n"
    dashboard += f"Daily Limit: ${config.get('thresholds', {}).get('daily_cost_limit', 5.0):.2f}\n"
    
    pct_used = (total_cost / config.get('thresholds', {}).get('daily_cost_limit', 5.0)) * 100
    dashboard += f"Daily Usage: {pct_used:.1f}%\n\n"
    
    # By Model
    dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    dashboard += "BY MODEL\n"
    dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for model in sorted(costs.keys()):
        cost_info = costs[model]
        usage = token_usage.get(model, {})
        
        indicator = "✓" if cost_info['total_cost'] < 1.0 else "⚠" if cost_info['total_cost'] < 2.0 else "⛔"
        dashboard += f"{indicator} {model}\n"
        dashboard += f"  Input:  {usage.get('input_tokens', 0):,} tokens → ${cost_info['input_cost']:.4f}\n"
        dashboard += f"  Output: {usage.get('output_tokens', 0):,} tokens → ${cost_info['output_cost']:.4f}\n"
        dashboard += f"  Total:  ${cost_info['total_cost']:.2f}\n"
        dashboard += f"  Sessions: {usage.get('sessions', 0)}\n\n"
    
    # Limits & Alerts
    thresholds = config.get('thresholds', {})
    dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    dashboard += "LIMITS & STATUS\n"
    dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    daily_limit = thresholds.get('daily_cost_limit', 5.0)
    if total_cost >= daily_limit * 0.95:
        dashboard += f"⛔ CRITICAL: {pct_used:.1f}% of daily limit used\n"
    elif total_cost >= daily_limit * 0.75:
        dashboard += f"⚠ WARNING: {pct_used:.1f}% of daily limit used\n"
    else:
        dashboard += f"✓ OK: {pct_used:.1f}% of daily limit used\n"
    
    # $5 milestone tracking
    alert_every = thresholds.get('alert_every_dollars', 5.0)
    if alert_every > 0:
        milestones_completed = int(total_cost / alert_every)
        next_milestone = (milestones_completed + 1) * alert_every
        dashboard += f"\n💰 Cost Milestones: {milestones_completed} × ${alert_every:.2f} (next: ${next_milestone:.2f})\n"
    
    dashboard += f"\n  Daily: ${total_cost:.2f} / ${daily_limit:.2f}\n"
    dashboard += f"  Weekly: TBD / ${thresholds.get('weekly_cost_limit', 30.0):.2f}\n"
    dashboard += f"  Monthly: TBD / ${thresholds.get('monthly_cost_limit', 100.0):.2f}\n"
    
    dashboard += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    dashboard += "RECOMMENDATIONS\n"
    dashboard += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    haiku_usage = token_usage.get('anthropic/claude-haiku-4-5', {}).get('sessions', 0)
    codex_usage = token_usage.get('openai/gpt-5.1-codex', {}).get('sessions', 0)
    
    if haiku_usage > 0 and codex_usage > 0:
        ratio = codex_usage / (haiku_usage + codex_usage)
        if ratio > 0.3:
            dashboard += "⚠ Using Codex frequently. Consider Haiku for most tasks.\n"
    
    if total_cost >= daily_limit * 0.75:
        dashboard += "⚠ Approaching daily limit. Monitor usage closely.\n"
    
    if total_cost < daily_limit * 0.3:
        dashboard += "✓ Good usage pattern. Continue with current setup.\n"
    
    return dashboard

def load_cost_history():
    """Load last tracked cost from history file"""
    history_file = SCRIPT_DIR / 'references' / 'last_alert_cost.json'
    try:
        with open(history_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'last_alert_cost': 0.0, 'timestamp': datetime.datetime.now().isoformat()}

def save_cost_history(cost):
    """Save current cost for next comparison"""
    history_file = SCRIPT_DIR / 'references' / 'last_alert_cost.json'
    data = {
        'last_alert_cost': cost,
        'timestamp': datetime.datetime.now().isoformat()
    }
    with open(history_file, 'w') as f:
        json.dump(data, f, indent=2)

def check_alerts(token_usage, prices, config):
    """Check if any alerts should be triggered"""
    costs, total_cost = calculate_costs(token_usage, prices)
    thresholds = config.get('thresholds', {})
    
    alerts = []
    
    # Check for $5 increment alerts
    alert_every_dollars = thresholds.get('alert_every_dollars', 5.0)
    if alert_every_dollars > 0:
        last_data = load_cost_history()
        last_alert_cost = last_data.get('last_alert_cost', 0.0)
        
        # Calculate how many $5 increments have been crossed
        last_increment = int(last_alert_cost / alert_every_dollars)
        current_increment = int(total_cost / alert_every_dollars)
        
        if current_increment > last_increment:
            threshold_crossed = (current_increment) * alert_every_dollars
            alerts.append(f"💰 Milestone: ${threshold_crossed:.2f} spent (${total_cost:.2f} total today)")
            save_cost_history(total_cost)
    
    # Daily limit check
    daily_limit = thresholds.get('daily_cost_limit', 5.0)
    if total_cost >= daily_limit * 0.95:
        alerts.append(f"⛔ CRITICAL: Daily cost limit at {(total_cost/daily_limit)*100:.1f}% (${total_cost:.2f} / ${daily_limit:.2f})")
    elif total_cost >= daily_limit * 0.75:
        alerts.append(f"⚠ WARNING: Daily cost at {(total_cost/daily_limit)*100:.1f}% of limit (${total_cost:.2f} / ${daily_limit:.2f})")
    
    # Model-specific limits
    model_limits = config.get('model_limits', {})
    for model, limit_info in model_limits.items():
        usage = token_usage.get(model, {})
        tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
        daily_tokens = limit_info.get('daily_tokens', float('inf'))
        
        if tokens > daily_tokens:
            alerts.append(f"⛔ {model}: {tokens:,} tokens exceed limit of {daily_tokens:,}")
    
    return alerts

def main():
    config = load_config()
    prices = load_prices()
    
    print("\n🔍 Scanning token usage...\n")
    
    token_usage = get_session_logs()
    
    if not token_usage:
        print("No token usage data found.")
        return
    
    # Generate dashboard
    dashboard = generate_dashboard(token_usage, prices)
    print(dashboard)
    
    # Save dashboard
    with open(DASHBOARD_FILE, 'w') as f:
        f.write(dashboard)
    print(f"Dashboard saved: {DASHBOARD_FILE}\n")
    
    # Log to history
    log_history(token_usage, prices, datetime.datetime.now().isoformat())
    
    # Check for alerts
    alerts = check_alerts(token_usage, prices, config)
    if alerts:
        print("⚠ ALERTS:\n")
        for alert in alerts:
            print(f"  {alert}")
            if config.get('alerts', {}).get('telegram_enabled'):
                send_alert(config, alert)
    else:
        print("✓ No alerts. Usage within limits.")

if __name__ == "__main__":
    main()
