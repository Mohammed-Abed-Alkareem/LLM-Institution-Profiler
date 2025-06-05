"""
Smart spell correction service for handling "did you mean" functionality.
Focuses exclusively on smart corrections that validate against actual institution names.
Uses SymSpell for finding closest matches and validates them against the institution trie.
"""

from symspellpy import SymSpell, Verbosity
import os
from .dictionary_manager import DictionaryManager


class SpellCorrectionService:
    """
    Smart spell correction service for institution names.
    
    This service focuses exclusively on smart corrections - it generates candidate
    corrections using SymSpell and validates them against actual institution names
    in the trie to ensure all suggestions are real institutions.
    
    Key features:
    - Corrects individual words in phrases
    - Tries common institution terms (university, college, etc.)
    - Validates all corrections against actual institution data
    - Only returns corrections that match real institutions
    """
    
    def __init__(self, dictionary_path=None, max_edit_distance=2):
        """
        Initialize the spell correction service.
        
        Args:
            dictionary_path (str): Path to SymSpell dictionary file
            max_edit_distance (int): Maximum edit distance for corrections
        """
        self.max_edit_distance = max_edit_distance
        self.dictionary_manager = DictionaryManager(max_edit_distance=max_edit_distance)
        self.is_initialized = False
        
        if dictionary_path and os.path.exists(dictionary_path):
            self.load_dictionary(dictionary_path)
    
    def load_dictionary(self, dictionary_path):
        """
        Load the SymSpell dictionary from file.
        
        Args:
            dictionary_path (str): Path to the dictionary file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        sym_spell = self.dictionary_manager.load_dictionary(dictionary_path)
        if sym_spell:
            self.is_initialized = True
            return True
        return False
    
    def add_words_from_trie(self, trie):
        """
        Add individual words from institution names in the trie to the spell correction dictionary.
        This ensures that all words from institution names are available for spell correction.
        
        Args:
            trie: Trie object containing institution names
        """
        self.dictionary_manager.add_words_from_trie(trie)
        self.is_initialized = self.dictionary_manager.is_initialized()
      # Removed get_corrections_for_phrase - we only use smart corrections now
      # Removed get_corrections - we only use smart corrections now
      # Removed get_best_correction - we only use smart corrections now
    
    def is_word_in_dictionary(self, word):
        """
        Check if a word exists in the spell correction dictionary.
        
        Args:
            word (str): Word to check
            
        Returns:
            bool: True if word exists, False otherwise
        """
        if not self.is_initialized or not word:
            return False
        
        try:
            sym_spell = self.dictionary_manager.get_sym_spell()
            if not sym_spell:
                return False
                  # Use lookup with very strict parameters to check exact match
            suggestions = sym_spell.lookup(word.strip().lower(), Verbosity.TOP, max_edit_distance=0)
            return len(suggestions) > 0 and suggestions[0].distance == 0
        except:
            return False
    
    def get_smart_corrections_for_phrase(self, phrase, trie, max_suggestions=5):
        """
        Get smart spell correction suggestions that validate against actual institutions.
        
        This is the main and only correction strategy used by this service.
        It generates candidate corrections and validates them against real institution
        names to ensure all suggestions are meaningful and accurate.
        
        Process:
        1. Split phrase into words
        2. Generate correction candidates for each word using SymSpell
        3. Add common institution terms as alternatives for the last word
        4. Try different combinations of corrected words
        5. Validate each combination against the institution trie
        6. Return only combinations that match real institutions
        
        Args:
            phrase (str): The phrase to get corrections for
            trie: Trie object containing institution names for validation
            max_suggestions (int): Maximum number of suggestions to return
              Returns:
            list: List of dictionaries with validated corrected phrases
        """
        if not self.is_initialized or not phrase or not phrase.strip():
            return []
        
        try:
            # Common institution words that should be tried as alternatives
            institution_words = ['university', 'college', 'institute', 'school', 'academy']
              # Split the phrase into words
            words = phrase.strip().lower().split()
            if not words:
                return []
            
            # Get corrections for each word
            word_options = []
            corrections_made = []
            
            sym_spell = self.dictionary_manager.get_sym_spell()
            if not sym_spell:
                return []            
            for i, word in enumerate(words):
                options = [word]  # Always include original
                
                # Skip very short words
                if len(word) > 2:
                    # Get spell corrections
                    suggestions = sym_spell.lookup(
                        word, 
                        Verbosity.CLOSEST, 
                        max_edit_distance=self.max_edit_distance
                    )
                    
                    if suggestions:
                        for suggestion in suggestions[:3]:  # Top 3 suggestions
                            if suggestion.term != word:
                                options.append(suggestion.term)
                                if suggestion.distance > 0:
                                    corrections_made.append({
                                        'position': i,
                                        'original': word,
                                        'corrected': suggestion.term,
                                        'distance': suggestion.distance
                                    })
                    
                    # For last word, also try common institution words
                    if i == len(words) - 1:
                        for inst_word in institution_words:
                            # Check if any institution word is close to the original word
                            edit_dist = self._calculate_edit_distance(word, inst_word)
                            if edit_dist <= self.max_edit_distance and inst_word not in options:
                                options.append(inst_word)
                                corrections_made.append({
                                    'position': i,
                                    'original': word,
                                    'corrected': inst_word,
                                    'distance': edit_dist
                                })                
                word_options.append(options)
            
            # Generate combinations and validate against trie
            valid_corrections = []
            
            # Try different combinations (limit to prevent explosion)
            max_combinations = 20
            combinations_tried = 0
            
            def generate_combinations(word_lists, current_combo=[], depth=0):
                nonlocal combinations_tried, valid_corrections
                
                if combinations_tried >= max_combinations:
                    return
                
                if depth == len(word_lists):
                    combinations_tried += 1
                    test_phrase = ' '.join(current_combo)
                      # Check if this combination exists in trie
                    suggestions = trie.get_suggestions(test_phrase, max_suggestions=1)
                    
                    if suggestions:
                        
                        # Calculate which corrections were used
                        used_corrections = []
                        for i, (original, corrected) in enumerate(zip(words, current_combo)):
                            if original != corrected:
                                used_corrections.append({
                                    'position': i,
                                    'original': original,
                                    'corrected': corrected,
                                    'distance': self._calculate_edit_distance(original, corrected)
                                })
                        
                        valid_corrections.append({
                            'corrected_phrase': test_phrase,
                            'original_phrase': phrase.strip().lower(),
                            'corrections': used_corrections,
                            'has_corrections': len(used_corrections) > 0,                            'suggestions': suggestions  # Include the actual institution matches
                        })
                    return
                
                for option in word_lists[depth]:
                    generate_combinations(word_lists, current_combo + [option], depth + 1)
            
            generate_combinations(word_options)
              # Sort by number of corrections (fewer corrections = better)
            valid_corrections.sort(key=lambda x: len(x['corrections']))
            
            return valid_corrections[:max_suggestions]
            
        except Exception as e:
            print(f"Error getting smart spell corrections for phrase '{phrase}': {e}")
            return []
    
    def get_stats(self):
        """
        Get statistics about the spell correction service.
        
        Returns:
            dict: Dictionary containing service statistics
        """
        sym_spell = self.dictionary_manager.get_sym_spell()
        return {
            'is_initialized': self.is_initialized,
            'word_count': sym_spell.word_count if sym_spell else 0,
            'max_edit_distance': self.max_edit_distance
        }
    
    def _calculate_edit_distance(self, word1, word2):
        """Calculate simple edit distance between two words."""
        if len(word1) < len(word2):
            return self._calculate_edit_distance(word2, word1)
        
        if len(word2) == 0:
            return len(word1)
        
        previous_row = list(range(len(word2) + 1))
        for i, c1 in enumerate(word1):
            current_row = [i + 1]
            for j, c2 in enumerate(word2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
