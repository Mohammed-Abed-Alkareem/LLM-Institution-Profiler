"""
Dictionary Manager for spell check functionality.
Handles loading, creating, and managing spell check dictionaries.
"""

import os
import pandas as pd
from symspellpy import SymSpell


class DictionaryManager:
    """
    Manages spell check dictionaries for institution names.
    Handles creation, loading, and maintenance of SymSpell dictionaries.
    """
    
    def __init__(self, max_edit_distance=2, prefix_length=7):
        """
        Initialize the dictionary manager.
        
        Args:
            max_edit_distance (int): Maximum edit distance for corrections
            prefix_length (int): Prefix length for SymSpell optimization
        """
        self.max_edit_distance = max_edit_distance
        self.prefix_length = prefix_length
        self.sym_spell = None
        
    def create_symspell_dict(self, csv_configs, dictionary_path):
        """
        Create a SymSpell dictionary from multiple CSV files.
        
        Args:
            csv_configs (list): List of dictionaries with CSV file configurations
                               Each dict should have: path, name_column, institution_type
            dictionary_path (str): Path to save the SymSpell dictionary
        """
        word_frequencies = {}
        
        for config in csv_configs:
            csv_file = config['path']
            name_column = config.get('name_column', 'name')
            institution_type = config.get('institution_type', 'Unknown')
            
            if not os.path.exists(csv_file):
                print(f"Warning: CSV file {csv_file} not found, skipping...")
                continue
                
            if not csv_file.endswith('.csv'):
                print(f"Warning: File {csv_file} is not a CSV file, skipping...")
                continue
            
            try:
                # Read the CSV file
                if 'list_of_univs' in csv_file:
                    # Special handling for university list (column index 5)
                    df = pd.read_csv(csv_file, usecols=[5])
                    df.columns = ['name']  # Rename column for consistency
                else:
                    # Use specified column name
                    df = pd.read_csv(csv_file)
                    if name_column not in df.columns:
                        print(f"Warning: Column '{name_column}' not found in {csv_file}, skipping...")
                        continue
                    df = df[[name_column]]
                    df.columns = ['name']  # Rename for consistency
                
                # Process each institution name
                for institution_name in df['name'].dropna():
                    if not isinstance(institution_name, str) or len(institution_name.strip()) == 0:
                        continue
                    
                    # Clean and normalize the institution name
                    clean_name = institution_name.strip().lower()
                    
                    # Add the full institution name
                    if clean_name in word_frequencies:
                        word_frequencies[clean_name] += 1
                    else:
                        word_frequencies[clean_name] = 1
                    
                    # Split into individual words and add them too
                    words = clean_name.split()
                    for word in words:
                        # Clean the word (remove punctuation, etc.)
                        cleaned_word = ''.join(c for c in word if c.isalnum()).strip()
                        
                        # Skip very short words
                        if len(cleaned_word) > 2:
                            if cleaned_word in word_frequencies:
                                word_frequencies[cleaned_word] += 1
                            else:
                                word_frequencies[cleaned_word] = 1
                
                print(f"Processed {len(df)} institutions from {csv_file} ({institution_type})")
                
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
                continue
        
        # Write dictionary file
        try:
            with open(dictionary_path, 'w', encoding='utf-8') as f:
                for word, frequency in word_frequencies.items():
                    f.write(f"{word},{frequency}\n")
            
            print(f"SymSpell dictionary created with {len(word_frequencies)} entries at {dictionary_path}")
            return True
            
        except Exception as e:
            print(f"Error writing dictionary file {dictionary_path}: {e}")
            return False
    
    def load_dictionary(self, dictionary_path):
        """
        Load a SymSpell dictionary from file.
        
        Args:
            dictionary_path (str): Path to the dictionary file
            
        Returns:
            SymSpell: Loaded SymSpell instance or None if failed
        """
        if not os.path.exists(dictionary_path):
            print(f"Dictionary file {dictionary_path} not found")
            return None
        
        try:
            sym_spell = SymSpell(
                max_dictionary_edit_distance=self.max_edit_distance, 
                prefix_length=self.prefix_length
            )
            
            sym_spell.load_dictionary(
                dictionary_path, 
                term_index=0, 
                count_index=1, 
                encoding='utf-8'
            )
            
            self.sym_spell = sym_spell
            print(f"Spell correction dictionary loaded with {sym_spell.word_count} words")
            return sym_spell
            
        except Exception as e:
            print(f"Error loading dictionary {dictionary_path}: {e}")
            return None
    
    def add_words_from_trie(self, trie):
        """
        Add words from a trie data structure to the spell correction dictionary.
        
        Args:
            trie: Trie object containing institution names
        """
        if not self.sym_spell:
            self.sym_spell = SymSpell(
                max_dictionary_edit_distance=self.max_edit_distance,
                prefix_length=self.prefix_length
            )
        
        if not hasattr(trie, 'get_all_words'):
            print("Warning: Trie does not have get_all_words method")
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
                        
                        # Skip very short words
                        if len(cleaned_word) > 2:
                            # Accumulate frequency for each word
                            if cleaned_word in word_frequencies:
                                word_frequencies[cleaned_word] += frequency
                            else:
                                word_frequencies[cleaned_word] = frequency
            
            # Add all unique words to SymSpell dictionary
            for word, freq in word_frequencies.items():
                self.sym_spell.create_dictionary_entry(word, freq)
            
            print(f"Added {len(word_frequencies)} unique words from {len(all_words)} institutions to spell correction dictionary")
            
        except Exception as e:
            print(f"Warning: Could not add words from trie to spell correction: {e}")
    
    def get_sym_spell(self):
        """
        Get the SymSpell instance.
        
        Returns:
            SymSpell: The SymSpell instance or None if not initialized
        """
        return self.sym_spell
    
    def is_initialized(self):
        """
        Check if the dictionary manager is initialized.
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return self.sym_spell is not None and self.sym_spell.word_count > 0
