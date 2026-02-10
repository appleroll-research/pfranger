# PromptForest Ranger

PromptForest Ranger (or PFRanger) is a CLI tool for auditing LLM prompts for injection attacks and jailbreaks. It leverages the PromptForest ensemble engine to scan datasets and generate comprehensive and accurate HTML reports.

## Features

### Works Offline
All data stays on your computer. The internet is only required to download models onto your computer. 

### Accurate and Reliable
Ranger utilises the PromptForest engine, which provides responses that are not only accurate, but also calibrated and reliable. 

### Fast
Startup latency of ~3s and an average request rate of 24 prompts/s with 3 workers.

## Installation

```bash
pip install pfranger
```

## Usage

```bash
ranger [INPUT_FILE] [OPTIONS]
```

### Examples

Scan a CSV file:
```bash
ranger validation_prompts.csv -p text
```

Scan with custom configuration:
```bash
ranger prompts.jsonl -c my_config.yaml
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `input` | Path to the file containing prompts | Required |
| `--output`, `-o` | Output path for HTML report | `report.html` |
| `--input-format`, `-f` | Force input format (csv, json, jsonl, txt) | Auto-detect |
| `--output-format` | Add additional output format | None |
| `--prompt-col`, `-p` | Column name for prompts (CSV/JSON) | `prompt` |
| `--timestamp-col`, `-t` | Column name for timestamp | None |
| `--workers`, `-w` | Number of parallel worker threads | 4 |
| `--config`, `-c` | Path to PromptForest YAML configuration file | Benchmark Defaults |

## Configuration

Ranger uses the `promptforest` library configuration. Valid YAML configurations can enable/disable specific models or adjust weights.

## License

See [LICENSE](LICENSE).
