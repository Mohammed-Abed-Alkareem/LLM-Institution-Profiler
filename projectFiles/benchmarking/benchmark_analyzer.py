"""
Advanced analyzer for benchmark data with statistical analysis and insights.
"""

import os
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

from .benchmark_config import BenchmarkConfig


@dataclass
class PerformanceTrend:
    """Represents a performance trend over time."""
    metric_name: str
    trend_direction: str  # 'improving', 'degrading', 'stable'
    change_percent: float
    confidence: float
    data_points: int
    time_span_days: int


@dataclass
class Anomaly:
    """Represents a performance anomaly."""
    anomaly_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    affected_metric: str
    timestamp: float
    value: float
    expected_value: float
    deviation_percent: float


@dataclass
class PerformanceInsight:
    """Represents a performance insight or recommendation."""
    insight_type: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    recommendation: str
    potential_impact: str
    supporting_data: Dict[str, Any]


class BenchmarkAnalyzer:
    """
    Advanced analyzer for benchmark data providing:
    - Performance trend analysis
    - Anomaly detection
    - Cost optimization insights
    - Quality improvement recommendations
    - Efficiency bottleneck identification
    """
    
    def __init__(self, config: BenchmarkConfig):
        """Initialize the benchmark analyzer."""
        self.config = config
        self.benchmarks_data = self._load_all_benchmarks()
    
    def _load_all_benchmarks(self) -> List[Dict[str, Any]]:
        """Load all available benchmark data."""
        all_benchmarks = []
        
        try:            # Load main benchmarks
            benchmarks_file = os.path.join(self.config.benchmarks_dir, "all_benchmarks.json")
            if os.path.exists(benchmarks_file):
                with open(benchmarks_file, 'r', encoding='utf-8') as f:
                    benchmark_data = json.load(f)
                    all_benchmarks.extend(benchmark_data)
            
            # Load legacy benchmarks for compatibility
            legacy_file = os.path.join(self.config.benchmarks_dir, "all_benchmarks.json")
            if os.path.exists(legacy_file):
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    legacy_data = json.load(f)
                    # Convert legacy format if needed
                    for item in legacy_data:
                        if 'pipeline_id' not in item:  # Legacy search benchmark
                            all_benchmarks.append(self._convert_legacy_benchmark(item))
        
        except Exception as e:
            print(f"Warning: Could not load benchmark data: {e}")
        
        return all_benchmarks
    
    def _convert_legacy_benchmark(self, legacy_item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy benchmark format to enhanced format."""
        return {
            'pipeline_id': f"legacy_{legacy_item.get('timestamp', 0)}",
            'pipeline_name': 'search_only',
            'institution_name': legacy_item.get('query', 'unknown'),
            'institution_type': legacy_item.get('institution_type', 'unknown'),
            'success': legacy_item.get('success', False),
            'latency_metrics': {
                'search_time_seconds': legacy_item.get('response_time', 0),
                'total_pipeline_time_seconds': legacy_item.get('response_time', 0),
                'start_timestamp': legacy_item.get('timestamp', 0)
            },
            'cost_metrics': {
                'google_search_queries': 1 if legacy_item.get('source') == 'api' else 0,
                'total_cost_usd': 0.005 if legacy_item.get('source') == 'api' else 0
            },
            'efficiency_metrics': {
                'cache_hit_rate': 1.0 if legacy_item.get('source') in ['cache', 'similar_cache'] else 0.0
            },
            'quality_metrics': {
                'completeness_score': 0.8 if legacy_item.get('success', False) else 0.0
            }
        }
    
    # === Trend Analysis ===
    
    def analyze_performance_trends(self, days_back: int = 30) -> List[PerformanceTrend]:
        """
        Analyze performance trends over the specified time period.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            List of performance trends
        """
        cutoff_time = datetime.now().timestamp() - (days_back * 24 * 60 * 60)
        recent_benchmarks = [
            b for b in self.benchmarks_data
            if b.get('latency_metrics', {}).get('start_timestamp', 0) > cutoff_time
        ]
        
        if len(recent_benchmarks) < 5:
            return []
        
        trends = []
        
        # Analyze different metrics
        metrics_to_analyze = [
            ('cost', lambda b: b.get('cost_metrics', {}).get('total_cost_usd', 0)),
            ('latency', lambda b: b.get('latency_metrics', {}).get('total_pipeline_time_seconds', 0)),
            ('quality', lambda b: b.get('quality_metrics', {}).get('completeness_score', 0)),
            ('cache_efficiency', lambda b: b.get('efficiency_metrics', {}).get('cache_hit_rate', 0))
        ]
        
        for metric_name, extractor in metrics_to_analyze:
            trend = self._calculate_trend(recent_benchmarks, metric_name, extractor, days_back)
            if trend:
                trends.append(trend)
        
        return trends
    
    def _calculate_trend(
        self, 
        benchmarks: List[Dict[str, Any]], 
        metric_name: str,
        value_extractor: callable,
        days_back: int
    ) -> Optional[PerformanceTrend]:
        """Calculate trend for a specific metric."""
        try:
            # Extract values with timestamps
            data_points = []
            for benchmark in benchmarks:
                timestamp = benchmark.get('latency_metrics', {}).get('start_timestamp', 0)
                value = value_extractor(benchmark)
                if timestamp > 0 and value >= 0:
                    data_points.append((timestamp, value))
            
            if len(data_points) < 3:
                return None
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x[0])
            
            # Calculate linear regression
            timestamps = [p[0] for p in data_points]
            values = [p[1] for p in data_points]
            
            if len(set(values)) == 1:  # All values are the same
                return PerformanceTrend(
                    metric_name=metric_name,
                    trend_direction='stable',
                    change_percent=0.0,
                    confidence=1.0,
                    data_points=len(data_points),
                    time_span_days=days_back
                )
            
            # Simple linear regression
            n = len(data_points)
            sum_x = sum(timestamps)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in data_points)
            sum_x2 = sum(x * x for x, _ in data_points)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Calculate trend direction and magnitude
            time_span = timestamps[-1] - timestamps[0]
            if time_span > 0:
                total_change = slope * time_span
                avg_value = sum_y / n
                change_percent = (total_change / avg_value * 100) if avg_value != 0 else 0
            else:
                change_percent = 0
            
            # Determine trend direction
            if abs(change_percent) < 5:
                trend_direction = 'stable'
            elif change_percent > 0:
                trend_direction = 'improving' if metric_name in ['quality', 'cache_efficiency'] else 'degrading'
            else:
                trend_direction = 'degrading' if metric_name in ['quality', 'cache_efficiency'] else 'improving'
            
            # Calculate confidence based on R-squared
            mean_y = sum_y / n
            ss_tot = sum((y - mean_y) ** 2 for y in values)
            ss_res = sum((y - (slope * x + (sum_y - slope * sum_x) / n)) ** 2 for x, y in data_points)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return PerformanceTrend(
                metric_name=metric_name,
                trend_direction=trend_direction,
                change_percent=abs(change_percent),
                confidence=max(0, min(1, r_squared)),
                data_points=len(data_points),
                time_span_days=days_back
            )
        
        except Exception as e:
            print(f"Warning: Could not calculate trend for {metric_name}: {e}")
            return None
    
    # === Anomaly Detection ===
    
    def detect_anomalies(self, days_back: int = 7) -> List[Anomaly]:
        """
        Detect performance anomalies in recent data.
        
        Args:
            days_back: Number of days to analyze for anomalies
            
        Returns:
            List of detected anomalies
        """
        cutoff_time = datetime.now().timestamp() - (days_back * 24 * 60 * 60)
        recent_benchmarks = [
            b for b in self.benchmarks_data
            if b.get('latency_metrics', {}).get('start_timestamp', 0) > cutoff_time
        ]
        
        if len(recent_benchmarks) < 3:
            return []
        
        anomalies = []
        
        # Define metrics to check for anomalies
        metrics_config = [
            ('cost', lambda b: b.get('cost_metrics', {}).get('total_cost_usd', 0), 'high'),
            ('latency', lambda b: b.get('latency_metrics', {}).get('total_pipeline_time_seconds', 0), 'high'),
            ('quality', lambda b: b.get('quality_metrics', {}).get('completeness_score', 0), 'low'),
            ('cache_efficiency', lambda b: b.get('efficiency_metrics', {}).get('cache_hit_rate', 0), 'low')
        ]
        
        for metric_name, extractor, anomaly_type in metrics_config:
            metric_anomalies = self._detect_metric_anomalies(
                recent_benchmarks, metric_name, extractor, anomaly_type
            )
            anomalies.extend(metric_anomalies)
        
        return anomalies
    
    def _detect_metric_anomalies(
        self,
        benchmarks: List[Dict[str, Any]],
        metric_name: str,
        value_extractor: callable,
        anomaly_type: str
    ) -> List[Anomaly]:
        """Detect anomalies for a specific metric using statistical methods."""
        anomalies = []
        
        try:
            # Extract values
            values = []
            for benchmark in benchmarks:
                value = value_extractor(benchmark)
                if value >= 0:  # Valid value
                    values.append((
                        benchmark.get('latency_metrics', {}).get('start_timestamp', 0),
                        value,
                        benchmark
                    ))
            
            if len(values) < 3:
                return anomalies
            
            # Calculate statistics
            metric_values = [v[1] for v in values]
            mean_value = statistics.mean(metric_values)
            std_dev = statistics.stdev(metric_values) if len(metric_values) > 1 else 0
            
            if std_dev == 0:
                return anomalies
            
            # Detect outliers using Z-score method
            threshold = 2.0  # 2 standard deviations
            
            for timestamp, value, benchmark in values:
                z_score = abs(value - mean_value) / std_dev
                
                if z_score > threshold:
                    # Determine if this is the type of anomaly we're looking for
                    is_high_anomaly = value > mean_value + threshold * std_dev
                    is_low_anomaly = value < mean_value - threshold * std_dev
                    
                    should_report = (
                        (anomaly_type == 'high' and is_high_anomaly) or
                        (anomaly_type == 'low' and is_low_anomaly)
                    )
                    
                    if should_report:
                        deviation_percent = ((value - mean_value) / mean_value * 100) if mean_value != 0 else 0
                        
                        # Determine severity
                        if z_score > 4:
                            severity = 'critical'
                        elif z_score > 3:
                            severity = 'high'
                        elif z_score > 2.5:
                            severity = 'medium'
                        else:
                            severity = 'low'
                        
                        anomaly = Anomaly(
                            anomaly_type=f"{anomaly_type}_{metric_name}",
                            severity=severity,
                            description=f"Abnormal {metric_name} detected: {value:.3f} (expected ~{mean_value:.3f})",
                            affected_metric=metric_name,
                            timestamp=timestamp,
                            value=value,
                            expected_value=mean_value,
                            deviation_percent=abs(deviation_percent)
                        )
                        
                        anomalies.append(anomaly)
        
        except Exception as e:
            print(f"Warning: Could not detect anomalies for {metric_name}: {e}")
        
        return anomalies
    
    # === Performance Insights ===
    
    def generate_performance_insights(self) -> List[PerformanceInsight]:
        """Generate actionable performance insights and recommendations."""
        insights = []
        
        if not self.benchmarks_data:
            return insights
        
        # Cost optimization insights
        insights.extend(self._analyze_cost_optimization())
        
        # Quality improvement insights
        insights.extend(self._analyze_quality_improvements())
        
        # Efficiency optimization insights
        insights.extend(self._analyze_efficiency_optimization())
        
        # Reliability insights
        insights.extend(self._analyze_reliability_issues())
        
        return insights
    
    def _analyze_cost_optimization(self) -> List[PerformanceInsight]:
        """Analyze cost optimization opportunities."""
        insights = []
        
        try:
            successful_benchmarks = [b for b in self.benchmarks_data if b.get('success', False)]
            
            if not successful_benchmarks:
                return insights
            
            # Analyze API vs cache usage
            api_calls = sum(
                b.get('cost_metrics', {}).get('google_search_queries', 0) 
                for b in successful_benchmarks
            )
            
            cache_hits = sum(
                1 for b in successful_benchmarks 
                if b.get('efficiency_metrics', {}).get('cache_hit_rate', 0) > 0.8
            )
            
            total_operations = len(successful_benchmarks)
            cache_hit_rate = cache_hits / total_operations if total_operations > 0 else 0
            
            if cache_hit_rate < self.config.target_cache_hit_rate:
                potential_savings = api_calls * (self.config.target_cache_hit_rate - cache_hit_rate) * 0.005
                
                insights.append(PerformanceInsight(
                    insight_type='cost_optimization',
                    priority='high' if potential_savings > 5 else 'medium',
                    title='Cache Hit Rate Below Target',
                    description=f"Current cache hit rate is {cache_hit_rate:.1%}, below target of {self.config.target_cache_hit_rate:.1%}",
                    recommendation="Implement better caching strategies or increase cache retention time",
                    potential_impact=f"Could save ${potential_savings:.2f} in API costs",
                    supporting_data={
                        'current_cache_hit_rate': cache_hit_rate,
                        'target_cache_hit_rate': self.config.target_cache_hit_rate,
                        'total_api_calls': api_calls,
                        'potential_savings_usd': potential_savings
                    }
                ))
            
            # Analyze LLM token usage
            total_llm_cost = sum(
                b.get('cost_metrics', {}).get('llm_cost_usd', 0) 
                for b in successful_benchmarks
            )
            
            if total_llm_cost > 0:
                avg_tokens = sum(
                    b.get('cost_metrics', {}).get('total_tokens', 0) 
                    for b in successful_benchmarks
                ) / len(successful_benchmarks)
                
                if avg_tokens > 10000:  # High token usage
                    insights.append(PerformanceInsight(
                        insight_type='cost_optimization',
                        priority='medium',
                        title='High LLM Token Usage',
                        description=f"Average token usage is {avg_tokens:.0f} tokens per operation",
                        recommendation="Consider prompt optimization or using more efficient models for simple tasks",
                        potential_impact="Could reduce LLM costs by 20-40%",
                        supporting_data={
                            'avg_tokens_per_operation': avg_tokens,
                            'total_llm_cost_usd': total_llm_cost
                        }
                    ))
        
        except Exception as e:
            print(f"Warning: Could not analyze cost optimization: {e}")
        
        return insights
    
    def _analyze_quality_improvements(self) -> List[PerformanceInsight]:
        """Analyze quality improvement opportunities."""
        insights = []
        
        try:
            successful_benchmarks = [b for b in self.benchmarks_data if b.get('success', False)]
            
            if not successful_benchmarks:
                return insights
            
            # Analyze completeness scores
            completeness_scores = [
                b.get('quality_metrics', {}).get('completeness_score', 0) 
                for b in successful_benchmarks
            ]
            
            if completeness_scores:
                avg_completeness = sum(completeness_scores) / len(completeness_scores)
                low_quality_count = sum(1 for score in completeness_scores if score < self.config.min_completeness_score)
                
                if avg_completeness < self.config.min_completeness_score:
                    insights.append(PerformanceInsight(
                        insight_type='quality_improvement',
                        priority='high',
                        title='Low Data Completeness',
                        description=f"Average completeness score is {avg_completeness:.1%}, below target of {self.config.min_completeness_score:.1%}",
                        recommendation="Review data extraction prompts and validation logic",
                        potential_impact="Could improve data quality and user satisfaction",
                        supporting_data={
                            'avg_completeness_score': avg_completeness,
                            'target_completeness_score': self.config.min_completeness_score,
                            'low_quality_operations': low_quality_count,
                            'total_operations': len(successful_benchmarks)
                        }
                    ))
                
                # Analyze validation failures
                validation_failures = sum(
                    1 for b in successful_benchmarks 
                    if not b.get('quality_metrics', {}).get('validation_passed', True)
                )
                
                if validation_failures > len(successful_benchmarks) * 0.1:  # More than 10% failures
                    insights.append(PerformanceInsight(
                        insight_type='quality_improvement',
                        priority='medium',
                        title='High Validation Failure Rate',
                        description=f"{validation_failures} out of {len(successful_benchmarks)} operations failed validation",
                        recommendation="Review validation rules and improve data extraction accuracy",
                        potential_impact="Reduce manual review requirements and improve automation",
                        supporting_data={
                            'validation_failures': validation_failures,
                            'total_operations': len(successful_benchmarks),
                            'failure_rate_percent': (validation_failures / len(successful_benchmarks)) * 100
                        }
                    ))
        
        except Exception as e:
            print(f"Warning: Could not analyze quality improvements: {e}")
        
        return insights
    
    def _analyze_efficiency_optimization(self) -> List[PerformanceInsight]:
        """Analyze efficiency optimization opportunities."""
        insights = []
        
        try:
            successful_benchmarks = [b for b in self.benchmarks_data if b.get('success', False)]
            
            if not successful_benchmarks:
                return insights
            
            # Analyze response times
            response_times = [
                b.get('latency_metrics', {}).get('total_pipeline_time_seconds', 0) 
                for b in successful_benchmarks
            ]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                slow_operations = sum(1 for t in response_times if t > self.config.max_response_time_seconds)
                
                if avg_response_time > self.config.max_response_time_seconds:
                    insights.append(PerformanceInsight(
                        insight_type='efficiency_optimization',
                        priority='medium',
                        title='Slow Response Times',
                        description=f"Average response time is {avg_response_time:.1f}s, above target of {self.config.max_response_time_seconds}s",
                        recommendation="Profile bottlenecks and optimize slow components",
                        potential_impact="Improve user experience and system throughput",
                        supporting_data={
                            'avg_response_time_seconds': avg_response_time,
                            'target_response_time_seconds': self.config.max_response_time_seconds,
                            'slow_operations': slow_operations,
                            'total_operations': len(successful_benchmarks)
                        }
                    ))
                
                # Analyze processing phases
                search_times = [
                    b.get('latency_metrics', {}).get('search_time_seconds', 0) 
                    for b in successful_benchmarks
                ]
                crawling_times = [
                    b.get('latency_metrics', {}).get('crawling_time_seconds', 0) 
                    for b in successful_benchmarks
                ]
                llm_times = [
                    b.get('latency_metrics', {}).get('llm_processing_time_seconds', 0) 
                    for b in successful_benchmarks
                ]
                
                # Find bottleneck phase
                avg_search = sum(search_times) / len(search_times) if search_times else 0
                avg_crawling = sum(crawling_times) / len(crawling_times) if crawling_times else 0
                avg_llm = sum(llm_times) / len(llm_times) if llm_times else 0
                
                phases = [
                    ('search', avg_search),
                    ('crawling', avg_crawling),
                    ('llm_processing', avg_llm)
                ]
                
                bottleneck_phase, bottleneck_time = max(phases, key=lambda x: x[1])
                
                if bottleneck_time > avg_response_time * 0.5:  # Phase takes more than 50% of total time
                    insights.append(PerformanceInsight(
                        insight_type='efficiency_optimization',
                        priority='medium',
                        title=f'{bottleneck_phase.title()} Phase Bottleneck',
                        description=f"The {bottleneck_phase} phase takes {bottleneck_time:.1f}s on average ({bottleneck_time/avg_response_time:.1%} of total time)",
                        recommendation=f"Optimize the {bottleneck_phase} phase for better overall performance",
                        potential_impact="Reduce overall processing time and improve throughput",
                        supporting_data={
                            'bottleneck_phase': bottleneck_phase,
                            'bottleneck_time_seconds': bottleneck_time,
                            'percentage_of_total_time': (bottleneck_time / avg_response_time) * 100,
                            'phase_breakdown': dict(phases)
                        }
                    ))
        
        except Exception as e:
            print(f"Warning: Could not analyze efficiency optimization: {e}")
        
        return insights
    
    def _analyze_reliability_issues(self) -> List[PerformanceInsight]:
        """Analyze reliability and error patterns."""
        insights = []
        
        try:
            total_operations = len(self.benchmarks_data)
            if total_operations == 0:
                return insights
            
            failed_operations = [b for b in self.benchmarks_data if not b.get('success', False)]
            failure_rate = len(failed_operations) / total_operations
            
            if failure_rate > 0.05:  # More than 5% failure rate
                insights.append(PerformanceInsight(
                    insight_type='reliability',
                    priority='high' if failure_rate > 0.1 else 'medium',
                    title='High Failure Rate',
                    description=f"System failure rate is {failure_rate:.1%} ({len(failed_operations)} out of {total_operations} operations)",
                    recommendation="Investigate error patterns and improve error handling",
                    potential_impact="Increase system reliability and user satisfaction",
                    supporting_data={
                        'failure_rate_percent': failure_rate * 100,
                        'failed_operations': len(failed_operations),
                        'total_operations': total_operations
                    }
                ))
            
            # Analyze error patterns if available
            error_types = {}
            for operation in failed_operations:
                error = operation.get('error_message', 'Unknown error')
                error_types[error] = error_types.get(error, 0) + 1
            
            if error_types:
                most_common_error = max(error_types.items(), key=lambda x: x[1])
                
                if most_common_error[1] > len(failed_operations) * 0.3:  # Single error type > 30% of failures
                    insights.append(PerformanceInsight(
                        insight_type='reliability',
                        priority='medium',
                        title='Recurring Error Pattern',
                        description=f"Most common error: '{most_common_error[0]}' ({most_common_error[1]} occurrences)",
                        recommendation="Focus on fixing the most common error type first",
                        potential_impact="Could significantly reduce overall failure rate",
                        supporting_data={
                            'most_common_error': most_common_error[0],
                            'occurrences': most_common_error[1],
                            'error_breakdown': error_types
                        }
                    ))
        
        except Exception as e:
            print(f"Warning: Could not analyze reliability issues: {e}")
        
        return insights
    
    # === Summary Reports ===
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report."""
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_summary': self._get_data_summary(),
            'performance_trends': self.analyze_performance_trends(),
            'anomalies': self.detect_anomalies(),
            'insights': self.generate_performance_insights(),
            'recommendations': self._generate_top_recommendations()
        }
        
        return report
    
    def _get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the benchmark data."""
        if not self.benchmarks_data:
            return {'message': 'No benchmark data available'}
        
        successful_operations = [b for b in self.benchmarks_data if b.get('success', False)]
        
        total_cost = sum(
            b.get('cost_metrics', {}).get('total_cost_usd', 0) 
            for b in successful_operations
        )
        
        avg_response_time = sum(
            b.get('latency_metrics', {}).get('total_pipeline_time_seconds', 0) 
            for b in successful_operations
        ) / len(successful_operations) if successful_operations else 0
        
        avg_quality = sum(
            b.get('quality_metrics', {}).get('completeness_score', 0) 
            for b in successful_operations
        ) / len(successful_operations) if successful_operations else 0
        
        # Time range analysis
        timestamps = [
            b.get('latency_metrics', {}).get('start_timestamp', 0) 
            for b in self.benchmarks_data
        ]
        
        time_range_days = 0
        if timestamps:
            min_time = min(t for t in timestamps if t > 0)
            max_time = max(timestamps)
            time_range_days = (max_time - min_time) / (24 * 60 * 60)
        
        return {
            'total_operations': len(self.benchmarks_data),
            'successful_operations': len(successful_operations),
            'success_rate_percent': (len(successful_operations) / len(self.benchmarks_data)) * 100,
            'total_cost_usd': round(total_cost, 4),
            'avg_response_time_seconds': round(avg_response_time, 2),
            'avg_quality_score': round(avg_quality, 3),
            'data_time_range_days': round(time_range_days, 1),
            'analysis_coverage': f"{len(self.benchmarks_data)} operations over {time_range_days:.1f} days"
        }
    
    def _generate_top_recommendations(self) -> List[Dict[str, Any]]:
        """Generate top recommendations based on all insights."""
        insights = self.generate_performance_insights()
        
        # Sort insights by priority and potential impact
        priority_scores = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        
        sorted_insights = sorted(
            insights,
            key=lambda i: priority_scores.get(i.priority, 0),
            reverse=True
        )
        
        # Return top 5 recommendations
        return [
            {
                'title': insight.title,
                'priority': insight.priority,
                'recommendation': insight.recommendation,
                'potential_impact': insight.potential_impact,
                'insight_type': insight.insight_type
            }
            for insight in sorted_insights[:5]
        ]
