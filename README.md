# PromptForest Ranger

PromptForest Ranger is a high-performance CLI tool for auditing LLM prompts for injection attacks and jailbreaks. It leverages the PromptForest ensemble engine (Llama Guard, Vijil, XGBoost) to scan datasets and generate comprehensive HTML reports.

## Features

- **Multi-Format Support**: Scan CSV, JSON, JSONL, and TXT files.
- **Parallel Processing**: Multi-threaded scanning for large datasets.
- **Advanced Reporting**: Interactive HTML reports with charts and time-series analysis.
- **Configurable**: Uses PromptForest configuration standards.

## Installation

```bash
git clone https://github.com/promptforest/ranger.git
cd ranger
pip install -r requirements.txt
```

## Usage

```bash
python3 -m ranger.cli [INPUT_FILE] [OPTIONS]
```

### Examples

Scan a CSV file:
```bash
python3 -m ranger.cli validation_prompts.csv --col text
```

Scan with custom configuration:
```bash
python3 -m ranger.cli prompts.jsonl --config my_config.yaml
```

Generate report with time-series data:
```bash
python3 -m ranger.cli logs.csv --time-col timestamp
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `input_file` | Path to the file containing prompts | Required |
| `--output`, `-o` | Output path for HTML report | `ranger_report.html` |
| `--format`, `-f` | Force input format (csv, json, jsonl, txt) | Auto-detect |
| `--col`, `-c` | Column name for prompts (CSV/JSON) | `prompt` |
| `--time-col` | Column name for timestamp | None |
| `--workers`, `-w` | Number of parallel worker threads | 4 |
| `--config` | Path to PromptForest YAML configuration file | Benchmark Defaults |

## Configuration

Ranger uses the `promptforest` library configuration. Valid YAML configurations can enable/disable specific models or adjust weights.

## License

See [LICENSE](LICENSE).
