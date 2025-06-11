# -*- coding: utf-8 -*-
"""
Benchmarking-related routes for the Institution Profiler Flask application.
Handles comprehensive performance tracking, metrics, and analysis.
"""
import json
import time
from flask import request, jsonify
from benchmarking.integration import benchmark_context, BenchmarkCategory


def register_benchmark_routes(app, services):
    """Register benchmarking-related routes."""
    benchmarking_manager = services.get('benchmarking')

    @app.route('/benchmarks/pipeline', methods=['GET'])
    def pipeline_benchmarks():
        """
        Get comprehensive pipeline benchmarking statistics.
        """
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        # Redirect to benchmarking system
        return jsonify({
            'success': True,
            'message': 'Pipeline benchmarks available through system',
            'redirect_to': '/benchmarks/metrics',
            'data': benchmarking_manager.get_session_summary()
        })

    @app.route('/benchmarks/overview', methods=['GET'])
    def benchmarks_overview():
        """
        Get a complete overview of all benchmarking data.
        """
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        search_service = services['search']
        
        overview = {
            'system': {
                'session_summary': benchmarking_manager.get_session_summary(),
                'recent_benchmarks': benchmarking_manager.get_recent_benchmarks(10),
                'system_status': 'active'
            },
            'search_service': {
                'cache_stats': search_service.get_stats().get('cache_stats', {}),
                'service_configured': search_service.get_stats().get('service_configured', False)
            },
            'message': 'Using benchmarking system for comprehensive tracking'
        }
        return jsonify(overview)

    @app.route('/benchmarks/status', methods=['GET'])
    def benchmarks_status():
        """Get benchmarking system status and configuration."""
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        try:
            config = benchmarking_manager.config
            summary = benchmarking_manager.get_session_summary()
            
            return jsonify({
                'success': True,
                'status': 'active',
                'configuration': {
                    'cost_tracking': config.enable_cost_tracking,
                    'latency_tracking': config.enable_latency_tracking,
                    'quality_tracking': config.enable_quality_tracking,
                    'efficiency_tracking': config.enable_efficiency_tracking,
                    'auto_reports': config.auto_generate_reports,
                    'retention_days': config.retention_days
                },
                'session_summary': summary,
                'directories': {
                    'benchmarks': config.benchmarks_dir,
                    'reports': config.reports_dir,
                    'test_results': config.test_results_dir
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Status check failed: {str(e)}'
            })

    @app.route('/benchmarks/metrics', methods=['GET'])
    def get_benchmarks_metrics():
        """Get comprehensive metrics from recent benchmarks."""
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        try:
            limit = int(request.args.get('limit', 20))
            category = request.args.get('category', 'all')
            
            recent_benchmarks = benchmarking_manager.get_recent_benchmarks(limit)
            
            # Filter by category if specified
            if category != 'all':
                recent_benchmarks = [
                    b for b in recent_benchmarks 
                    if b.get('category', '').lower() == category.lower()
                ]
            
            # Calculate aggregated metrics
            total_cost = sum(b.get('total_cost', 0) for b in recent_benchmarks)
            avg_latency = (
                sum(b.get('total_latency', 0) for b in recent_benchmarks) / 
                len(recent_benchmarks) if recent_benchmarks else 0
            )
            success_rate = (
                sum(1 for b in recent_benchmarks if b.get('success', False)) /
                len(recent_benchmarks) if recent_benchmarks else 0
            )
            
            # Group by institution type
            by_type = {}
            for benchmark in recent_benchmarks:
                inst_type = benchmark.get('institution_type', 'unknown')
                if inst_type not in by_type:
                    by_type[inst_type] = []
                by_type[inst_type].append(benchmark)
            
            return jsonify({
                'success': True,
                'metrics': {
                    'total_benchmarks': len(recent_benchmarks),
                    'total_cost_usd': round(total_cost, 4),
                    'average_latency_seconds': round(avg_latency, 3),
                    'success_rate_percent': round(success_rate * 100, 2),
                    'by_institution_type': {
                        inst_type: {
                            'count': len(benchmarks),
                            'avg_cost': round(
                                sum(b.get('total_cost', 0) for b in benchmarks) / len(benchmarks), 4
                            ) if benchmarks else 0,
                            'success_rate': round(
                                sum(1 for b in benchmarks if b.get('success', False)) / len(benchmarks) * 100, 2
                            ) if benchmarks else 0
                        }
                        for inst_type, benchmarks in by_type.items()
                    }
                },
                'recent_benchmarks': recent_benchmarks[:10]  # Return top 10 for display
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Metrics retrieval failed: {str(e)}'
            })

    @app.route('/benchmarks/cost-analysis', methods=['GET'])
    def get_cost_analysis():
        """Get detailed cost analysis and optimization recommendations."""
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        try:
            days = int(request.args.get('days', 7))
            
            # Get recent benchmarks for analysis
            recent_benchmarks = benchmarking_manager.get_recent_benchmarks(limit=100)
            
            # Cost breakdown
            total_api_cost = sum(b.get('api_cost', 0) for b in recent_benchmarks)
            total_llm_cost = sum(b.get('llm_cost', 0) for b in recent_benchmarks)
            total_compute_cost = sum(b.get('compute_cost', 0) for b in recent_benchmarks)
            
            # Token usage analysis
            total_input_tokens = sum(b.get('input_tokens', 0) for b in recent_benchmarks)
            total_output_tokens = sum(b.get('output_tokens', 0) for b in recent_benchmarks)
            
            # Cache efficiency analysis
            cache_hits = sum(1 for b in recent_benchmarks if b.get('cache_hit', False))
            cache_efficiency = cache_hits / len(recent_benchmarks) if recent_benchmarks else 0
            
            # Cost optimization recommendations
            recommendations = []
            
            if cache_efficiency < 0.7:
                recommendations.append({
                    'type': 'cache_optimization',
                    'priority': 'high',
                    'message': f'Cache hit rate is {cache_efficiency:.1%}. Consider tuning cache similarity thresholds.',
                    'potential_savings': total_api_cost * (0.7 - cache_efficiency)
                })
            
            if total_llm_cost > total_api_cost * 2:
                recommendations.append({
                    'type': 'llm_optimization',
                    'priority': 'medium',
                    'message': 'LLM costs are high relative to API costs. Consider prompt optimization.',
                    'potential_savings': total_llm_cost * 0.2
                })
            
            return jsonify({
                'success': True,
                'cost_analysis': {
                    'period_days': days,
                    'total_operations': len(recent_benchmarks),
                    'cost_breakdown': {
                        'api_cost_usd': round(total_api_cost, 4),
                        'llm_cost_usd': round(total_llm_cost, 4),
                        'compute_cost_usd': round(total_compute_cost, 4),
                        'total_cost_usd': round(total_api_cost + total_llm_cost + total_compute_cost, 4)
                    },
                    'token_usage': {
                        'total_input_tokens': total_input_tokens,
                        'total_output_tokens': total_output_tokens,
                        'total_tokens': total_input_tokens + total_output_tokens
                    },
                    'efficiency_metrics': {
                        'cache_hit_rate': round(cache_efficiency * 100, 2),
                        'cost_per_operation': round(
                            (total_api_cost + total_llm_cost) / len(recent_benchmarks), 4
                        ) if recent_benchmarks else 0
                    },
                    'optimization_recommendations': recommendations
                }
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Cost analysis failed: {str(e)}'
            })

    @app.route('/benchmarks/performance-report', methods=['GET'])
    def generate_performance_report():
        """Generate a comprehensive performance report."""
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        try:
            format_type = request.args.get('format', 'json')
            include_charts = request.args.get('charts', 'false').lower() == 'true'
            
            # Generate report using the benchmarking manager
            if format_type == 'json':
                report_data = benchmarking_manager.export_benchmarks(format='json')
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported format: {format_type}'
                })
            
            return jsonify({
                'success': True,
                'report_format': format_type,
                'include_charts': include_charts,
                'report_data': json.loads(report_data) if isinstance(report_data, str) else report_data,
                'generated_at': time.time()
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Report generation failed: {str(e)}'
            })

    @app.route('/benchmarks/test', methods=['POST'])
    def run_benchmark_test():        
        """Run a custom benchmark test with specified configuration."""
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        try:
            test_config = request.get_json()
            if not test_config:
                return jsonify({
                    'success': False,
                    'error': 'Test configuration required'
                })
            
            institution_name = test_config.get('institution_name', 'Test Institution')
            institution_type = test_config.get('institution_type', 'general')
            test_type = test_config.get('test_type', 'search')
            iterations = test_config.get('iterations', 1)
            
            results = []
            
            for i in range(iterations):
                # Create a test benchmark
                category = BenchmarkCategory.SEARCH if test_type == 'search' else BenchmarkCategory.PIPELINE
                
                with benchmark_context(category, institution_name, institution_type) as ctx:
                    start_time = time.time()
                    
                    # Simulate test operation based on type
                    if test_type == 'search':
                        # Simulate search operation
                        time.sleep(0.1)  # Simulate processing
                        ctx.record_cost(api_calls=1, service_type="google_search")
                        ctx.record_quality(completeness_score=0.9, accuracy_score=0.85)
                    
                    elif test_type == 'crawling':
                        # Simulate crawling operation
                        time.sleep(0.5)  # Simulate processing
                        ctx.record_content(content_size=10000, word_count=1500)
                        ctx.record_quality(completeness_score=0.8, accuracy_score=0.9)
                    
                    execution_time = time.time() - start_time
                    
                    results.append({
                        'iteration': i + 1,
                        'execution_time': round(execution_time, 3),
                        'success': True
                    })
            
            # Get session summary for results
            summary = benchmarking_manager.get_session_summary()
            
            return jsonify({
                'success': True,
                'test_configuration': test_config,
                'test_results': {
                    'iterations_completed': len(results),
                    'individual_results': results,
                    'average_execution_time': round(
                        sum(r['execution_time'] for r in results) / len(results), 3
                    ),
                    'success_rate': sum(1 for r in results if r['success']) / len(results)
                },
                'session_summary': summary
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Benchmark test failed: {str(e)}'
            })

    @app.route('/benchmarks/export', methods=['GET'])
    def export_benchmark_data():
        """Export comprehensive benchmark data in various formats."""        
        if not benchmarking_manager:
            return jsonify({
                'success': False,
                'error': 'Benchmarking not initialized'
            })
        
        try:
            format_type = request.args.get('format', 'json')
            limit = int(request.args.get('limit', 100))
            
            # Export data
            if format_type == 'json':
                exported_data = benchmarking_manager.export_benchmarks(format='json')
                
                return jsonify({
                    'success': True,
                    'format': format_type,
                    'data': json.loads(exported_data) if isinstance(exported_data, str) else exported_data,
                    'export_timestamp': time.time()
                })
            
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported export format: {format_type}'
                })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Export failed: {str(e)}'
            })
