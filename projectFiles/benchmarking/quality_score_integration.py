# -*- coding: utf-8 -*-
"""
Enhanced Quality Score Integration for Benchmarking

This module integrates the calculate_information_quality_score function from core routes
into the benchmarking system for consistent quality scoring across all operations.
"""

import sys
import os

# Add the project directory to path for imports
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from typing import Dict, Any, Tuple, Optional
from quality_score_calculator import calculate_information_quality_score


class QualityScoreIntegrator:
    """
    Integrates the core quality scoring system with benchmarking operations.
    
    This class provides methods to calculate quality scores using the same
    algorithm used in the web interface, ensuring consistency across all
    benchmarking operations.
    """
    
    def __init__(self):
        self.last_quality_details = {}
    
    def calculate_enhanced_quality_metrics(
        self, 
        institution_data: Dict[str, Any],
        benchmark_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality metrics using the core quality score function.
        
        Args:
            institution_data: The processed institution data
            benchmark_context: Additional context for benchmarking
            
        Returns:
            Enhanced quality metrics including core quality score and additional metrics
        """
        if not institution_data:
            return self._empty_quality_metrics()
        
        # Calculate core quality score using the same function as web interface
        try:
            quality_score, quality_rating, quality_details = calculate_information_quality_score(institution_data)
            self.last_quality_details = quality_details
        except Exception as e:
            print(f"Warning: Could not calculate core quality score: {e}")
            quality_score, quality_rating, quality_details = 0, "Error", {}
        
        # Calculate additional benchmarking-specific metrics
        additional_metrics = self._calculate_benchmarking_metrics(institution_data)
        
        # Calculate field-level completeness
        field_metrics = self._calculate_field_level_metrics(institution_data)
        
        # Calculate crawler and pipeline success metrics
        pipeline_metrics = self._calculate_pipeline_metrics(institution_data)
          # Combine all metrics
        enhanced_metrics = {
            # Core quality metrics (from web interface)
            'quality_score': quality_score,  # Primary quality score for pipeline compatibility
            'quality_rating': quality_rating,  # Primary quality rating for pipeline compatibility
            'quality_details': quality_details,  # Primary quality details for pipeline compatibility
            'core_quality_score': quality_score,
            'core_quality_rating': quality_rating,
            'core_quality_details': quality_details,
            
            # Benchmarking-specific metrics
            'completeness_score': quality_details.get('completion_percentage', 0) / 100.0,
            'fields_extracted': quality_details.get('populated_fields', 0),
            'fields_requested': quality_details.get('total_fields', 97),  # Default STRUCTURED_INFO_KEYS count
            
            # Enhanced accuracy and validation metrics
            'accuracy_score': additional_metrics.get('accuracy_score', 0.0),
            'precision_score': additional_metrics.get('precision_score', 0.0),
            'recall_score': additional_metrics.get('recall_score', 0.0),
            'f1_score': additional_metrics.get('f1_score', 0.0),
            
            # Content quality metrics
            'content_quality_score': additional_metrics.get('content_quality_score', 0.8),
            'relevance_score': additional_metrics.get('relevance_score', 0.0),
            'coherence_score': additional_metrics.get('coherence_score', 0.0),
            
            # Validation results
            'validation_passed': quality_score >= 50,  # Pass threshold
            'validation_errors': self._get_validation_errors(quality_score, quality_details),
            'confidence_scores': additional_metrics.get('confidence_scores', {}),
            
            # Source quality metrics
            'source_authority_score': additional_metrics.get('source_authority_score', 0.0),
            'source_freshness_score': additional_metrics.get('source_freshness_score', 0.0),
            'source_credibility_score': additional_metrics.get('source_credibility_score', 0.0),
            
            # Field-level analysis
            'critical_fields_completion': field_metrics.get('critical_completion', 0.0),
            'important_fields_completion': field_metrics.get('important_completion', 0.0),
            'specialized_fields_completion': field_metrics.get('specialized_completion', 0.0),
            
            # Pipeline success metrics
            'search_success': pipeline_metrics.get('search_success', False),
            'crawling_success': pipeline_metrics.get('crawling_success', False),
            'extraction_success': pipeline_metrics.get('extraction_success', False),
            'overall_pipeline_success': pipeline_metrics.get('overall_success', False)        }
        
        return enhanced_metrics
    
    def _empty_quality_metrics(self) -> Dict[str, Any]:
        """Return empty quality metrics for failed operations."""
        return {
            'quality_score': 0,  # Primary quality score for pipeline compatibility
            'quality_rating': 'No Data',  # Primary quality rating for pipeline compatibility
            'quality_details': {},  # Primary quality details for pipeline compatibility
            'core_quality_score': 0,
            'core_quality_rating': 'No Data',
            'core_quality_details': {},
            'completeness_score': 0.0,
            'fields_extracted': 0,
            'fields_requested': 97,
            'accuracy_score': 0.0,
            'precision_score': 0.0,
            'recall_score': 0.0,
            'f1_score': 0.0,
            'content_quality_score': 0.0,
            'relevance_score': 0.0,
            'coherence_score': 0.0,
            'validation_passed': False,
            'validation_errors': ['No data available'],
            'confidence_scores': {},
            'source_authority_score': 0.0,
            'source_freshness_score': 0.0,
            'source_credibility_score': 0.0,
            'critical_fields_completion': 0.0,
            'important_fields_completion': 0.0,
            'specialized_fields_completion': 0.0,
            'search_success': False,
            'crawling_success': False,
            'extraction_success': False,
            'overall_pipeline_success': False
        }
    
    def _calculate_benchmarking_metrics(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional metrics specific to benchmarking."""
        metrics = {}
        
        # Content quality based on available rich content
        content_score = 0.8  # Base score
        if institution_data.get('images_found'):
            content_score += 0.1
        if institution_data.get('logos_found'):
            content_score += 0.1
        metrics['content_quality_score'] = min(content_score, 1.0)
        
        # Relevance score based on institution type detection accuracy
        institution_type = institution_data.get('type', '').lower()
        entity_type = institution_data.get('entity_type', '').lower()
        if institution_type == entity_type and institution_type != 'unknown':
            metrics['relevance_score'] = 0.9
        elif institution_type or entity_type:
            metrics['relevance_score'] = 0.6
        else:
            metrics['relevance_score'] = 0.3
        
        # Source authority based on website presence and crawling success
        if institution_data.get('website'):
            metrics['source_authority_score'] = 0.7
            crawl_summary = institution_data.get('crawl_summary', {})
            if crawl_summary.get('success_rate', 0) > 0.5:
                metrics['source_authority_score'] = 0.9
        else:
            metrics['source_authority_score'] = 0.3
        
        # Freshness based on cache hit rates (lower cache hit = fresher data)
        crawl_summary = institution_data.get('crawl_summary', {})
        cache_hit_rate = crawl_summary.get('cache_hit_rate', 1.0)
        metrics['source_freshness_score'] = 1.0 - cache_hit_rate
        
        # Credibility based on multiple sources and validation
        credibility = 0.5  # Base credibility
        if institution_data.get('crawling_links') and len(institution_data.get('crawling_links', [])) > 3:
            credibility += 0.2
        if institution_data.get('social_media_links'):
            credibility += 0.1
        if institution_data.get('documents_found'):
            credibility += 0.1
        metrics['source_credibility_score'] = min(credibility, 1.0)
        
        # Confidence scores for different aspects
        metrics['confidence_scores'] = {
            'data_extraction': 0.8 if institution_data.get('extraction_metrics', {}).get('success') else 0.3,
            'search_accuracy': 0.9 if institution_data.get('website') else 0.5,
            'content_relevance': metrics.get('relevance_score', 0.5),
            'pipeline_success': 0.9 if institution_data.get('processing_phases', {}).get('extraction', {}).get('success') else 0.4
        }
        
        return metrics
    
    def _calculate_field_level_metrics(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate completion rates for different field categories."""
        # Get the quality details from the last calculation
        quality_details = self.last_quality_details
        
        if not quality_details:
            return {
                'critical_completion': 0.0,
                'important_completion': 0.0,
                'specialized_completion': 0.0
            }
        
        # Extract completion rates from category breakdown
        category_breakdown = quality_details.get('category_breakdown', {})
        
        return {
            'critical_completion': category_breakdown.get('critical', {}).get('completion_rate', 0) / 100.0,
            'important_completion': category_breakdown.get('important', {}).get('completion_rate', 0) / 100.0,
            'specialized_completion': category_breakdown.get('specialized', {}).get('completion_rate', 0) / 100.0
        }
    
    def _calculate_pipeline_metrics(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate pipeline-specific success metrics."""
        processing_phases = institution_data.get('processing_phases', {})
        
        search_success = processing_phases.get('search', {}).get('success', False)
        crawling_success = processing_phases.get('crawling', {}).get('success', False)
        extraction_success = processing_phases.get('extraction', {}).get('success', False)
        
        # Overall success requires at least search and one other phase
        overall_success = search_success and (crawling_success or extraction_success)
        
        return {
            'search_success': search_success,
            'crawling_success': crawling_success,
            'extraction_success': extraction_success,
            'overall_success': overall_success
        }
    
    def _get_validation_errors(self, quality_score: float, quality_details: Dict[str, Any]) -> list:
        """Generate validation errors based on quality analysis."""
        errors = []
        
        if quality_score < 20:
            errors.append("Very low quality score")
        elif quality_score < 50:
            errors.append("Low quality score")
        
        # Check critical fields
        critical_completion = quality_details.get('category_breakdown', {}).get('critical', {}).get('completion_rate', 0)
        if critical_completion < 60:
            errors.append("Critical fields incomplete")
        
        # Check for missing essential information
        if quality_details.get('critical_fields_populated', 0) < 3:
            errors.append("Missing essential identification information")
        
        return errors if errors else []

    def get_output_type_metrics(self, institution_data: Dict[str, Any], output_type: str) -> Dict[str, Any]:
        """
        Calculate metrics specific to different output types (json, structured, comprehensive).
        
        Args:
            institution_data: The processed institution data
            output_type: The type of output format being tested
            
        Returns:
            Metrics specific to the output type
        """
        base_metrics = self.calculate_enhanced_quality_metrics(institution_data)
        
        # Add output-type specific metrics
        output_metrics = {
            'output_type': output_type,
            'data_size_estimate': self._estimate_output_size(institution_data, output_type),
            'serialization_complexity': self._calculate_serialization_complexity(institution_data, output_type),
            'information_density': self._calculate_information_density(institution_data, output_type)
        }
        
        # Combine with base metrics
        base_metrics.update(output_metrics)
        return base_metrics
    
    def _estimate_output_size(self, institution_data: Dict[str, Any], output_type: str) -> int:
        """Estimate the output size in bytes for different formats."""
        import json
        
        try:
            if output_type == 'json':
                return len(json.dumps(institution_data, indent=2).encode('utf-8'))
            elif output_type == 'structured':
                # Simplified structured format
                structured_data = {k: v for k, v in institution_data.items() 
                                 if not k.startswith('_') and v not in [None, '', [], {}]}
                return len(json.dumps(structured_data).encode('utf-8'))
            elif output_type == 'comprehensive':
                # Full format with all metadata
                return len(json.dumps(institution_data, indent=4).encode('utf-8'))
            else:
                return len(str(institution_data).encode('utf-8'))
        except Exception:
            return 0
    
    def _calculate_serialization_complexity(self, institution_data: Dict[str, Any], output_type: str) -> float:
        """Calculate the complexity of serializing the data."""
        def count_nested_structures(obj, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return 0
            
            count = 0
            if isinstance(obj, dict):
                count += 1
                for value in obj.values():
                    count += count_nested_structures(value, depth + 1)
            elif isinstance(obj, list):
                count += 1
                for item in obj:
                    count += count_nested_structures(item, depth + 1)
            
            return count
        
        nested_count = count_nested_structures(institution_data)
        total_keys = len(str(institution_data).split('"'))
        
        # Normalize complexity score (0-1 range)
        complexity = min((nested_count + total_keys) / 1000.0, 1.0)
        
        # Adjust based on output type
        if output_type == 'comprehensive':
            complexity *= 1.2  # More complex
        elif output_type == 'structured':
            complexity *= 0.8  # Less complex
        
        return min(complexity, 1.0)
    
    def _calculate_information_density(self, institution_data: Dict[str, Any], output_type: str) -> float:
        """Calculate how much useful information is packed into the output."""
        from extraction_logic import STRUCTURED_INFO_KEYS
        
        total_fields = len(STRUCTURED_INFO_KEYS)
        populated_fields = sum(1 for key in STRUCTURED_INFO_KEYS 
                             if institution_data.get(key) not in [None, '', [], {}])
        
        base_density = populated_fields / total_fields if total_fields > 0 else 0
        
        # Adjust for additional content
        bonus_content = 0
        if institution_data.get('images_found'):
            bonus_content += 0.1
        if institution_data.get('logos_found'):
            bonus_content += 0.1
        if institution_data.get('social_media_links'):
            bonus_content += 0.05
        if institution_data.get('documents_found'):
            bonus_content += 0.05
        
        final_density = min(base_density + bonus_content, 1.0)
        
        # Output type doesn't significantly affect information density
        # but comprehensive format might have slightly more metadata
        if output_type == 'comprehensive':
            final_density *= 1.05
        
        return min(final_density, 1.0)


# Global instance for easy import
quality_integrator = QualityScoreIntegrator()
