"""
Factory functions and singleton management for the autocomplete service.
Provides convenient initialization functions for different use cases.
"""

import os
from autocomplete.autocomplete_service import AutocompleteService
from spell_check import DictionaryManager


# Singleton instance for the autocomplete service
_autocomplete_service = None


def get_autocomplete_service(spell_dict_path=None):
    """
    Get the singleton autocomplete service instance.
    
    Args:
        spell_dict_path (str): Optional path to spell correction dictionary
    
    Returns:
        AutocompleteService: The singleton instance
    """
    global _autocomplete_service
    if _autocomplete_service is None:
        _autocomplete_service = AutocompleteService(spell_dict_path=spell_dict_path)
    return _autocomplete_service


def initialize_autocomplete(csv_configs):
    """
    Initialize the autocomplete service with data from multiple CSV files.
    
    Args:
        csv_configs (list or str): List of CSV configurations or single CSV path for backward compatibility
                                  Each config should be a dict with: path, institution_type, name_column (optional)
    """
    service = get_autocomplete_service()
    
    # Handle backward compatibility - single CSV path
    if isinstance(csv_configs, str):
        csv_configs = [{'path': csv_configs, 'institution_type': 'Edu', 'name_column': 'name'}]
    
    service.load_from_multiple_csvs(csv_configs)
    return service


def initialize_autocomplete_with_all_institutions(base_dir):
    """
    Initialize the autocomplete service with data from multiple CSV files for different institution types.
    
    Args:
        base_dir (str): Base directory path where the spell_check folder is located
    """
    spell_check_dir = os.path.join(base_dir, 'spell_check')
    
    # Path to spell correction dictionary
    spell_dict_path = os.path.join(spell_check_dir, 'symspell_dict.txt')
    
    # Get service with spell correction support
    service = get_autocomplete_service(spell_dict_path=spell_dict_path)
    
    csv_configs = [
        {
            'path': os.path.join(spell_check_dir, 'list_of_univs.csv'),
            'name_column': 'name',
            'institution_type': 'Edu'
        },
        {
            'path': os.path.join(spell_check_dir, 'national-by-name.csv'),
            'name_column': 'NAME',
            'institution_type': 'Fin'
        },
        {
            'path': os.path.join(spell_check_dir, 'thrifts-by-name.csv'),
            'name_column': 'NAME',
            'institution_type': 'Fin'
        },
        {
            'path': os.path.join(spell_check_dir, 'trust-by-name.csv'),
            'name_column': 'NAME',
            'institution_type': 'Fin'
        },
        {
            'path': os.path.join(spell_check_dir, 'world_hospitals_globalsurg.csv'),
            'name_column': 'hospital_name',
            'institution_type': 'Med'
        }
    ]
    
    service = get_autocomplete_service()
    service.load_from_multiple_csvs(csv_configs)
    return service
