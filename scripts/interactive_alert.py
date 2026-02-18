#!/usr/bin/env python3
"""
Interactive Cost Alert Handler

When daily/weekly/monthly limits are approached, asks user if they want to raise the limit.
Allows dynamic adjustment of thresholds based on user input.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
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

def get_alert_message(period, current_cost, current_limit, percentage):
    """Generate interactive alert message"""
    message = f"""⛔ **Daily Cost Alert**

Current spending: **${current_cost:.2f}** / **${current_limit:.2f}** ({percentage:.1f}%)

Would you like to raise the daily limit?

Reply with:
• A number (e.g., `15` for $15/day)
• An increase (e.g., `+5` to add $5/day)
• `keep` to maintain current limit
• `disable` to turn off alerts

Current setting: ${current_limit:.2f}/day
"""
    return message

def process_user_response(response, current_limit):
    """Parse user input and return new limit or None"""
    response = response.strip().lower()
    
    if response == 'keep' or response == 'no':
        return None
    
    if response == 'disable':
        return -1  # Special value for disabled
    
    try:
        # Check if it's an increase (e.g., "+5")
        if response.startswith('+'):
            increase = float(response[1:])
            return current_limit + increase
        
        # Otherwise treat as absolute value
        new_limit = float(response)
        if new_limit > 0:
            return new_limit
    except ValueError:
        pass
    
    return None

def update_limit(period, new_limit):
    """Update the daily/weekly/monthly limit"""
    config = load_config()
    if not config:
        return False
    
    period_key = f"{period}_cost_limit"
    if period_key in config.get('thresholds', {}):
        old_limit = config['thresholds'][period_key]
        config['thresholds'][period_key] = new_limit
        save_config(config)
        return old_limit, new_limit
    
    return False

def generate_confirmation(period, old_limit, new_limit):
    """Generate confirmation message"""
    if new_limit == -1:
        return f"✓ Alerts disabled for {period} limit"
    
    change = new_limit - old_limit
    direction = "increased" if change > 0 else "decreased"
    
    return f"""✓ **Limit Updated**

{period.capitalize()} cost limit {direction}:
${old_limit:.2f} → **${new_limit:.2f}**
(change: ${change:+.2f})

New alerts will:
• Fire at 75%: ${new_limit * 0.75:.2f}
• Fire at 95%: ${new_limit * 0.95:.2f}
"""

def main():
    """Main handler - called when limit is approached"""
    
    if len(sys.argv) < 4:
        print("Usage: interactive_alert.py <period> <current_cost> <current_limit>")
        sys.exit(1)
    
    period = sys.argv[1]  # daily, weekly, monthly
    current_cost = float(sys.argv[2])
    current_limit = float(sys.argv[3])
    
    percentage = (current_cost / current_limit) * 100
    
    # Generate and display message
    message = get_alert_message(period, current_cost, current_limit, percentage)
    print(message)
    
    # Wait for user input
    print("\n(Waiting for your response...)\n")
    user_input = input("> ").strip()
    
    if not user_input:
        print("❌ No response provided. Limit unchanged.")
        return
    
    new_limit = process_user_response(user_input, current_limit)
    
    if new_limit is None:
        print("❌ Invalid input. Limit unchanged.")
        return
    
    # Update config
    result = update_limit(period, new_limit if new_limit > 0 else -1)
    
    if result:
        old_limit, updated_limit = result
        confirmation = generate_confirmation(period, old_limit, updated_limit)
        print(confirmation)
    else:
        print("❌ Failed to update limit.")

if __name__ == "__main__":
    main()
