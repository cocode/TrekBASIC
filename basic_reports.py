
def print_coverage_report(coverage, program, lines):
    total_lines = len(program)
    total_stmts = 0
    for p in program:
        total_stmts += len(p.stmts)

    if total_stmts == 0:
        print("Program is empty.")
        return

    executed_lines = len(coverage)
    executed_stmts = 0
    for s in coverage.values():
        executed_stmts += len(s)
    column = 20
    print("Code Coverage Report")
    print(F'            {"Total":>{column}} {"Executed":>{column}} {"Percent":>{column}}')
    print \
        (F"Lines.....: {total_lines:{column}} {executed_lines:{column}} {100 * executed_lines / total_lines:{column}.1f}%")
    print \
        (F"Statements: {total_stmts:{column}} {executed_stmts:{column}} {100 * executed_stmts / total_stmts:{column}.1f}%")

def generate_html_coverage_report(coverage, program, filename="coverage_report.html"):
    """
    Generate a beautiful HTML coverage report with pie charts and visual code display

    :param coverage: Coverage data dict {line_number: set of executed stmt indices}
    :param program: Program object containing all program lines
    :param filename: Output HTML filename
    """
    import html
    from datetime import datetime

    # Calculate coverage statistics
    total_lines = len(program)
    total_stmts = 0
    for p in program:
        total_stmts += len(p.stmts)

    if total_stmts == 0:
        print("Program is empty.")
        return

    executed_lines = len(coverage)
    executed_stmts = 0
    for s in coverage.values():
        executed_stmts += len(s)

    line_coverage_percent = (executed_lines / total_lines) * 100
    stmt_coverage_percent = (executed_stmts / total_stmts) * 100

    # Collect uncovered lines data
    uncovered_lines = []
    partially_covered_lines = []

    for line in program:
        if line.line not in coverage:
            # Completely uncovered line
            stmt_indices = [i for i, j in enumerate(line.stmts)]
            uncovered_lines.append({
                'line_number': line.line,
                'source': line.source,
                'uncovered_stmts': stmt_indices,
                'total_stmts': len(line.stmts)
            })
        else:
            # Check if partially covered
            stmt_indices = [i for i, j in enumerate(line.stmts)]
            uncovered_stmts = [i for i, j in enumerate(line.stmts) if i not in coverage[line.line]]
            if len(uncovered_stmts) > 0:
                partially_covered_lines.append({
                    'line_number': line.line,
                    'source': line.source,
                    'uncovered_stmts': uncovered_stmts,
                    'total_stmts': len(line.stmts)
                })

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BASIC Code Coverage Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            padding: 30px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .header h1 {{
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }}
        .header .timestamp {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .stats-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }}
        .stat-card h3 {{
            margin: 0;
            color: #333;
            font-size: 1.2em;
        }}
        .stat-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
            margin: 10px 0;
        }}
        .stat-card .detail {{
            color: #666;
            font-size: 0.9em;
        }}
        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .chart-card h3 {{
            margin: 0 0 20px 0;
            color: #333;
        }}
        .chart-wrapper {{
            position: relative;
            height: 300px;
            margin: 0 auto;
        }}
        .uncovered-section {{
            margin-top: 30px;
        }}
        .uncovered-section h2 {{
            color: #333;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        .code-block {{
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            margin: 10px 0;
            overflow-x: auto;
        }}
        .code-header {{
            background: #e9ecef;
            padding: 8px 15px;
            border-bottom: 1px solid #e0e0e0;
            font-weight: bold;
            color: #495057;
        }}
        .code-line {{
            padding: 8px 15px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: #fff;
            border-left: 4px solid #dc3545;
        }}
        .code-line.partial {{
            border-left: 4px solid #ffc107;
        }}
        .uncovered-stmt {{
            background: #ffe6e6;
            padding: 2px 4px;
            border-radius: 3px;
            margin: 0 2px;
            font-weight: bold;
        }}
        .coverage-excellent {{ border-left-color: #28a745; }}
        .coverage-good {{ border-left-color: #007bff; }}
        .coverage-fair {{ border-left-color: #ffc107; }}
        .coverage-poor {{ border-left-color: #dc3545; }}
        .program-listing {{
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            max-height: 600px;
            overflow-y: auto;
            margin: 20px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        .program-line {{
            display: flex;
            align-items: center;
            padding: 4px 0;
            border-bottom: 1px solid #f0f0f0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            transition: background-color 0.2s ease;
        }}
        .program-line:hover {{
            background-color: rgba(0,0,0,0.05);
        }}
        .stmt-covered {{
            background-color: #d4edda;
            padding: 2px 4px;
            border-radius: 3px;
            margin: 0 2px;
            border: 1px solid #28a745;
            display: inline-block;
        }}
        .stmt-uncovered {{
            background-color: #f8d7da;
            padding: 2px 4px;
            border-radius: 3px;
            margin: 0 2px;
            border: 1px solid #dc3545;
            display: inline-block;
        }}
        .program-line {{
            border-left: 4px solid #e0e0e0;
        }}
        .line-number {{
            min-width: 60px;
            padding: 0 15px;
            text-align: right;
            color: #666;
            font-weight: bold;
            background-color: rgba(255,255,255,0.7);
            border-right: 1px solid #ddd;
        }}
        .line-code {{
            padding: 0 15px;
            flex: 1;
            white-space: pre-wrap;
            word-break: break-all;
        }}

        @media (max-width: 768px) {{
            .charts-container {{
                grid-template-columns: 1fr;
            }}
            .stats-overview {{
                grid-template-columns: 1fr;
            }}
            .program-listing {{
                max-height: 400px;
            }}
            .line-number {{
                min-width: 50px;
                padding: 0 10px;
            }}
            .line-code {{
                padding: 0 10px;
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 BASIC Code Coverage Report</h1>
            <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>

        <div class="stats-overview">
            <div class="stat-card coverage-{'excellent' if line_coverage_percent >= 90 else 'good' if line_coverage_percent >= 75 else 'fair' if line_coverage_percent >= 50 else 'poor'}">
                <h3>Line Coverage</h3>
                <div class="number">{line_coverage_percent:.1f}%</div>
                <div class="detail">{executed_lines} of {total_lines} lines</div>
            </div>
            <div class="stat-card coverage-{'excellent' if stmt_coverage_percent >= 90 else 'good' if stmt_coverage_percent >= 75 else 'fair' if stmt_coverage_percent >= 50 else 'poor'}">
                <h3>Statement Coverage</h3>
                <div class="number">{stmt_coverage_percent:.1f}%</div>
                <div class="detail">{executed_stmts} of {total_stmts} statements</div>
            </div>
        </div>

        <div class="charts-container">
            <div class="chart-card">
                <h3>Line Coverage</h3>
                <div class="chart-wrapper">
                    <canvas id="lineChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>Statement Coverage</h3>
                <div class="chart-wrapper">
                    <canvas id="statementChart"></canvas>
                </div>
            </div>
                 </div>

         <div class="uncovered-section">
             <h2>📋 Complete Program Listing</h2>
             <p>Full program with statement-level coverage visualization: <span style="background-color: #d4edda; padding: 2px 4px; border-radius: 3px;">Covered Statement</span> | <span style="background-color: #f8d7da; padding: 2px 4px; border-radius: 3px;">Uncovered Statement</span></p>

             <div class="program-listing">
                 {"".join([f'''
                 <div class="program-line">
                     <div class="line-number">{line.line}</div>
                     <div class="line-code">{"".join([f'<span class="stmt-{("covered" if line.line in coverage and i in coverage[line.line] else "uncovered")}">{html.escape(str(stmt))}</span>{" : " if i < len(line.stmts) - 1 else ""}' for i, stmt in enumerate(line.stmts)])}</div>
                 </div>
                 ''' for line in program])}
             </div>
         </div>


    </div>

    <script>
        // Line Coverage Chart
        const lineCtx = document.getElementById('lineChart').getContext('2d');
        const lineChart = new Chart(lineCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Covered', 'Uncovered'],
                datasets: [{{
                    data: [{executed_lines}, {total_lines - executed_lines}],
                    backgroundColor: ['#28a745', '#dc3545'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = {total_lines};
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${{label}}: ${{value}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Statement Coverage Chart
        const stmtCtx = document.getElementById('statementChart').getContext('2d');
        const statementChart = new Chart(stmtCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Covered', 'Uncovered'],
                datasets: [{{
                    data: [{executed_stmts}, {total_stmts - executed_stmts}],
                    backgroundColor: ['#007bff', '#ffc107'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = {total_stmts};
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${{label}}: ${{value}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    # Write HTML file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print()
    print(f"HTML coverage report generated: {filename}")
    print(f"Line coverage: {line_coverage_percent:.1f}% ({executed_lines}/{total_lines})")
    print(f"Statement coverage: {stmt_coverage_percent:.1f}% ({executed_stmts}/{total_stmts})")
