#!/usr/bin/env python3
"""
Test script for spell correction ranking system
"""

from autocomplete.autocomplete_service import AutocompleteService
from spell_check.spell_correction_service import SpellCorrectionService

def test_spell_correction_ranking():
    # Initialize services
    autocomplete = AutocompleteService()
    spell_service = SpellCorrectionService()

    # Load data
    autocomplete.load_data_from_csv_files()
    spell_service.load_dictionary('./spell_check/symspell_dict.txt')

    # Test the ranking with a misspelled query
    result = spell_service.get_corrections_with_debug_info('birzoet', autocomplete.trie, debug=True)

    print('=== Spell Correction Ranking Test ===')
    print(f'Original phrase: {result["original_phrase"]}')
    print(f'Total corrections found: {result["debug_info"]["total_corrections_found"]}')
    print(f'Ranking method: {result["debug_info"]["ranking_method"]}')
    print()

    for item in result['debug_info']['ranking_explanation']:
        print(f'Rank {item["rank"]}: {item["corrected_phrase"]}')
        print(f'  - {item["num_suggestions"]} results in trie')
        print(f'  - {item["corrections_made"]} corrections made')
        print(f'  - {item["ranking_explanation"]}')
        if item['top_suggestion']:
            if isinstance(item['top_suggestion'], dict):
                top_name = item['top_suggestion'].get('full_name', item['top_suggestion'].get('name', 'N/A'))
            else:
                top_name = str(item['top_suggestion'])
            print(f'  - Top suggestion: {top_name}')
        print()

if __name__ == "__main__":
    test_spell_correction_ranking()
