
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
        h1, h2 { color: #333; }
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
        .search-box { width: 100%; padding: 10px; margin-bottom: 20px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
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
            {% if has_time_data %}
            <div class="chart-container" style="flex: 2;">
                <canvas id="timeChart"></canvas>
            </div>
            {% else %}
            <div class="chart-container">
                <canvas id="histChart"></canvas>
            </div>
            {% endif %}
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
                    {% if has_time_data %}
                    <th>Time</th>
                    {% endif %}
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
                    {% if has_time_data %}
                    <td>{{ item.timestamp }}</td>
                    {% endif %}
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
                        <strong>Full Prompt:</strong><br>
                        {{ item.prompt }}
                        <br><br>
                        <strong>Analysis:</strong><br>
                        <pre>{{ item | tojson(indent=2) }}</pre>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        // Pie Chart
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

        // Histogram Data
        const scores = {{ scores | tojson }};
        const bins = Array(20).fill(0);
        scores.forEach(s => {
            const binIndex = Math.min(Math.floor(s * 20), 19);
            bins[binIndex]++;
        });
        const labels = Array.from({length: 20}, (_, i) => (i/20).toFixed(2) + '-' + ((i+1)/20).toFixed(2));

        const histCtx = document.getElementById('histChart').getContext('2d');
        new Chart(histCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Score Distribution',
                    data: bins,
                    backgroundColor: '#007bff'
                }]
            },
            options: { 
                maintainAspectRatio: false, 
                plugins: { title: { display: true, text: 'Malicious Score Distribution' } },
                scales: { x: { title: { display: true, text: 'Score' } }, y: { title: { display: true, text: 'Count' } } }
            }
        });
        
        {% if has_time_data %}
        // Time Series Chart
        const timeData = {{ time_series | tojson }};
        
        // Simple implementation: Scatter plot with color coding
        const scatterData = timeData.map((d, i) => ({
            x: i, 
            // Actually let's try to parse date
            x: new Date(d.t).getTime(),
            y: d.s, // Score
            label: d.t
        }));
        
        const timeCtx = document.getElementById('timeChart').getContext('2d');
        new Chart(timeCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Prompt Scores over Time',
                    data: scatterData,
                    backgroundColor: scatterData.map(d => d.y > 0.5 ? '#dc3545' : '#28a745')
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: { 
                    title: { display: true, text: 'Malicious Scores vs Time' },
                    tooltip: {
                         callbacks: {
                             label: function(context) {
                                 return context.raw.label + ': ' + context.raw.y.toFixed(2);
                             }
                         }
                    }
                },
                scales: {
                    x: { 
                        type: 'linear', 
                        position: 'bottom',
                        title: { display: true, text: 'Time (Timestamp)' },
                        ticks: {
                            callback: function(value) { return new Date(value).toLocaleTimeString(); }
                        }
                    },
                    y: { title: { display: true, text: 'Malicious Score' }, min: 0, max: 1 }
                }
            }
        });
        {% endif %}

        function toggleRow(id) {
            const row = document.getElementById('row-' + id);
            row.style.display = row.style.display === 'table-row' ? 'none' : 'table-row';
        }

        function searchTable() {
            var input, filter, table, tr, i;
            input = document.getElementById("searchInput");
            filter = input.value.toUpperCase();
            table = document.getElementById("promptsTable");
            tr = table.getElementsByTagName("tr");
            
            // Loop through all table rows, and hide those who don't match the search query
            // Skip header (index 0)
            for (i = 1; i < tr.length; i += 2) {
                // Main row is i, Details row is i+1
                var mainRow = tr[i];
                var detailsRow = tr[i+1];
                
                if (!mainRow) continue;
                
                // Search Prompt text (index 4 - last column)
                // ID is index 1, Prompt is last.
                var tds = mainRow.getElementsByTagName("td");
                var promptTd = tds[tds.length - 1]; // Last column is Prompt
                
                if (promptTd) {
                    var txtValue = promptTd.textContent || promptTd.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        mainRow.style.display = "";
                        detailsRow.style.display = "none";
                    } else {
                        mainRow.style.display = "none";
                        detailsRow.style.display = "none";
                    }
                }
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
        
        # safely handle missing keys using .get() with defaults
        malicious = [r for r in results if r.get('is_malicious', False)]
        
        # Check for uncertain: Not malicious but uncertainty > 0.5
        # We need to make sure we don't double count.
        # Definition: 
        # Malicious: is_malicious=True
        # Uncertain: is_malicious=False AND uncertainty > 0.5
        # Safe: is_malicious=False AND uncertainty <= 0.5
        
        uncertain = [r for r in results if not r.get('is_malicious', False) and r.get('uncertainty', 0.0) > 0.5]
        safe = [r for r in results if not r.get('is_malicious', False) and r.get('uncertainty', 0.0) <= 0.5]
        
        malicious_count = len(malicious)
        uncertain_count = len(uncertain)
        safe_count = len(safe)
        
        scores = [r.get('malicious_score', 0.0) for r in results]
        
        # Check for time data
        has_time_data = any('timestamp' in r for r in results)
        time_series = []
        if has_time_data:
            # Prepare data for chart: [{'t': timestamp, 's': score}]
            for r in results:
                if 'timestamp' in r and r.get('timestamp'):
                    time_series.append({
                        't': r['timestamp'],
                        's': r.get('malicious_score', 0.0)
                    })
            # Sort by time
            time_series.sort(key=lambda x: x['t'])

        # Sort ALL prompts by ID (index) for auditing.
        all_prompts = sorted(results, key=lambda x: x.get('index', 0))
        
        template = Template(REPORT_TEMPLATE)
        html_content = template.render(
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_prompts=total,
            malicious_count=malicious_count,
            malicious_percent=(malicious_count/total*100) if total > 0 else 0,
            uncertain_count=uncertain_count,
            uncertain_percent=(uncertain_count/total*100) if total > 0 else 0,
            safe_count=safe_count,
            prompts=all_prompts,
            scores=scores,
            has_time_data=has_time_data,
            time_series=time_series
        )
        
        with open(self.output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Report generated at {self.output_path}")

