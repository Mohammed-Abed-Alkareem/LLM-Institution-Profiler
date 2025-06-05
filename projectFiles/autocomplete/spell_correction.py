"""
Spell correction service for handling "did you mean" functionality.
Integrates with SymSpell for finding closest matches when autocomplete fails.
"""

from symspellpy import SymSpell, Verbosity
import os


class SpellCorrectionService:
    """
    Service for providing spell correction suggestions when autocomplete fails.
    Uses SymSpell for finding the closest matching institution names.
    """
    
    def __init__(self, dictionary_path=None, max_edit_distance=2):
        """
        Initialize the spell correction service.
        
        Args:
            dictionary_path (str): Path to SymSpell dictionary file
            max_edit_distance (int): Maximum edit distance for corrections
        """
        self.sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance, prefix_length=7)
        self.is_initialized = False
        self.max_edit_distance = max_edit_distance
        
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
        try:
            self.sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1, encoding='utf-8')
            self.is_initialized = True
            print(f"Spell correction dictionary loaded with {self.sym_spell.word_count} words")
            return True
        except Exception as e:
            print(f"Warning: Could not load spell correction dictionary: {e}")
            self.is_initialized = False
            return False
    def add_words_from_trie(self, trie):
        """
        Add individual words from institution names in the trie to the spell correction dictionary.
        This ensures that all words from institution names are available for spell correction.
        
        Args:
            trie: Trie object containing institution names
        """
        if not hasattr(trie, 'get_all_words'):
            return
        
        try:
            all_words = trie.get_all_words()
            word_frequencies = {}
            
            for word_info in all_words:
                # Extract the institution name and its frequency
                if isinstance(word_info, dict):
                    institution_name = word_info.get('name', '')
                    frequency = word_info.get('frequency', 1)
                else:
                    institution_name = str(word_info)
                    frequency = 1
                
                if institution_name and len(institution_name.strip()) > 0:
                    # Split institution name into individual words
                    words = institution_name.lower().split()
                    
                    for word in words:
                        # Clean the word (remove punctuation, etc.)
                        cleaned_word = ''.join(c for c in word if c.isalnum()).strip()
                        
                        # Skip very short words and common words
                        if len(cleaned_word) > 2:
                            # Accumulate frequency for each word
                            if cleaned_word in word_frequencies:
                                word_frequencies[cleaned_word] += frequency
                            else:
                                word_frequencies[cleaned_word] = frequency
            
            # Add all unique words to SymSpell dictionary
            for word, freq in word_frequencies.items():
                self.sym_spell.create_dictionary_entry(word, freq)
            
            self.is_initialized = True
            print(f"Added {len(word_frequencies)} unique words from {len(all_words)} institutions to spell correction dictionary")
        except Exception as e:
            print(f"Warning: Could not add words from trie to spell correction: {e}")
    def get_corrections_for_phrase(self, phrase, max_suggestions=5):
        """
        Get spell correction suggestions for a phrase by correcting individual words.
        
        Args:
            phrase (str): The phrase to get corrections for
            max_suggestions (int): Maximum number of suggestions to return
            
        Returns:
            list: List of dictionaries with corrected phrases and correction details
        """
        if not self.is_initialized or not phrase or not phrase.strip():
            return []
        
        print(f"DEBUG: Spell checking phrase: '{phrase}'")
        
        try:
            # Split the phrase into words
            words = phrase.strip().lower().split()
            if not words:
                return []
            
            print(f"DEBUG: Split into words: {words}")
            
            # For each word, get the best correction
            corrected_words = []
            corrections_made = []
            has_corrections = False
            
            for i, word in enumerate(words):
                print(f"DEBUG: Checking word '{word}' (length: {len(word)})")
                
                # Skip very short words (articles, prepositions, etc.)
                if len(word) <= 2:
                    corrected_words.append(word)
                    print(f"DEBUG: Skipping short word: '{word}'")
                    continue
                
                # Get suggestions for this word
                suggestions = self.sym_spell.lookup(
                    word, 
                    Verbosity.CLOSEST, 
                    max_edit_distance=self.max_edit_distance
                )
                
                print(f"DEBUG: Found {len(suggestions)} suggestions for '{word}'")
                if suggestions:
                    print(f"DEBUG: Best suggestion: '{suggestions[0].term}' (distance: {suggestions[0].distance})")
                
                if suggestions and suggestions[0].distance > 0:
                    # Use the best correction
                    corrected_word = suggestions[0].term
                    corrected_words.append(corrected_word)
                    corrections_made.append({
                        'position': i,
                        'original': word,
                        'corrected': corrected_word,
                        'distance': suggestions[0].distance
                    })
                    has_corrections = True
                    print(f"DEBUG: Corrected '{word}' → '{corrected_word}'")
                else:
                    # Keep the original word
                    corrected_words.append(word)
                    print(f"DEBUG: No correction needed for '{word}'")
            
            # Only return corrections if we actually made some changes
            if has_corrections:
                corrected_phrase = ' '.join(corrected_words)
                print(f"DEBUG: Final correction: '{phrase}' → '{corrected_phrase}'")
                return [{
                    'corrected_phrase': corrected_phrase,
                    'original_phrase': phrase.strip().lower(),
                    'corrections': corrections_made,
                    'has_corrections': True
                }]
            
            print(f"DEBUG: No corrections needed for phrase: '{phrase}'")
            return []
            
        except Exception as e:
            print(f"Error getting spell corrections for phrase '{phrase}': {e}")
            return []
    
    def get_corrections(self, word, max_suggestions=3, suggestion_verbosity=Verbosity.CLOSEST):
        """
        Get spell correction suggestions for a single word.
        
        Args:
            word (str): The word to get corrections for
            max_suggestions (int): Maximum number of suggestions to return
            suggestion_verbosity: SymSpell verbosity level
            
        Returns:
            list: List of correction suggestions
        """
        if not self.is_initialized or not word or not word.strip():
            return []
        
        try:
            # Get suggestions from SymSpell
            suggestions = self.sym_spell.lookup(
                word.strip().lower(), 
                suggestion_verbosity, 
                max_edit_distance=self.max_edit_distance
            )
            
            # Limit results to max_suggestions
            suggestions = suggestions[:max_suggestions]
            
            # Format suggestions for consistency with autocomplete
            formatted_suggestions = []
            for suggestion in suggestions:
                formatted_suggestions.append({
                    'term': suggestion.term,
                    'distance': suggestion.distance,
                    'frequency': suggestion.count,
                    'original_query': word
                })
            
            return formatted_suggestions
            
        except Exception as e:
            print(f"Error getting spell corrections for '{word}': {e}")
            return []
    
    def get_best_correction(self, word):
        """
        Get the single best correction for a word.
        
        Args:
            word (str): The word to correct
            
        Returns:
            str or None: Best correction or None if no good correction found
        """
        corrections = self.get_corrections(word, max_suggestions=1)
        
        if corrections and len(corrections) > 0:
            best_correction = corrections[0]
            # Only return if the edit distance is reasonable (not too high)
            if best_correction['distance'] <= min(len(word) // 2, self.max_edit_distance):
                return best_correction['term']
        
        return None
    
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
            # Use lookup with very strict parameters to check exact match
            suggestions = self.sym_spell.lookup(word.strip().lower(), Verbosity.TOP, max_edit_distance=0)
            return len(suggestions) > 0 and suggestions[0].distance == 0
        except:
            return False
    
    def get_stats(self):
        """
        Get statistics about the spell correction service.
        
        Returns:
            dict: Dictionary containing service statistics
        """
        return {
            'is_initialized': self.is_initialized,
            'word_count': self.sym_spell.word_count if self.is_initialized else 0,
            'max_edit_distance': self.max_edit_distance
        }
    
    def get_smart_corrections_for_phrase(self, phrase, trie, max_suggestions=5):
        """
        Get smart spell correction suggestions that validate against actual institutions.
        Tries different combinations of corrected words and common institution terms.
        
        Args:
            phrase (str): The phrase to get corrections for
            trie: Trie object containing institution names for validation
            max_suggestions (int): Maximum number of suggestions to return
            
        Returns:
            list: List of dictionaries with validated corrected phrases
        """
        if not self.is_initialized or not phrase or not phrase.strip():
            return []
        
        print(f"DEBUG: Smart spell checking phrase: '{phrase}'")
        
        try:
            # Common institution words that should be tried as alternatives
            institution_words = ['university', 'college', 'institute', 'school', 'academy']
            
            # Split the phrase into words
            words = phrase.strip().lower().split()
            if not words:
                return []
            
            print(f"DEBUG: Split into words: {words}")
            
            # Get corrections for each word
            word_options = []
            corrections_made = []
            
            for i, word in enumerate(words):
                print(f"DEBUG: Processing word '{word}' at position {i}")
                
                options = [word]  # Always include original
                
                # Skip very short words
                if len(word) > 2:
                    # Get spell corrections
                    suggestions = self.sym_spell.lookup(
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
                            # Only add if it's a reasonable correction (edit distance check)
                            inst_suggestions = self.sym_spell.lookup(
                                word,
                                Verbosity.CLOSEST,
                                max_edit_distance=self.max_edit_distance
                            )
                            
                            # Check if any institution word is close to the original word
                            for inst_word in institution_words:
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
                print(f"DEBUG: Options for '{word}': {options}")
            
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
                        print(f"DEBUG: Found valid combination: '{test_phrase}'")
                        
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
                            'has_corrections': len(used_corrections) > 0,
                            'suggestions': suggestions  # Include the actual institution matches
                        })
                    else:
                        print(f"DEBUG: No institutions found for: '{test_phrase}'")
                    return
                
                for option in word_lists[depth]:
                    generate_combinations(word_lists, current_combo + [option], depth + 1)
            
            generate_combinations(word_options)
            
            # Sort by number of corrections (fewer corrections = better)
            valid_corrections.sort(key=lambda x: len(x['corrections']))
            
            print(f"DEBUG: Found {len(valid_corrections)} valid corrections")
            return valid_corrections[:max_suggestions]
            
        except Exception as e:
            print(f"Error getting smart spell corrections for phrase '{phrase}': {e}")
            return []
    
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

    # ...existing code...
