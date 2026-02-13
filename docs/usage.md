# Usage

PFRanger is a command-line interface (CLI) tool. You can run it using the `pfranger` command.

## Basic Usage

```bash
pfranger [INPUT_FILE] [OPTIONS]
```

### Examples

**Scan a CSV file:**
```bash
pfranger validation_prompts.csv -p text
```

**Scan with custom configuration:**
```bash
pfranger prompts.jsonl -c my_config.yaml
```

**Output to JSON alongside HTML:**
```bash
pfranger input.txt --output-format json
```

## Command Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `input` | | Path to the file containing prompts. | **Required** |
| `--output` | `-o` | Path for the output HTML report. | `report.html` |
| `--input-format` | `-f` | Force input format (`csv`, `json`, `jsonl`, `txt`). If not specified, inferred from extension. | Auto-detect |
| `--output-format` | | Add an additional output format (`csv`, `json`, `text`, `txt`) alongside the HTML report. | None |
| `--prompt-col` | `-p` | Column name (CSV) or key (JSON) containing the prompts. | `prompt` |
| `--timestamp-col` | `-t` | Column name or key containing the timestamp. | None |
| `--workers` | `-w` | Number of parallel worker threads for scanning. | `1` |
| `--config` | `-c` | Path to a custom PromptForest YAML configuration file. | Benchmark Defaults |

## Input Formats

PFRanger supports several input formats. It attempts to detect the format from the file extension, but you can force a format using `--input-format`.

### CSV
Expects a Comma Separated Values file.
* Uses the column specified by `--prompt-col` (defaults to "prompt").
* If that column is missing, it falls back to the *first column*.
* Optionally reads a timestamp column if `--timestamp-col` is provided.

### JSON & JSONL
* **JSONL**: Each line is a valid JSON object.
* **JSON**: Can be a list of objects `[...]` or a wrapper object `{"prompts": [...]}`.
* Extracts prompt text using `--prompt-col` key.
* If the items are simple strings instead of objects, it simply reads the strings.

### Text (txt/log)
* Reads the file line by line.
* Each non-empty line is treated as a separate prompt.
