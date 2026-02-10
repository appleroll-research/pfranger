from jinja2 import Template
import datetime
import os
import json
import csv

class Reporter:
    def __init__(self, output_path, output_format=None):
        self.output_path = output_path
        self.output_format = output_format
    
    def generate(self, results):
        total = len(results)
        malicious = [r for r in results if r.get('is_malicious', False)]
        uncertain = [r for r in results if not r.get('is_malicious', False) and r.get('uncertainty', 0.0) > 0.5]
        safe = [r for r in results if not r.get('is_malicious', False) and r.get('uncertainty', 0.0) <= 0.5]
        
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
            malicious_count=len(malicious),
            malicious_percent=(len(malicious)/total*100) if total > 0 else 0,
            uncertain_count=len(uncertain),
            uncertain_percent=(len(uncertain)/total*100) if total > 0 else 0,
            safe_count=len(safe),
            prompts=sorted(results, key=lambda x: x.get('index', 0)),
            scores=[r.get('malicious_score', 0) for r in results],
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
            elif fmt in ['text', 'txt']:
                with open(extra_output_path, 'w') as f:
                    for r in sorted(results, key=lambda x: x.get('index', 0)):
                        f.write(f"Prompt: {r.get('prompt', '')}\n")
                        f.write(f"Score: {r.get('malicious_score', 'N/A')}\n")
                        f.write(f"Malicious: {r.get('is_malicious', 'N/A')}\n")
                        f.write("-" * 40 + "\n")

