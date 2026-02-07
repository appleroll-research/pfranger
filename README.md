# PromptForest Ranger

Ranger is a high-performance CLI tool for auditing prompt datasets using [PromptForest](https://github.com/promptforest/promptforest). It scans large files of prompts, detects injection/jailbreak attempts using an ensemble of models, and generates detailed HTML reports.

## Features

- **Multi-format Support**: CSV, JSON, JSONL, TXT.
- **Fast**: Parallel processing for high throughput.
- **Accurate**: Uses the PromptForest ensemble (Llama Guard, Vijil, XGBoost).
- **Reporting**: Generates interactive HTML reports with charts and statistics.

## Installation

```bash
cd ranger
pip install -e .
```

## Usage

```bash
# Scan a CSV file
ranger prompts.csv --col prompt_text

# Scan a JSONL file
ranger dataset.jsonl --format jsonl

# Override weights (e.g. trust Vijil more)
ranger prompts.csv --weights "vijil=2.0,llama_guard=0.5"

# Output to custom path
ranger prompts.csv -o my_report.html
```

## Configuration

Ranger uses the PromptForest benchmark configuration by default for maximum accuracy. You can override individual model weights via CLI arguments or provide a full PromptForest `config.yaml` using `--config`.

## License

See LICENSE.
