#!/usr/bin/env python3
"""
Handle User Response to Cost Limit Alerts

Parses user input and updates tracking_config.json accordingly.
Can be called directly with user response or via cron/webhook.

Usage:
  handle_limit_response.py "15"          # Set daily limit to $15
  handle_limit_response.py "+5"          # Increase daily limit by $5
  handle_limit_response.py "keep"        # Keep current limit
  handle_limit_response.py "disable"     # Disable critical alerts
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
CONFIG_FILE = SCRIPT_DIR / 'references' / 'tracking_config.json'

def load_config():
    """Load current tracking config"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_config(config):
    """Save updated tracking config"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def parse_response(response):
    """
    Parse user response to determine new limit.
    
    Returns: (success, new_limit, message)
    """
    response = response.strip().lower()
    
    if not response:
        return False, None, "No response provided. Limit unchanged."
    
    if response in ('keep', 'no', 'skip'):
        return True, None, "✓ Keeping current daily limit."
    
    if response == 'disable':
        return True, -1, "⚠ Critical alerts disabled. Warnings still active."
    
    try:
        # Check if it's an increase (e.g., "+5" or "+ 5")
        if response.startswith('+'):
            increase = float(response[1:].strip())
            if increase > 0:
                return True, ('increase', increase), f"Will increase daily limit by ${increase:.2f}"
        
        # Otherwise treat as absolute value
        new_limit = float(response)
        if new_limit > 0:
            return True, new_limit, f"Will set daily limit to ${new_limit:.2f}"
    
    except ValueError:
        pass
    
    return False, None, f"Invalid input: '{response}'. Please use a number (e.g., '15') or '+5' to increase."

def update_daily_limit(new_limit_spec):
    """
    Update the daily limit in config.
    
    new_limit_spec can be:
    - A number (absolute limit)
    - ('increase', amount) tuple (increase current limit)
    - -1 (disable critical alerts)
    """
    config = load_config()
    if not config:
        return False, "Could not load config"
    
    try:
        current_limit = config['thresholds']['daily_cost_limit']
        
        if new_limit_spec == -1:
            # Disable critical alerts
            config['thresholds']['alert_level_critical'] = float('inf')
            new_limit = current_limit
        elif isinstance(new_limit_spec, tuple) and new_limit_spec[0] == 'increase':
            # Increase by amount
            new_limit = current_limit + new_limit_spec[1]
        else:
            # Absolute value
            new_limit = float(new_limit_spec)
        
        # Update config
        config['thresholds']['daily_cost_limit'] = new_limit
        
        # Proportionally update weekly/monthly
        ratio = new_limit / current_limit
        config['thresholds']['weekly_cost_limit'] *= ratio
        config['thresholds']['monthly_cost_limit'] *= ratio
        
        save_config(config)
        
        return True, (current_limit, new_limit)
    
    except Exception as e:
        return False, str(e)

def main():
    """Main handler"""
    if len(sys.argv) < 2:
        print("Usage: handle_limit_response.py <user_response>")
        print("Examples: '15', '+5', 'keep', 'disable'")
        sys.exit(1)
    
    user_response = ' '.join(sys.argv[1:])
    
    # Parse response
    success, limit_spec, message = parse_response(user_response)
    print(message)
    
    if not success:
        return
    
    if limit_spec is None:
        # User said "keep" - no action needed
        return
    
    # Update config
    config_success, result = update_daily_limit(limit_spec)
    
    if not config_success:
        print(f"❌ Error: {result}")
        return
    
    old_limit, new_limit = result
    
    if new_limit == old_limit and limit_spec == -1:
        print("⛔ Critical alerts have been disabled.")
        print(f"   (Daily limit remains at ${old_limit:.2f})")
    else:
        change = new_limit - old_limit
        direction = "↑ increased" if change > 0 else "↓ decreased"
        print(f"\n✓ **Limit Updated** {direction}")
        print(f"   Daily:   ${old_limit:.2f} → ${new_limit:.2f}")
        print(f"   Weekly:  ${old_limit*6:.2f} → ${new_limit*6:.2f}")
        print(f"   Monthly: ${old_limit*30:.2f} → ${new_limit*30:.2f}")
        print(f"\nNew alert thresholds:")
        print(f"   ⚠ Warning at 75%: ${new_limit * 0.75:.2f}")
        print(f"   ⛔ Critical at 95%: ${new_limit * 0.95:.2f}")

if __name__ == "__main__":
    main()
