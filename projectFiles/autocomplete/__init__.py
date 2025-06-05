"""
Autocomplete package for efficient prefix-based university name suggestions.

This package provides a Trie-based autocomplete system that can quickly
suggest university names based on user input prefixes.
"""

from .trie import Trie, TrieNode
from .autocomplete_service import AutocompleteService
from .institution_normalizer import InstitutionNormalizer
from .csv_loader import CSVLoader

__all__ = [
    'Trie',
    'TrieNode',
    'AutocompleteService',
    'InstitutionNormalizer',
    'CSVLoader'
]
