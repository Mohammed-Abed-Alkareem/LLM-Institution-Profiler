"""
Report generator for benchmark results with multiple output formats.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

from .benchmark_config import BenchmarkConfig
from .benchmark_analyzer import BenchmarkAnalyzer


class BenchmarkReporter:
    """
    Generate comprehensive benchmark reports in multiple formats.
    
    Formats supported:
    - JSON: Machine-readable detailed reports
    - HTML: Human-readable dashboard reports
    - CSV: Tabular data for analysis
    - Markdown: Documentation-friendly reports
    """
    
    def __init__(self, config: BenchmarkConfig, analyzer: BenchmarkAnalyzer):
        """Initialize the benchmark reporter."""
        self.config = config
        self.analyzer = analyzer
    
    def generate_dashboard_report(self, format: str = 'html') -> str:
        """
        Generate a comprehensive dashboard report.
        
        Args:
            format: Output format ('html', 'json', 'markdown')
            
        Returns:
            Path to the generated report file
        """
        # Get comprehensive analysis
        analysis = self.analyzer.generate_comprehensive_report()
        
        # Generate report in requested format
        if format == 'html':
            return self._generate_html_dashboard(analysis)
        elif format == 'json':
            return self._generate_json_report(analysis)
        elif format == 'markdown':
            return self._generate_markdown_report(analysis)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_dashboard(self, analysis: Dict[str, Any]) -> str:
        """Generate an HTML dashboard report."""
        report_file = os.path.join(
            self.config.reports_dir,
            self.config.get_report_filename('dashboard', 'html')
        )
        
        html_content = self._create_html_dashboard(analysis)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_file
    
    def _create_html_dashboard(self, analysis: Dict[str, Any]) -> str:
        """Create HTML dashboard content."""
        data_summary = analysis.get('data_summary', {})
        trends = analysis.get('performance_trends', [])
        anomalies = analysis.get('anomalies', [])
        insights = analysis.get('insights', [])
        recommendations = analysis.get('recommendations', [])
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Institution Profiler - Benchmark Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .dashboard {{
            padding: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 0 8px 8px 0;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .trend-item, .anomaly-item, .insight-item {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #ddd;
        }}
        .trend-improving {{ border-left-color: #28a745; }}
        .trend-degrading {{ border-left-color: #dc3545; }}
        .trend-stable {{ border-left-color: #6c757d; }}
        .anomaly-critical {{ border-left-color: #dc3545; background: #fff5f5; }}
        .anomaly-high {{ border-left-color: #fd7e14; background: #fff8f3; }}
        .anomaly-medium {{ border-left-color: #ffc107; background: #fffbf3; }}
        .anomaly-low {{ border-left-color: #17a2b8; background: #f3f9fb; }}
        .insight-critical {{ border-left-color: #dc3545; }}
        .insight-high {{ border-left-color: #fd7e14; }}
        .insight-medium {{ border-left-color: #ffc107; }}
        .insight-low {{ border-left-color: #17a2b8; }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .badge-improving {{ background: #d4edda; color: #155724; }}
        .badge-degrading {{ background: #f8d7da; color: #721c24; }}
        .badge-stable {{ background: #e2e3e5; color: #383d41; }}
        .badge-critical {{ background: #f8d7da; color: #721c24; }}
        .badge-high {{ background: #ffeaa7; color: #856404; }}
        .badge-medium {{ background: #fff3cd; color: #856404; }}
        .badge-low {{ background: #cce5ff; color: #004085; }}
        .no-data {{
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Benchmark Dashboard</h1>
            <p>Generated on {analysis.get('analysis_timestamp', 'Unknown')}</p>
        </div>
        
        <div class="dashboard">
            <!-- Key Metrics -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{data_summary.get('total_operations', 0)}</div>
                    <div class="metric-label">Total Operations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{data_summary.get('success_rate_percent', 0):.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data_summary.get('total_cost_usd', 0):.2f}</div>
                    <div class="metric-label">Total Cost</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{data_summary.get('avg_response_time_seconds', 0):.1f}s</div>
                    <div class="metric-label">Avg Response Time</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{data_summary.get('avg_quality_score', 0):.1%}</div>
                    <div class="metric-label">Avg Quality Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{data_summary.get('data_time_range_days', 0):.0f}</div>
                    <div class="metric-label">Days of Data</div>
                </div>
            </div>
            
            <!-- Performance Trends -->
            <div class="section">
                <h2>📈 Performance Trends</h2>
                {self._generate_trends_html(trends)}
            </div>
            
            <!-- Anomalies -->
            <div class="section">
                <h2>⚠️ Anomalies Detected</h2>
                {self._generate_anomalies_html(anomalies)}
            </div>
            
            <!-- Insights & Recommendations -->
            <div class="section">
                <h2>💡 Performance Insights</h2>
                {self._generate_insights_html(insights)}
            </div>
            
            <!-- Top Recommendations -->
            <div class="section">
                <h2>🎯 Top Recommendations</h2>
                {self._generate_recommendations_html(recommendations)}
            </div>
        </div>
        
        <div class="footer">
            Institution Profiler Benchmark System • Data covers {data_summary.get('analysis_coverage', 'unknown period')}
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_trends_html(self, trends: List[Dict[str, Any]]) -> str:
        """Generate HTML for performance trends."""
        if not trends:
            return '<div class="no-data">No trend data available</div>'
        
        html = ""
        for trend in trends:
            direction = trend.get('trend_direction', 'stable')
            metric_name = trend.get('metric_name', 'Unknown')
            change_percent = trend.get('change_percent', 0)
            confidence = trend.get('confidence', 0)
            data_points = trend.get('data_points', 0)
            
            html += f"""
            <div class="trend-item trend-{direction}">
                <strong>{metric_name.title()}</strong>
                <span class="status-badge badge-{direction}">{direction}</span>
                <br>
                <small>
                    Change: {change_percent:.1f}% • 
                    Confidence: {confidence:.1%} • 
                    Data points: {data_points}
                </small>
            </div>"""
        
        return html
    
    def _generate_anomalies_html(self, anomalies: List[Dict[str, Any]]) -> str:
        """Generate HTML for anomalies."""
        if not anomalies:
            return '<div class="no-data">No anomalies detected</div>'
        
        html = ""
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            description = anomaly.get('description', 'Unknown anomaly')
            affected_metric = anomaly.get('affected_metric', 'Unknown')
            deviation_percent = anomaly.get('deviation_percent', 0)
            
            html += f"""
            <div class="anomaly-item anomaly-{severity}">
                <strong>{affected_metric.title()}</strong>
                <span class="status-badge badge-{severity}">{severity}</span>
                <br>
                {description}
                <br>
                <small>Deviation: {deviation_percent:.1f}%</small>
            </div>"""
        
        return html
    
    def _generate_insights_html(self, insights: List[Dict[str, Any]]) -> str:
        """Generate HTML for insights."""
        if not insights:
            return '<div class="no-data">No insights available</div>'
        
        html = ""
        for insight in insights:
            priority = insight.get('priority', 'low')
            title = insight.get('title', 'Unknown insight')
            description = insight.get('description', '')
            recommendation = insight.get('recommendation', '')
            potential_impact = insight.get('potential_impact', '')
            
            html += f"""
            <div class="insight-item insight-{priority}">
                <strong>{title}</strong>
                <span class="status-badge badge-{priority}">{priority}</span>
                <br>
                {description}
                <br>
                <strong>Recommendation:</strong> {recommendation}
                <br>
                <strong>Impact:</strong> {potential_impact}
            </div>"""
        
        return html
    
    def _generate_recommendations_html(self, recommendations: List[Dict[str, Any]]) -> str:
        """Generate HTML for top recommendations."""
        if not recommendations:
            return '<div class="no-data">No recommendations available</div>'
        
        html = "<ol>"
        for i, rec in enumerate(recommendations, 1):
            title = rec.get('title', 'Unknown recommendation')
            recommendation = rec.get('recommendation', '')
            potential_impact = rec.get('potential_impact', '')
            priority = rec.get('priority', 'low')
            
            html += f"""
            <li style="margin-bottom: 15px;">
                <strong>{title}</strong>
                <span class="status-badge badge-{priority}">{priority}</span>
                <br>
                {recommendation}
                <br>
                <em>Impact: {potential_impact}</em>
            </li>"""
        
        html += "</ol>"
        return html
    
    def _generate_json_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a JSON report."""
        report_file = os.path.join(
            self.config.reports_dir,
            self.config.get_report_filename('dashboard', 'json')
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return report_file
    
    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a Markdown report."""
        report_file = os.path.join(
            self.config.reports_dir,
            self.config.get_report_filename('dashboard', 'md')
        )
        
        markdown_content = self._create_markdown_content(analysis)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return report_file
    
    def _create_markdown_content(self, analysis: Dict[str, Any]) -> str:
        """Create Markdown report content."""
        data_summary = analysis.get('data_summary', {})
        trends = analysis.get('performance_trends', [])
        anomalies = analysis.get('anomalies', [])
        insights = analysis.get('insights', [])
        recommendations = analysis.get('recommendations', [])
        
        markdown = f"""# Institution Profiler - Benchmark Report

**Generated:** {analysis.get('analysis_timestamp', 'Unknown')}

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| Total Operations | {data_summary.get('total_operations', 0)} |
| Success Rate | {data_summary.get('success_rate_percent', 0):.1f}% |
| Total Cost | ${data_summary.get('total_cost_usd', 0):.2f} |
| Avg Response Time | {data_summary.get('avg_response_time_seconds', 0):.1f}s |
| Avg Quality Score | {data_summary.get('avg_quality_score', 0):.1%} |
| Data Time Range | {data_summary.get('data_time_range_days', 0):.0f} days |

## 📈 Performance Trends

"""
        
        if trends:
            for trend in trends:
                direction_emoji = {'improving': '📈', 'degrading': '📉', 'stable': '➡️'}.get(trend.get('trend_direction'), '❓')
                markdown += f"""### {direction_emoji} {trend.get('metric_name', 'Unknown').title()}

- **Direction:** {trend.get('trend_direction', 'stable')}
- **Change:** {trend.get('change_percent', 0):.1f}%
- **Confidence:** {trend.get('confidence', 0):.1%}
- **Data Points:** {trend.get('data_points', 0)}

"""
        else:
            markdown += "*No trend data available*\n\n"
        
        markdown += "## ⚠️ Anomalies Detected\n\n"
        
        if anomalies:
            for anomaly in anomalies:
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(anomaly.get('severity'), '⚪')
                markdown += f"""### {severity_emoji} {anomaly.get('affected_metric', 'Unknown').title()} ({anomaly.get('severity', 'low').title()})

{anomaly.get('description', 'No description')}

**Deviation:** {anomaly.get('deviation_percent', 0):.1f}%

"""
        else:
            markdown += "*No anomalies detected*\n\n"
        
        markdown += "## 💡 Performance Insights\n\n"
        
        if insights:
            for insight in insights:
                priority_emoji = {'critical': '🔥', 'high': '⚡', 'medium': '💡', 'low': '💭'}.get(insight.get('priority'), '💭')
                markdown += f"""### {priority_emoji} {insight.get('title', 'Unknown')} ({insight.get('priority', 'low').title()} Priority)

**Description:** {insight.get('description', '')}

**Recommendation:** {insight.get('recommendation', '')}

**Potential Impact:** {insight.get('potential_impact', '')}

---

"""
        else:
            markdown += "*No insights available*\n\n"
        
        markdown += "## 🎯 Top Recommendations\n\n"
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {'critical': '🔥', 'high': '⚡', 'medium': '💡', 'low': '💭'}.get(rec.get('priority'), '💭')
                markdown += f"""{i}. **{rec.get('title', 'Unknown')}** {priority_emoji}
   
   {rec.get('recommendation', '')}
   
   *Impact: {rec.get('potential_impact', '')}*

"""
        else:
            markdown += "*No recommendations available*\n\n"
        
        markdown += f"""
---

*Report generated by Institution Profiler Benchmark System*  
*Data coverage: {data_summary.get('analysis_coverage', 'unknown period')}*
"""
        
        return markdown
    
    def generate_csv_export(self, data_type: str = 'all') -> str:
        """
        Generate CSV export of benchmark data.
        
        Args:
            data_type: Type of data to export ('all', 'successful', 'failed')
            
        Returns:
            Path to the generated CSV file
        """
        import csv
        
        csv_file = os.path.join(
            self.config.reports_dir,
            self.config.get_report_filename(f'export_{data_type}', 'csv')
        )
        
        # Filter data based on type
        if data_type == 'successful':
            data = [b for b in self.analyzer.benchmarks_data if b.get('success', False)]
        elif data_type == 'failed':
            data = [b for b in self.analyzer.benchmarks_data if not b.get('success', False)]
        else:
            data = self.analyzer.benchmarks_data
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'pipeline_id', 'pipeline_name', 'institution_name', 'institution_type',
                'success', 'timestamp', 'total_time_seconds', 'total_cost_usd',
                'completeness_score', 'cache_hit_rate', 'search_time_seconds',
                'crawling_time_seconds', 'llm_time_seconds', 'google_queries',
                'llm_tokens', 'error_message'
            ])
            
            # Data rows
            for benchmark in data:
                latency = benchmark.get('latency_metrics', {})
                cost = benchmark.get('cost_metrics', {})
                quality = benchmark.get('quality_metrics', {})
                efficiency = benchmark.get('efficiency_metrics', {})
                
                writer.writerow([
                    benchmark.get('pipeline_id', ''),
                    benchmark.get('pipeline_name', ''),
                    benchmark.get('institution_name', ''),
                    benchmark.get('institution_type', ''),
                    benchmark.get('success', False),
                    latency.get('start_timestamp', 0),
                    latency.get('total_pipeline_time_seconds', 0),
                    cost.get('total_cost_usd', 0),
                    quality.get('completeness_score', 0),
                    efficiency.get('cache_hit_rate', 0),
                    latency.get('search_time_seconds', 0),
                    latency.get('crawling_time_seconds', 0),
                    latency.get('llm_processing_time_seconds', 0),
                    cost.get('google_search_queries', 0),
                    cost.get('total_tokens', 0),
                    benchmark.get('error_message', '')
                ])
        
        return csv_file
    
    def generate_performance_comparison_report(self, baseline_date: str, comparison_date: str) -> str:
        """
        Generate a performance comparison report between two time periods.
        
        Args:
            baseline_date: Start date for baseline period (YYYY-MM-DD)
            comparison_date: Start date for comparison period (YYYY-MM-DD)
            
        Returns:
            Path to the generated comparison report
        """
        # This would implement time-based comparison logic
        # For now, returning a placeholder
        
        report_file = os.path.join(
            self.config.reports_dir,
            self.config.get_report_filename('comparison', 'html')
        )
        
        comparison_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Comparison Report</title>
    <style>body {{ font-family: Arial, sans-serif; padding: 20px; }}</style>
</head>
<body>
    <h1>Performance Comparison Report</h1>
    <p>Baseline Period: {baseline_date}</p>
    <p>Comparison Period: {comparison_date}</p>
    <p><em>Detailed comparison functionality to be implemented</em></p>
</body>
</html>"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(comparison_html)
        
        return report_file
