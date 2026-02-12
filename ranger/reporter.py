from jinja2 import Template
import datetime
import os
import json
import csv
import numpy as np

class Reporter:
    def __init__(self, output_path, output_format=None):
        self.output_path = output_path
        self.output_format = output_format
    
    def generate(self, results):
        total = len(results)
        
        # Calculate basic stats
        malicious_count = len([r for r in results if r.get('is_malicious', False)])
        safe_count = total - malicious_count
        
        scores = [r.get('malicious_score', 0.0) for r in results]
        uncertainties = [r.get('uncertainty', 0.0) for r in results]
        
        avg_score = np.mean(scores) if scores else 0.0
        avg_uncertainty = np.mean(uncertainties) if uncertainties else 0.0

        # Prepare time series data if available
        time_series = []
        if any('timestamp' in r for r in results):
            time_series = sorted([
                {'t': r['timestamp'], 's': r.get('malicious_score', 0.0)}
                for r in results if r.get('timestamp')
            ], key=lambda x: x['t'])

        # Render report
        template_path = os.path.join(os.path.dirname(__file__), 'report_template.html')
        with open(template_path, 'r') as f:
            template_str = f.read()

        template = Template(template_str)
        html_content = template.render(
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_prompts=total,
            malicious_count=malicious_count,
            safe_count=safe_count,
            avg_score=avg_score,
            avg_uncertainty=avg_uncertainty,
            prompts=sorted(results, key=lambda x: x.get('index', 0)),
            scores=scores,
            uncertainties=uncertainties,
            has_time_data=bool(time_series),
            time_series=time_series
        )
        
        with open(self.output_path, 'w') as f:
            f.write(html_content)

        if self.output_format:
            fmt = self.output_format.lower()
            base, ext = os.path.splitext(self.output_path)
            if ext == '.html':
                extra_output_path = f"{base}.{fmt}"
            else:
                extra_output_path = f"{self.output_path}.{fmt}"

            if fmt == 'json':
                with open(extra_output_path, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
            elif fmt == 'csv':
                if results:
                    keys = set()
                    for r in results:
                        keys.update(r.keys())
                    fieldnames = sorted(list(keys))
                    
                    with open(extra_output_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(results)
            elif fmt == 'txt':
                with open(extra_output_path, 'w') as f:
                    for r in sorted(results, key=lambda x: x.get('index', 0)):
                        f.write(f"'{r.get('prompt', '')}'\n - Malicious: {r.get('is_malicious', False)}\n - Score: {r.get('malicious_score', -1)}\n - Confidence: {r.get('confidence', -1)}\n - Uncertainty: {r.get('uncertainty', -1)}\n")
