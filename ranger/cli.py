import argparse
import sys

import json
import os

from .scanner import Scanner
from .reporter import Reporter

def load_prompts(file_path, input_format=None, prompt_col='prompt', timestamp_col=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    fmt = input_format.lower() if input_format else ext.lstrip('.')

    items = []
    try:
        if fmt == 'csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            col = prompt_col if prompt_col in df.columns else df.columns[0]
            if timestamp_col and timestamp_col in df.columns:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
            
            for _, row in df.iterrows():
                item = {'prompt': str(row[col])}
                if timestamp_col and timestamp_col in df.columns and pd.notnull(row[timestamp_col]):
                    item['timestamp'] = row[timestamp_col].isoformat()
                items.append(item)
                 
        elif fmt in ['json', 'jsonl']:
            with open(file_path, 'r') as f:
                if fmt == 'jsonl':
                    data = [json.loads(line) for line in f if line.strip()]
                else:
                    data = json.load(f)
                    
                if isinstance(data, dict) and prompt_col in data and isinstance(data[prompt_col], list):
                    data = data[prompt_col] # Handle {"prompts": [...]}
                
                if isinstance(data, list):
                    for obj in data:
                        if isinstance(obj, dict):
                            item = {'prompt': str(obj.get(prompt_col, list(obj.values())[0]))}
                            if timestamp_col and timestamp_col in obj:
                                item['timestamp'] = obj[timestamp_col]
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
    parser.add_argument("input", help="Input file path")
    parser.add_argument("--output", "-o", default="report.html", help="Output HTML report path", required=False)
    parser.add_argument("--input-format", "-f", choices=['csv', 'json', 'jsonl', 'txt'], help="Input format", required=False)
    parser.add_argument("--prompt-col", "-p", default="prompt", help="Prompt column name for CSV/JSON", required=False)
    parser.add_argument("--workers", "-w", type=int, default=1, help="Parallel workers", required=False)
    parser.add_argument("--config", "-c", help="Path to PromptForest config (YAML)", required=False)
    parser.add_argument("--timestamp-col", "-t", help="Timestamp column name", required=False)
    
    args = parser.parse_args()
    
    try:
        print(f"Loading prompts from {args.input}...")
        items = load_prompts(args.input, args.input_format, args.prompt_col, args.timestamp_col)
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
    
    print(f"Report saved to {args.output}")

if __name__ == "__main__":
    main()
