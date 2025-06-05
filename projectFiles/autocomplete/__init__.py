"""
Autocomplete package for efficient prefix-based university name suggestions.

This package provides a Trie-based autocomplete system that can quickly
suggest university names based on user input prefixes.
"""

from .trie import Trie, TrieNode
from .autocomplete_service import AutocompleteService
from .service_factory import get_autocomplete_service, initialize_autocomplete, initialize_autocomplete_with_all_institutions
from .institution_normalizer import InstitutionNormalizer
from .csv_loader import CSVLoader
from .spell_correction import SpellCorrectionService

__all__ = [
    'Trie',
    'TrieNode',
    'AutocompleteService',
    'get_autocomplete_service',
    'initialize_autocomplete',
    'initialize_autocomplete_with_all_institutions',
    'InstitutionNormalizer',
    'CSVLoader',
    'SpellCorrectionService'
]
