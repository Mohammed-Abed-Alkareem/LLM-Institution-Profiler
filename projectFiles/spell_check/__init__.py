"""
Spell check module for institution name correction.
Provides spell checking and correction services for institution names.
"""

from .spell_correction_service import SpellCorrectionService
from .dictionary_manager import DictionaryManager

__all__ = [
    'SpellCorrectionService',
    'DictionaryManager'
]
