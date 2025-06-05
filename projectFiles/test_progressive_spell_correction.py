#!/usr/bin/env python3
"""
Test the enhanced spell correction with progressive edit distance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service_factory import initialize_autocomplete_with_all_institutions

def test_progressive_spell_correction():
    """Test the enhanced spell correction system"""
    print("Testing Progressive Spell Correction System")
    print("=" * 50)
    
    # Initialize services with all institution data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    autocomplete_service = initialize_autocomplete_with_all_institutions(base_dir)
    
    # Test cases that should benefit from progressive edit distance
    test_cases = [
        "bakk",           # Should correct to "bank" and show "bank of..." suggestions
        "universtiy",     # Should correct to "university" 
        "colege",         # Should correct to "college"
        "hosptial",       # Should correct to "hospital"
        "institue",       # Should correct to "institute"
        "birzoet",        # Should correct to "birzeit"
        "harvrd",         # Should correct to "harvard"
        "standford",      # Should correct to "stanford" 
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: '{test_case}'")
        print("-" * 30)
        
        result = autocomplete_service.get_suggestions(test_case, max_suggestions=5, include_spell_correction=True)
        
        print(f"Source: {result.get('source', 'unknown')}")
        
        if result.get('source') == 'spell_correction':
            suggestions = result.get('suggestions', [])
            print(f"Found {len(suggestions)} spell correction suggestions:")
            
            for i, suggestion in enumerate(suggestions, 1):
                corrected_query = suggestion.get('corrected_query', 'N/A')
                full_name = suggestion.get('full_name', 'N/A')
                inst_type = suggestion.get('institution_type', 'N/A')
                
                print(f"  {i}. Corrected: '{corrected_query}' → {full_name} ({inst_type})")
                
                # Show corrections made
                corrections = suggestion.get('corrections', [])
                if corrections:
                    for corr in corrections:
                        print(f"      - '{corr['original']}' → '{corr['corrected']}' (distance: {corr['distance']})")
        else:
            suggestions = result.get('suggestions', [])
            print(f"Found {len(suggestions)} regular autocomplete suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                if isinstance(suggestion, dict):
                    name = suggestion.get('full_name', suggestion.get('name', str(suggestion)))
                    inst_type = suggestion.get('type', suggestion.get('institution_type', 'N/A'))
                    print(f"  {i}. {name} ({inst_type})")
                else:
                    print(f"  {i}. {suggestion}")
        
        print()

if __name__ == "__main__":
    test_progressive_spell_correction()
