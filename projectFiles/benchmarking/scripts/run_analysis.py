#!/usr/bin/env python3
"""
Analysis script for the benchmarking system
"""
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project files directory to the path
project_files = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..')
days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
output_format = sys.argv[3] if len(sys.argv) > 3 else 'json'
output_file = sys.argv[4] if len(sys.argv) > 4 else f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{output_format}'

sys.path.insert(0, project_files)

try:
    from benchmarking.integration import get_benchmarking_manager, initialize_benchmarking
    
    print('🔧 Initializing benchmarking system...')
    manager = initialize_benchmarking(project_files)
    
    print(f'📊 Analyzing data from last {days} days...')
    
    # Get benchmark data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # For now, just get session summary
    summary = manager.get_session_summary()
    
    analysis_data = {
        'analysis_date': end_date.isoformat(),
        'period_days': days,
        'format': output_format,
        'session_summary': summary,
        'analysis_notes': 'Basic analysis - detailed historical analysis requires database integration'
    }
    
    if output_format.lower() == 'json':
        output_path = os.path.join(project_files, 'benchmarking', output_file)
        with open(output_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        print(f'📁 Analysis saved to: {output_path}')
    else:
        print('📋 Analysis Results:')
        for key, value in analysis_data.items():
            print(f'   {key}: {value}')
    
    print('✅ Analysis completed successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
