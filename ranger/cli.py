import argparse
import sys
import pandas as pd
import json
import os

# Ensure promptforest is importable for dev environment
dev_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../promptforest'))
if os.path.exists(dev_path) and dev_path not in sys.path:
    sys.path.append(dev_path)

from .scanner import Scanner
from .reporter import Reporter

def load_prompts(file_path, format=None, column='prompt', time_col=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    fmt = format.lower() if format else ext.lstrip('.')

    items = []
    try:
        if fmt == 'csv':
            df = pd.read_csv(file_path)
            col = column if column in df.columns else df.columns[0]
            if time_col and time_col in df.columns:
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            
            for _, row in df.iterrows():
                item = {'prompt': str(row[col])}
                if time_col and time_col in df.columns and pd.notnull(row[time_col]):
                    item['timestamp'] = row[time_col].isoformat()
                items.append(item)
                 
        elif fmt in ['json', 'jsonl']:
            with open(file_path, 'r') as f:
                if fmt == 'jsonl':
                    data = [json.loads(line) for line in f if line.strip()]
                else:
                    data = json.load(f)
                    
                if isinstance(data, dict) and column in data and isinstance(data[column], list):
                    data = data[column] # Handle {"prompts": [...]}
                
                if isinstance(data, list):
                    for obj in data:
                        if isinstance(obj, dict):
                            item = {'prompt': str(obj.get(column, list(obj.values())[0]))}
                            if time_col and time_col in obj:
                                item['timestamp'] = obj[time_col]
                            items.append(item)
                        else:
                            items.append({'prompt': str(obj)})
        
        elif fmt in ['txt', 'log']:
            with open(file_path, 'r') as f:
                items = [{'prompt': line.strip()} for line in f if line.strip()]
        
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

    return items

def main():
    parser = argparse.ArgumentParser(description="PromptForest Ranger - Audit prompts for injection/jailbreaks")
    parser.add_argument("input_file", help="Input file path")
    parser.add_argument("--output", "-o", default="ranger_report.html", help="Output HTML report path")
    parser.add_argument("--format", "-f", choices=['csv', 'json', 'jsonl', 'txt'], help="Input format")
    parser.add_argument("--col", "-c", default="prompt", help="Prompt column name for CSV/JSON")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Parallel workers")
    parser.add_argument("--config", help="Path to PromptForest config (YAML)")
    parser.add_argument("--time-col", help="Timestamp column name")
    
    args = parser.parse_args()
    
    try:
        print(f"Loading prompts from {args.input_file}...")
        items = load_prompts(args.input_file, args.format, args.col, args.time_col)
        print(f"Loaded {len(items)} prompts.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    if not items:
        print("No prompts found.")
        sys.exit(0)

    # Load configuration
    scanner_config = None
    if args.config:
        try:
            from promptforest.config import load_config
            scanner_config = load_config(os.path.abspath(args.config))
            print(f"Loaded configuration from {args.config}")
        except ImportError:
            import yaml
            with open(args.config, 'r') as f:
                scanner_config = yaml.safe_load(f)

    # Initialize Scanner (defaults to benchmark config if no config provided)
    scanner = Scanner(config=scanner_config)
    
    print(f"Starting scan with {args.workers} workers...")
    results = scanner.scan_prompts(items, workers=args.workers)
    
    reporter = Reporter(args.output)
    reporter.generate(results)
    
    malicious_count = sum(1 for r in results if r.get('is_malicious', False))
    print(f"\nScan complete. Malicious: {malicious_count}/{len(items)}")
    print(f"Report saved to {args.output}")

if __name__ == "__main__":
    main()
