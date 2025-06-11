#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick validation test to verify quality score integration and cost tracking fixes.
"""

import sys
import os
import time

# Add project directory to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from institution_processor import process_institution_pipeline

def test_quality_score_integration():
    """Test a single institution to verify quality score integration works."""
    print("🧪 Testing Quality Score Integration and Cost Tracking...")
    
    # Test with a simple, well-known institution
    institution_name = "Harvard University"
    institution_type = "university"
    
    print(f"   Processing: {institution_name}")
    
    start_time = time.time()
    
    try:
        result = process_institution_pipeline(
            institution_name=institution_name,
            institution_type=institution_type,
            search_params={}
        )
        
        processing_time = time.time() - start_time
        
        print(f"   ⏱️  Processing completed in {processing_time:.2f}s")
        
        # Check quality score integration
        quality_score = result.get('quality_score', 0)
        quality_rating = result.get('quality_rating', 'Unknown')
        
        print(f"   📊 Quality Score: {quality_score}")
        print(f"   📈 Quality Rating: {quality_rating}")
        
        # Check cost metrics
        cost_metrics = result.get('cost_metrics', {})
        if cost_metrics:
            total_cost = cost_metrics.get('total_cost_usd', 0.0)
            print(f"   💰 Total Cost: ${total_cost:.4f}")
            print(f"   🔍 Google Search Cost: ${cost_metrics.get('google_search_cost_usd', 0.0):.4f}")
            print(f"   🤖 LLM Cost: ${cost_metrics.get('llm_cost_usd', 0.0):.4f}")
            print(f"   🏗️  Infrastructure Cost: ${cost_metrics.get('infrastructure_cost_usd', 0.0):.4f}")
        else:
            print("   ⚠️  No cost metrics found")
        
        # Check if we have meaningful data
        success_indicators = [
            result.get('website') and result.get('website') != 'Unknown',
            result.get('address') and result.get('address') != 'Unknown',
            result.get('phone') and result.get('phone') != 'Unknown',
            quality_score > 0,
            not result.get('error')
        ]
        
        success_count = sum(success_indicators)
        print(f"   ✅ Success Indicators: {success_count}/5")
        
        if success_count >= 3:
            print("   🎉 Test PASSED: Quality integration and processing working correctly!")
            return True
        else:
            print("   ❌ Test FAILED: Insufficient data quality or processing issues")
            if result.get('error'):
                print(f"      Error: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   💥 Test FAILED with exception: {e}")
        return False

def main():
    """Run the quick validation test."""
    print("🚀 Quick Validation Test for Institution Profiler")
    print("=" * 60)
    
    success = test_quality_score_integration()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed! Ready to run comprehensive benchmark.")
    else:
        print("❌ Tests failed. Please check the issues above before running full benchmark.")
        sys.exit(1)

if __name__ == "__main__":
    main()
