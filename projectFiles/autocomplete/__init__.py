"""
Autocomplete package for efficient prefix-based university name suggestions.

This package provides a Trie-based autocomplete system that can quickly
suggest university names based on user input prefixes.
"""

from .trie import Trie, TrieNode
from .autocomplete_service import AutocompleteService, get_autocomplete_service, initialize_autocomplete, initialize_autocomplete_with_all_institutions

__all__ = [
    'Trie',
    'TrieNode', 
    'AutocompleteService',
    'get_autocomplete_service',
    'initialize_autocomplete',
    'initialize_autocomplete_with_all_institutions'
]
