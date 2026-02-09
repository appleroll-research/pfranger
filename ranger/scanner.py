from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import contextlib
import io

from promptforest.lib import PFEnsemble
from promptforest.config import DEFAULT_CONFIG, MODELS_DIR

DEFAULT_CONFIG = {
    "models": [
        {"name": "llama_guard", "type": "hf", "path": "llama_guard", "enabled": True, "accuracy_weight": 0.6},
        {"name": "vijil", "type": "hf", "path": "vijil_dome", "enabled": True, "accuracy_weight": 1.0},
        {"name": "xgboost", "type": "xgboost", "enabled": True, "threshold": 0.10, "accuracy_weight": 0.5}
    ],
    "settings": {"device": "auto", "fp16": True},
    "logging": {"stats": True}
}

class Scanner:
    def __init__(self, config=None):
        if not config:
            self.config = DEFAULT_CONFIG.copy()
            self.config['models'] = DEFAULT_CONFIG['models']
            self.config['settings'].update(DEFAULT_CONFIG['settings'])
        else:
            self.config = config

        print("Initializing PromptForest Engine...")
        
        # Silence initialization unless models need downloading
        # 
        if self._check_models_present(self.config):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.ensemble = PFEnsemble(config=self.config)
        else:
            self.ensemble = PFEnsemble(config=self.config)
    
    def _check_models_present(self, config):
        try:
            if not MODELS_DIR.exists(): return False
            for model in config.get('models', []):
                if not model.get('enabled', True): continue
                if model.get('type') == 'hf':
                    if not (MODELS_DIR / model.get('path', model.get('name'))).exists(): return False
            return (MODELS_DIR / 'sentence_transformer').exists()
        except:
            return False

    def scan_prompts(self, items, workers=4):
        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_item = {}
            for i, item in enumerate(items):
                prompt = item.get('prompt', '') if isinstance(item, dict) else str(item)
                item_data = item if isinstance(item, dict) else {'prompt': prompt}
                future = executor.submit(self.ensemble.check_prompt, prompt)
                future_to_item[future] = (i, item_data)

            pbar = tqdm(total=len(items), desc="Scanning", unit="prompt")
            
            for future in as_completed(future_to_item):
                idx, item_data = future_to_item[future]
                res = {
                    'prompt': item_data.get('prompt'),
                    'index': idx,
                    'is_malicious': False,
                    'malicious_score': 0.0,
                    'confidence': 0.0,
                    **{k: v for k, v in item_data.items() if k != 'prompt'}
                }

                try:
                    inference = future.result()
                    if 'error' in inference:
                        res['error'] = inference['error']
                    else:
                        res.update(inference)
                except Exception as e:
                    res['error'] = str(e)
                
                results.append(res)
                pbar.update(1)
            
            pbar.close()
            
        return sorted(results, key=lambda x: x['index'])
