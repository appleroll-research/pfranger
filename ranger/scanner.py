
import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import numpy as np

# Ensure promptforest is importable
PROMPTFOREST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'promptforest'))
if PROMPTFOREST_PATH not in sys.path:
    sys.path.append(PROMPTFOREST_PATH)

try:
    from promptforest.lib import PFEnsemble
    from promptforest.config import DEFAULT_CONFIG, MODELS_DIR
    import promptforest.config as pf_config
except ImportError:
    # If installed as a package, it might be just 'promptforest'
    try:
        from promptforest.lib import PFEnsemble
        from promptforest.config import DEFAULT_CONFIG, MODELS_DIR
        import promptforest.config as pf_config
    except ImportError:
        print("Error: Could not import promptforest. Please ensure it is installed or in a sibling directory.")
        sys.exit(1)

# Benchmark-optimized Configuration
BENCHMARK_CONFIG = {
    "models": [
        {"name": "llama_guard", "type": "hf", "path": "llama_guard", "enabled": True, "accuracy_weight": 0.6},
        {"name": "vijil", "type": "hf", "path": "vijil_dome", "enabled": True, "accuracy_weight": 1.0},
        {"name": "xgboost", "type": "xgboost", "enabled": True, "threshold": 0.10, "accuracy_weight": 0.5}
    ],
    "settings": {
        "device": "auto",
        "fp16": True
    },
    "logging": {
        "stats": True
    }
}

class Scanner:
    def __init__(self, config=None, use_benchmark_defaults=True):
        self.config = config or {}
        
        if use_benchmark_defaults and not config:
            # Merge benchmark defaults with any provided settings
            # For simplicity, we just use the benchmark models list if no models config provided
            base_config = DEFAULT_CONFIG.copy()
            base_config['models'] = BENCHMARK_CONFIG['models']
            if 'settings' in self.config:
                base_config['settings'].update(self.config['settings'])
            self.model_config = base_config
        else:
             # Use provided or library default
             self.model_config = self.config if self.config else DEFAULT_CONFIG

        print("Initializing PromptForest Engine...")
        
        # Check if we need to download models. If so, show output. If not, silence initialization noise.
        should_silence = self._check_models_present(self.model_config)
        
        if should_silence:
            # Silence stdout/stderr during init to hide "Using FP16" and other noise
            import contextlib
            import io
            f_out = io.StringIO()
            f_err = io.StringIO()
            with contextlib.redirect_stdout(f_out), contextlib.redirect_stderr(f_err):
                try:
                    self.ensemble = PFEnsemble(config=self.model_config)
                except Exception:
                    # If init fails, we probably want to see why, so print the captured stderr
                    print(f_err.getvalue(), file=sys.stderr)
                    raise
        else:
            # Show output (download progress)
            self.ensemble = PFEnsemble(config=self.model_config)
    
    def _check_models_present(self, config):
        """Check if all enabled models in config are present on disk."""
        try:
            if not MODELS_DIR.exists():
                return False
            
            for model in config.get('models', []):
                if not model.get('enabled', True):
                    continue
                
                # Logic copied from lib.py/download.py essentially
                if model.get('type') == 'hf':
                    path = MODELS_DIR / model.get('path', model.get('name'))
                    if not path.exists():
                        return False
                
                # Check sentence transformer
                st_path = MODELS_DIR / 'sentence_transformer'
                if not st_path.exists():
                    return False
                    
            return True
        except Exception:
            # On error, don't silence
            return False

    def scan_prompts(self, items, workers=4):
        """
        Scan a list of prompts in parallel.
        items: List of dictionaries containing 'prompt' and optionally 'timestamp'
        Returns a list of result dictionaries.
        """
        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Map prompts to futures
            # items can be string (legacy) or dict
            future_to_item = {}
            for i, item in enumerate(items):
                if isinstance(item, dict):
                    prompt_text = item.get('prompt', '')
                else:
                    prompt_text = str(item)
                    item = {'prompt': prompt_text} # normalize
                
                future = executor.submit(self.ensemble.check_prompt, prompt_text)
                future_to_item[future] = (i, item)

            # Using tqdm for progress bar
            files_pbar = tqdm(total=len(items), desc="Scanning Prompts", unit="prompt")
            
            for future in as_completed(future_to_item):
                idx, item_data = future_to_item[future]
                prompt_text = item_data.get('prompt', '')
                
                # Base result structure (safe default)
                res = {
                    'prompt': prompt_text,
                    'index': idx,
                    'is_malicious': False,
                    'malicious_score': 0.0,
                    'confidence': 0.0,
                }
                
                # Copy metadata (timestamp etc)
                for k, v in item_data.items():
                    if k != 'prompt':
                        res[k] = v

                try:
                    inference_res = future.result()
                    # Check for error in result (e.g. "No models loaded")
                    if 'error' in inference_res:
                        res['error'] = inference_res['error']
                    else:
                        # Merge inference results
                        res.update(inference_res)
                        
                        # Fix for potential missing is_malicious if something weird happened
                        if 'is_malicious' not in res:
                             if 'error' not in res:
                                 res['error'] = 'Invalid response from inference engine'
                             
                except Exception as e:
                    print(f"Error processing prompt {idx}: {e}")
                    res['error'] = str(e)
                
                results.append(res)
                files_pbar.update(1)
            
            files_pbar.close()
            
        # Sort by original index
        results.sort(key=lambda x: x['index'])
        return results

