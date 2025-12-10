"""
Analytics Dashboard - Real-time login analytics web interface
Displays success/failure ratios by country with auto-refresh
"""

import os
import asyncio
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import asyncpg
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    "database": os.getenv("POSTGRES_DB", "logindata"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "pwd"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432))
}

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Analytics Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            color: #888;
            font-size: 1rem;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #888;
            font-size: 0.9rem;
        }
        .success { color: #00ff88; }
        .failed { color: #ff4757; }
        .ratio { color: #00d4ff; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            overflow: hidden;
        }
        th, td {
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th {
            background: rgba(0,212,255,0.2);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 1px;
        }
        tr:hover {
            background: rgba(255,255,255,0.05);
        }
        .ratio-bar {
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        .ratio-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00d4ff);
            border-radius: 4px;
        }
        .refresh-info {
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 0.9rem;
        }
        .last-update {
            color: #00d4ff;
        }
        .no-data {
            text-align: center;
            padding: 50px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔐 Login Analytics Dashboard</h1>
            <p class="subtitle">Real-time authentication metrics by region</p>
        </header>
        
        <div class="stats-grid" id="summary-stats">
            <div class="stat-card">
                <div class="stat-value success" id="total-success">-</div>
                <div class="stat-label">Total Successes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value failed" id="total-failed">-</div>
                <div class="stat-label">Total Failures</div>
            </div>
            <div class="stat-card">
                <div class="stat-value ratio" id="overall-ratio">-</div>
                <div class="stat-label">Overall Ratio</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-events">-</div>
                <div class="stat-label">Total Events</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Country</th>
                    <th>Successes</th>
                    <th>Failures</th>
                    <th>Success Rate</th>
                    <th>Ratio Visualization</th>
                </tr>
            </thead>
            <tbody id="analytics-table">
                <tr><td colspan="5" class="no-data">Loading data...</td></tr>
            </tbody>
        </table>
        
        <p class="refresh-info">
            Auto-refreshing every 5 seconds | Last update: <span class="last-update" id="last-update">-</span>
        </p>
    </div>
    
    <script>
        async function fetchAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching analytics:', error);
            }
        }
        
        function updateDashboard(data) {
            // Update summary stats
            document.getElementById('total-success').textContent = data.summary.total_success;
            document.getElementById('total-failed').textContent = data.summary.total_failed;
            document.getElementById('total-events').textContent = data.summary.total_events;
            document.getElementById('overall-ratio').textContent = 
                data.summary.overall_ratio !== null ? data.summary.overall_ratio.toFixed(2) : 'N/A';
            
            // Update table
            const tbody = document.getElementById('analytics-table');
            if (data.by_country.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="no-data">No login events recorded yet</td></tr>';
            } else {
                tbody.innerHTML = data.by_country.map(row => {
                    const total = row.successes + row.failures;
                    const successRate = total > 0 ? ((row.successes / total) * 100).toFixed(1) : 0;
                    return `
                        <tr>
                            <td><strong>${row.country}</strong></td>
                            <td class="success">${row.successes}</td>
                            <td class="failed">${row.failures}</td>
                            <td>${successRate}%</td>
                            <td>
                                <div class="ratio-bar">
                                    <div class="ratio-fill" style="width: ${successRate}%"></div>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update timestamp
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }
        
        // Initial fetch
        fetchAnalytics();
        
        // Auto-refresh every 5 seconds
        setInterval(fetchAnalytics, 5000);
    </script>
</body>
</html>
"""


async def get_analytics():
    """Fetch analytics from PostgreSQL"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get by-country breakdown
        by_country = await conn.fetch("""
            SELECT 
                country,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successes,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failures
            FROM login_events
            GROUP BY country
            ORDER BY (SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) + 
                      SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)) DESC
        """)
        
        # Get summary
        summary = await conn.fetchrow("""
            SELECT 
                COUNT(*) AS total_events,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS total_success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS total_failed
            FROM login_events
        """)
        
        return {
            "by_country": [
                {
                    "country": row["country"],
                    "successes": row["successes"],
                    "failures": row["failures"]
                }
                for row in by_country
            ],
            "summary": {
                "total_events": summary["total_events"],
                "total_success": summary["total_success"],
                "total_failed": summary["total_failed"],
                "overall_ratio": (
                    summary["total_success"] / summary["total_failed"] 
                    if summary["total_failed"] > 0 else None
                )
            }
        }
    finally:
        await conn.close()


@app.route('/')
def dashboard():
    """Serve the analytics dashboard"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics data"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(get_analytics())
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    port = int(os.getenv("ANALYTICS_PORT", 5003))
    print(f"Starting Analytics Dashboard on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
