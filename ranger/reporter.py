import json
import os
from jinja2 import Template
import datetime

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptForest Ranger Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .summary-cards { display: flex; gap: 20px; margin-bottom: 20px; }
        .card { flex: 1; padding: 15px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid #007bff; }
        .card h3 { margin: 0 0 10px 0; font-size: 14px; color: #666; }
        .card .value { font-size: 24px; font-weight: bold; }
        .card.danger { border-left-color: #dc3545; }
        .card.success { border-left-color: #28a745; }
        .card.warning { border-left-color: #ffc107; }
        .charts { display: flex; gap: 20px; margin-bottom: 30px; height: 300px; }
        .chart-container { flex: 1; position: relative; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-danger { background: #dc3545; color: white; }
        .badge-success { background: #28a745; color: white; }
        .badge-warning { background: #ffc107; color: #212529; }
        .prompt-text { font-family: monospace; color: #555; max-width: 500px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .details-row { display: none; background: #fafafa; }
        .details-row td { white-space: pre-wrap; word-break: break-all; }
        .expand-btn { cursor: pointer; color: #007bff; border: none; background: none; }
        .search-box { width: 100%; padding: 10px; margin-bottom: 20px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PromptForest Ranger Report</h1>
        <p>Generated on {{ date }}</p>

        <div class="summary-cards">
            <div class="card">
                <h3>Total Prompts</h3>
                <div class="value">{{ total_prompts }}</div>
            </div>
            <div class="card danger">
                <h3>Malicious Detected</h3>
                <div class="value">{{ malicious_count }} ({{ "%.1f"|format(malicious_percent) }}%)</div>
            </div>
            <div class="card warning">
                <h3>Uncertain</h3>
                <div class="value">{{ uncertain_count }} ({{ "%.1f"|format(uncertain_percent) }}%)</div>
            </div>
            <div class="card success">
                <h3>Safe Prompts</h3>
                <div class="value">{{ safe_count }}</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <canvas id="pieChart"></canvas>
            </div>
            <div class="chart-container" {% if has_time_data %}style="flex: 2;"{% endif %}>
                <canvas id="{% if has_time_data %}timeChart{% else %}histChart{% endif %}"></canvas>
            </div>
        </div>
        
        {% if has_time_data %}
        <div class="charts" style="height: 250px;">
             <div class="chart-container">
                <canvas id="histChart"></canvas>
            </div>
        </div>
        {% endif %}

        <h2>All Prompts</h2>
        <input type="text" id="searchInput" class="search-box" onkeyup="searchTable()" placeholder="Search Prompts...">
        
        <table id="promptsTable">
            <thead>
                <tr>
                    <th width="50"></th>
                    <th>ID</th>
                    {% if has_time_data %}<th>Time</th>{% endif %}
                    <th>Status</th>
                    <th>Score</th>
                    <th>Prompt</th>
                </tr>
            </thead>
            <tbody>
                {% for item in prompts %}
                <tr>
                    <td><button class="expand-btn" onclick="toggleRow({{ loop.index }})">▶</button></td>
                    <td>{{ item.index }}</td>
                    {% if has_time_data %}<td>{{ item.timestamp }}</td>{% endif %}
                    <td>
                        {% if item.is_malicious %}
                            <span class="badge badge-danger">Malicious</span>
                        {% elif item.uncertainty > 0.5 %}
                            <span class="badge badge-warning">Uncertain</span>
                        {% else %}
                            <span class="badge badge-success">Safe</span>
                        {% endif %}
                    </td>
                    <td>{{ "%.4f"|format(item.malicious_score) }}</td>
                    <td class="prompt-text" title="{{ item.prompt }}">{{ item.prompt[:80] }}...</td>
                </tr>
                <tr id="row-{{ loop.index }}" class="details-row">
                    <td colspan="{% if has_time_data %}6{% else %}5{% endif %}">
                        <strong>Full Prompt:</strong><br>{{ item.prompt }}<br><br>
                        <strong>Analysis:</strong><br><pre>{{ item | tojson(indent=2) }}</pre>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        // Charts
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Malicious', 'Uncertain', 'Safe'],
                datasets: [{
                    data: [{{ malicious_count }}, {{ uncertain_count }}, {{ safe_count }}],
                    backgroundColor: ['#dc3545', '#ffc107', '#28a745']
                }]
            },
            options: { maintainAspectRatio: false, plugins: { title: { display: true, text: 'Detection Ratio' } } }
        });

        const scores = {{ scores | tojson }};
        const bins = Array(20).fill(0);
        scores.forEach(s => bins[Math.min(Math.floor(s * 20), 19)]++);
        
        const histCtx = document.getElementById('histChart').getContext('2d');
        new Chart(histCtx, {
            type: 'bar',
            data: {
                labels: Array.from({length: 20}, (_, i) => (i/20).toFixed(2) + '-' + ((i+1)/20).toFixed(2)),
                datasets: [{ label: 'Score Distribution', data: bins, backgroundColor: '#007bff' }]
            },
            options: { maintainAspectRatio: false, plugins: { title: { display: true, text: 'Score Distribution' } } }
        });
        
        {% if has_time_data %}
        const timeCtx = document.getElementById('timeChart').getContext('2d');
        new Chart(timeCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Prompt Scores over Time',
                    data: {{ time_series | tojson }}.map(d => ({ x: new Date(d.t).getTime(), y: d.s })),
                    backgroundColor: c => c.raw.y > 0.5 ? '#dc3545' : '#28a745'
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: { title: { display: true, text: 'Scores vs Time' } },
                scales: {
                    x: { type: 'linear', ticks: { callback: v => new Date(v).toLocaleTimeString() } },
                    y: { min: 0, max: 1 }
                }
            }
        });
        {% endif %}

        function toggleRow(id) {
            const row = document.getElementById('row-' + id);
            row.style.display = row.style.display === 'table-row' ? 'none' : 'table-row';
        }

        function searchTable() {
            const filter = document.getElementById("searchInput").value.toUpperCase();
            const rows = document.getElementById("promptsTable").getElementsByTagName("tr");
            
            for (let i = 1; i < rows.length; i += 2) {
                const mainRow = rows[i];
                const cells = mainRow.getElementsByTagName("td");
                const promptText = cells[cells.length - 1].innerText.toUpperCase();
                
                const display = promptText.indexOf(filter) > -1 ? "" : "none";
                mainRow.style.display = display;
                rows[i+1].style.display = "none"; 
            }
        }
    </script>
</body>
</html>
"""

class Reporter:
    def __init__(self, output_path):
        self.output_path = output_path
    
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
        template = Template(REPORT_TEMPLATE)
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
        
        print(f"Report saved to {self.output_path}")
