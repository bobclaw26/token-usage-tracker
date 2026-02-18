#!/usr/bin/env python3
import os
import json
import glob
import datetime

def load_model_prices():
    """Load model pricing information"""
    price_file = os.path.join(
        os.path.dirname(__file__), 
        '..', 'references', 'model_prices.json'
    )
    try:
        with open(price_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: Model prices configuration not found")
        return {}
    except json.JSONDecodeError:
        print("Error: Invalid JSON in model prices configuration")
        return {}

def parse_session_logs():
    """Parse OpenClaw session logs for token usage"""
    # Path to OpenClaw session logs
    session_log_pattern = os.path.expanduser('~/.openclaw/agents/*/sessions/*.jsonl')
    
    token_usage = {}
    model_prices = load_model_prices()
    
    for log_file in glob.glob(session_log_pattern):
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        # Check for model and token information
                        if 'model' in entry and 'usage' in entry:
                            model = entry['model']
                            input_tokens = entry['usage'].get('input_tokens', 0)
                            output_tokens = entry['usage'].get('output_tokens', 0)
                            
                            # Initialize model entry if not exists
                            if model not in token_usage:
                                token_usage[model] = {
                                    'input_tokens': 0,
                                    'output_tokens': 0,
                                    'total_cost': 0.0
                                }
                            
                            # Accumulate tokens
                            token_usage[model]['input_tokens'] += input_tokens
                            token_usage[model]['output_tokens'] += output_tokens
                            
                            # Calculate cost if pricing is available
                            if model in model_prices:
                                input_cost = (input_tokens / 1000) * model_prices[model]['input_price_per_1k_tokens']
                                output_cost = (output_tokens / 1000) * model_prices[model]['output_price_per_1k_tokens']
                                token_usage[model]['total_cost'] += input_cost + output_cost
                    
                    except json.JSONDecodeError:
                        continue
        except IOError:
            print(f"Could not read log file: {log_file}")
    
    return token_usage

def generate_report(token_usage):
    """Generate a human-readable report of token usage"""
    report = "🤖 OpenClaw Token Usage Report\n"
    report += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for model, usage in token_usage.items():
        report += f"Model: {model}\n"
        report += f"Input Tokens: {usage['input_tokens']:,}\n"
        report += f"Output Tokens: {usage['output_tokens']:,}\n"
        report += f"Total Tokens: {usage['input_tokens'] + usage['output_tokens']:,}\n"
        report += f"Estimated Cost: ${usage['total_cost']:.2f}\n\n"
    
    return report

def main():
    """Main function to track token usage"""
    token_usage = parse_session_logs()
    
    # Print report to console
    print(generate_report(token_usage))
    
    # Optional: Save report to a file
    report_dir = os.path.join(
        os.path.dirname(__file__), 
        '..', 'references'
    )
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, 'token_usage_report.txt')
    
    with open(report_path, 'w') as f:
        f.write(generate_report(token_usage))
    
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    main()