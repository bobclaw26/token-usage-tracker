#!/usr/bin/env python3
"""
Detect Cost Limit Alert Responses

Monitors for user responses to cost limit alerts and updates config.
Called by heartbeat to process pending responses.

This script:
1. Checks if a cost alert was recently sent
2. Looks for user responses matching pattern (number, +number, keep, disable)
3. Updates config if valid response found
4. Sends confirmation message
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent.parent
CONFIG_FILE = SCRIPT_DIR / 'references' / 'tracking_config.json'
RESPONSE_STATE_FILE = SCRIPT_DIR / 'references' / 'cost_alert_state.json'

def load_config():
    """Load current tracking config"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def load_response_state():
    """Load state of pending cost alerts"""
    try:
        with open(RESPONSE_STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'last_alert_sent': None, 'awaiting_response': False}

def save_response_state(state):
    """Save response state"""
    RESPONSE_STATE_FILE.parent.mkdir(exist_ok=True)
    with open(RESPONSE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def mark_alert_sent():
    """Mark that a cost alert was just sent"""
    state = load_response_state()
    state['last_alert_sent'] = datetime.now().isoformat()
    state['awaiting_response'] = True
    save_response_state(state)

def mark_response_processed():
    """Mark that response has been processed"""
    state = load_response_state()
    state['awaiting_response'] = False
    save_response_state(state)

def is_alert_pending():
    """Check if alert is still pending (sent within last hour)"""
    state = load_response_state()
    if not state.get('awaiting_response'):
        return False
    
    if not state.get('last_alert_sent'):
        return False
    
    try:
        sent_time = datetime.fromisoformat(state['last_alert_sent'])
        return (datetime.now() - sent_time) < timedelta(hours=1)
    except:
        return False

def parse_user_response(text):
    """Parse response text and return (is_valid, new_limit_spec)"""
    text = text.strip().lower()
    
    if not text:
        return False, None
    
    # Ignore typical conversation starters
    if any(x in text for x in ['thanks', 'ok', 'yes', 'no', 'sure', 'alright', 'cool', 'sounds good']):
        # Check if it contains a number specification
        import re
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            return True, float(match.group(1))
        return False, None
    
    if text in ('keep', 'no', 'skip'):
        return True, 'keep'
    
    if text == 'disable':
        return True, 'disable'
    
    try:
        # Check for "+5" pattern
        if '+' in text:
            import re
            match = re.search(r'\+\s*(\d+\.?\d*)', text)
            if match:
                return True, ('increase', float(match.group(1)))
        
        # Just a number
        import re
        match = re.search(r'^\d+\.?\d*$', text.strip())
        if match:
            return True, float(text.strip())
    except:
        pass
    
    return False, None

def update_limit(new_limit_spec):
    """Apply limit update to config"""
    config = load_config()
    if not config:
        return False, "Could not load config"
    
    try:
        current_limit = config['thresholds']['daily_cost_limit']
        
        if new_limit_spec == 'keep':
            return True, (current_limit, current_limit, 'kept')
        
        if new_limit_spec == 'disable':
            config['thresholds']['alert_level_critical'] = float('inf')
            SCRIPT_DIR.joinpath('references', 'tracking_config.json').write_text(
                json.dumps(config, indent=2)
            )
            return True, (current_limit, current_limit, 'disabled')
        
        if isinstance(new_limit_spec, tuple) and new_limit_spec[0] == 'increase':
            new_limit = current_limit + new_limit_spec[1]
        else:
            new_limit = float(new_limit_spec)
        
        # Update config
        config['thresholds']['daily_cost_limit'] = new_limit
        config['thresholds']['weekly_cost_limit'] = new_limit * 6
        config['thresholds']['monthly_cost_limit'] = new_limit * 30
        
        SCRIPT_DIR.joinpath('references', 'tracking_config.json').write_text(
            json.dumps(config, indent=2)
        )
        
        return True, (current_limit, new_limit, 'updated')
    
    except Exception as e:
        return False, str(e)

def main():
    """
    Main detector - checks if alert is pending and processes any response.
    Should be called from heartbeat periodically.
    """
    
    # Check if we're waiting for a response
    if not is_alert_pending():
        return  # Nothing to do
    
    print("🔍 Checking for cost limit alert responses...\n")
    
    # In a real implementation, this would check message history
    # For now, we'll provide the framework
    # This will be enhanced to integrate with OpenClaw message APIs
    
    return

if __name__ == "__main__":
    main()
