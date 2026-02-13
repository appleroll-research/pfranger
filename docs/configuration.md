# Configuration

PFRanger uses the PromptForest engine, which can be configured via a YAML file. You can pass a configuration file using the `--config` argument.

If no configuration is provided, PFRanger uses the default "Benchmark" configuration which balances accuracy and performance.

## Example Configuration

```yaml
# Example configuration file for PromptForest
models:
  - name: llama_guard
    enabled: true
    accuracy_weight: 0.6

  - name: vijil
    enabled: true
    accuracy_weight: 1.0
    
  - name: xgboost
    enabled: true
    accuracy_weight: 0.5
    threshold: 0.1

# System Settings
settings:
  # Device: 'auto' (default), 'cuda', 'mps', or 'cpu'
  device: 'auto'
  
  # Use half precision for faster inference on supported hardware
  fp16: true

logging:
  # Include detailed model scores in response 
  stats: true
```

## Structure

### `models`
A list of model definitions that participate in the ensemble.

- `name`: The identifier of the model (e.g., `llama_guard`, `vijil`, `xgboost`).
- `enabled`: `true` or `false` to enable/disable the model.
- `accuracy_weight`: A float value representing the voting weight of this model in the ensemble.
- `threshold`: (Optional) Specific threshold for this model if applicable.

### `settings`
Global system settings.

- `device`: Hardware acceleration device.
    - `auto`: Automatically select best available (CUDA > MPS > CPU).
    - `cuda`: Force NVIDIA GPU.
    - `mps`: Force macOS Metal Performance Shaders (Apple Silicon).
    - `cpu`: Force CPU usage.
- `fp16`: Boolean. Enable 16-bit floating point precision (half-precision) to save memory and increase speed on compatible GPUs.

### `logging`
Controls verbosity and output details.

- `stats`: `true` to include detailed scoring statistics in the results.
