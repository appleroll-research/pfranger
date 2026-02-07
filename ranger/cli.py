
import argparse
import sys
import pandas as pd
import json
import os
from .scanner import Scanner
from .reporter import Reporter

def parse_weights(weights_str):
    """
    Parse weights string like "llama_guard=0.5,xgboost=1.0" into a dict.
    """
    if not weights_str:
        return {}
    
    weights = {}
    parts = weights_str.split(',')
    for part in parts:
        if '=' in part:
            k, v = part.split('=')
            weights[k.strip()] = float(v.strip())
    return weights

def load_prompts_with_meta(file_path, format=None, column='prompt', time_col=None):
    """
    Load prompts from a file, optionally extracting timestamp metadata.
    Returns list of {'prompt': str, 'timestamp': datetime (optional), ...}
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if format:
        fmt = format.lower()
    else:
        if ext == '.csv':
            fmt = 'csv'
        elif ext == '.jsonl':
            fmt = 'jsonl'
        elif ext == '.json':
            fmt = 'json'
        elif ext in ['.txt', '.log']:
            fmt = 'txt'
        else:
            raise ValueError(f"Could not infer format from extension {ext}. Please specify --format.")

    items = []
    
    try:
        if fmt == 'csv':
            df = pd.read_csv(file_path)
            
            # Find prompt column
            prompt_c = column if column in df.columns else df.columns[0]
            if column not in df.columns:
                 print(f"Warning: Column '{column}' not found. Using '{prompt_c}'.")
            
            # Find time column
            time_c = None
            if time_col:
                if time_col in df.columns:
                    time_c = time_col
                    # Parse dates
                    df[time_c] = pd.to_datetime(df[time_c], errors='coerce')
                else:
                    print(f"Warning: Time column '{time_col}' not found.")

            for _, row in df.iterrows():
                item = {'prompt': str(row[prompt_c])}
                if time_c and pd.notnull(row[time_c]):
                    item['timestamp'] = row[time_c].isoformat()
                items.append(item)
                 
        elif fmt == 'jsonl':
            with open(file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if isinstance(data, dict):
                            item = {'prompt': str(data.get(column, list(data.values())[0]))}
                            if time_col and time_col in data:
                                item['timestamp'] = data[time_col]
                            items.append(item)
                        else:
                            items.append({'prompt': str(data)})
                            
        elif fmt == 'json':
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for obj in data:
                        if isinstance(obj, dict):
                             item = {'prompt': str(obj.get(column, list(obj.values())[0]))}
                             if time_col and time_col in obj:
                                 item['timestamp'] = obj[time_col]
                             items.append(item)
                        else:
                             items.append({'prompt': str(obj)})
                elif isinstance(data, dict):
                    if column in data and isinstance(data[column], list):
                        # Simple list
                        for p in data[column]:
                             items.append({'prompt': str(p)})
                    else:
                        raise ValueError("JSON structure not supported (must be list of objects)")

        elif fmt == 'txt':
            with open(file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        items.append({'prompt': line.strip()})

    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

    return items

def main():
    parser = argparse.ArgumentParser(description="PromptForest Ranger - Audit prompts for injection/jailbreaks")
    
    parser.add_argument("input_file", help="Path to input file containing prompts")
    parser.add_argument("--output", "-o", default="ranger_report.html", help="Path to output HTML report")
    parser.add_argument("--format", "-f", choices=['csv', 'json', 'jsonl', 'txt'], help="Input file format")
    parser.add_argument("--col", "-c", default="prompt", help="Column name for CSV/JSON input")
    
    parser.add_argument("--workers", "-w", type=int, default=4, help="Number of parallel workers")
    
    # Config file argument
    parser.add_argument("--config", help="Path to PromptForest configuration file (YAML)")
    
    # Metadata arguments
    parser.add_argument("--time-col", help="Column name containing timestamp (for time-series analysis)")

    # Config overrides
    parser.add_argument("--weights", help="Override model weights (e.g. 'llama_guard=0.5,xgboost=1.0')")
    parser.add_argument("--threshold", type=float, help="Override XGBoost threshold")
    
    args = parser.parse_args()
    
    # 1. Load Prompts
    try:
        print(f"Loading prompts from {args.input_file}...")
        # Load raw data first to handle time col
        items = load_prompts_with_meta(args.input_file, args.format, args.col, args.time_col)
        print(f"Loaded {len(items)} prompts.")
    except Exception as e:
        print(f"Error loading prompts: {e}")
        sys.exit(1)
        
    if not items:
        print("No prompts found.")
        sys.exit(0)

    # 2. Configure Scanner
    # Use PromptForest's own config loader to ensure proper merging with defaults
    try:
        from promptforest.config import load_config
        # If config file provided, load it properly via PF to get defaults + overrides
        # passing absolute path to ensure it finds it
        config_path = os.path.abspath(args.config) if args.config else None
        final_config = load_config(config_path)
        if args.config:
            print(f"Loaded configuration from {args.config}")
    except ImportError:
         print("Could not import promptforest.config. Falling back to simple loading.")
         # Fallback logic if import fails (shouldn't happen if env is right)
         final_config = None 
         if args.config:
            import yaml
            with open(args.config, 'r') as f:
                final_config = yaml.safe_load(f)

    # If loading failed or returned empty/defaults, and no config file was meant,
    # we might want benchmark defaults. 
    # BUT load_config() returns standard defaults if path is None.
    # We want BENCHMARK defaults if user didn't specify a config file?
    # User requirement: "Ranger should also accept config files"
    # User requirement: "uses Benchmark configuration by default"
    
    # If args.config is NOT provided, we want Benchmark info. 
    # load_config(None) gives "Default" config (Standard weights, not benchmark weights).
    # We need to apply overrides or use Scanner's default behavior.
    
    scanner_config = final_config
    use_benchmark_defaults = False
    
    if not args.config:
        # No config file -> Use Benchmark Defaults (handled by Scanner if config=None)
        scanner_config = None
        use_benchmark_defaults = True
    else:
        # Config file -> We loaded it. 
        # But if the user provided a config file that relies on defaults (like the one with just names),
        # load_config has merged it with STANDARD defaults.
        # This matches PF behavior.
        pass
    
    # Apply CLI overrides (weights/threshold) to whatever config we have
    # If scanner_config is None, we can't easily override before Scanner init unless we construct it.
    
    # To support overrides on top of Benchmark defaults (when no config file):
    if scanner_config is None:
        from .scanner import BENCHMARK_CONFIG
        import copy
        scanner_config = copy.deepcopy(BENCHMARK_CONFIG)
        # We manually load settings/logging defaults since BENCHMARK_CONFIG is partial in scanner.py?
        # Actually scanner.py constructs full config from BENCHMARK_CONFIG.
        # Let's import the full construction logic or just use BENCHMARK_CONFIG + standard defaults here.
        
        # Simpler: Initialize Scanner, then check if we need to apply overrides? 
        # No, Scanner inits ensemble immediately.
        
        # Let's just use BENCHMARK_CONFIG as base if no config file.
        # Re-construct a full valid config for overrides.
        from promptforest.config import DEFAULT_CONFIG
        full_defaults = copy.deepcopy(DEFAULT_CONFIG)
        # Update models with benchmark ones
        full_defaults['models'] = BENCHMARK_CONFIG['models']
        scanner_config = full_defaults

    # Apply overrides
    user_weights = parse_weights(args.weights)
    if user_weights or args.threshold is not None:
        if 'models' in scanner_config:
            for m in scanner_config['models']:
                if m['name'] in user_weights:
                    m['accuracy_weight'] = user_weights[m['name']]
                    print(f"Overridden {m['name']} weight to {m['accuracy_weight']}")
                if m['name'] == 'xgboost' and args.threshold is not None:
                    m['threshold'] = args.threshold
                    print(f"Overridden xgboost threshold to {m['threshold']}")

    scanner = Scanner(config=scanner_config, use_benchmark_defaults=False)
    
    # 3. Scan
    print(f"Starting scan with {args.workers} workers...")
    results = scanner.scan_prompts(items, workers=args.workers)
    
    # 4. Report
    reporter = Reporter(args.output)
    reporter.generate(results)
    
    # 5. Summary to stdout
    malicious_count = sum(1 for r in results if r.get('is_malicious', False))
    print(f"\nScan complete.")
    print(f"Malicious: {malicious_count}/{len(items)}")
    print(f"Report saved to {args.output}")

if __name__ == "__main__":
    main()
