import pandas as pd
from .trie import Trie
import os


class AutocompleteService:
    """
    Service class for managing autocomplete functionality using a Trie data structure.
    Handles loading university data and providing fast prefix-based suggestions.
    """
    
    def __init__(self, csv_path=None):
        self.trie = Trie()
        self.is_initialized = False
        
        if csv_path:
            self.load_from_csv(csv_path)
    
    def load_from_csv(self, csv_path, name_column='name', frequency_column=None):
        """
        Load university names from a CSV file into the trie.
        
        Args:
            csv_path (str): Path to the CSV file
            name_column (str): Name of the column containing university names
            frequency_column (str): Optional column for frequency/ranking data
        """
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            if name_column not in df.columns:
                available_cols = ', '.join(df.columns.tolist())
                raise ValueError(f"Column '{name_column}' not found. Available columns: {available_cols}")
            
            # Load names into trie
            for idx, row in df.iterrows():
                name = row[name_column]
                if pd.notna(name) and isinstance(name, str) and name.strip():
                    # Use frequency if available, otherwise use inverse index for basic ranking
                    frequency = 1
                    if frequency_column and frequency_column in df.columns:
                        freq_val = row[frequency_column]
                        if pd.notna(freq_val) and isinstance(freq_val, (int, float)):
                            frequency = int(freq_val)
                    else:
                        # Higher frequency for earlier entries (assumes some ordering)
                        frequency = len(df) - idx
                    
                    self.trie.insert(name.strip(), frequency)
            
            self.is_initialized = True
            print(f"Loaded {self.trie.size()} university names into autocomplete trie")
            
        except Exception as e:
            print(f"Error loading CSV data: {str(e)}")
            raise
    
    def add_institution(self, name, frequency=1):
        """
        Add a single institution name to the trie.
        
        Args:
            name (str): Institution name
            frequency (int): Frequency/ranking for the institution
        """
        if name and isinstance(name, str) and name.strip():
            self.trie.insert(name.strip(), frequency)
            if not self.is_initialized:
                self.is_initialized = True
    
    def get_suggestions(self, prefix, max_suggestions=5):
        """
        Get autocomplete suggestions for a given prefix.
        
        Args:
            prefix (str): The text prefix to get suggestions for
            max_suggestions (int): Maximum number of suggestions to return
            
        Returns:
            list: List of suggested institution names
        """
        if not self.is_initialized:
            return []
        
        if not prefix or not isinstance(prefix, str):
            return []
        
        # Clean the prefix
        clean_prefix = prefix.strip()
        if not clean_prefix:
            return []
        
        return self.trie.get_suggestions(clean_prefix, max_suggestions)
    
    def search_institution(self, name):
        """
        Check if an institution name exists in the trie.
        
        Args:
            name (str): Institution name to search for
            
        Returns:
            bool: True if institution exists, False otherwise
        """
        if not self.is_initialized or not name:
            return False
        
        return self.trie.search(name.strip())
    
    def get_all_institutions(self):
        """
        Get all institution names sorted by frequency.
        
        Returns:
            list: List of all institution names
        """
        if not self.is_initialized:
            return []
        
        return self.trie.get_all_words()
    
    def get_stats(self):
        """
        Get statistics about the autocomplete service.
        
        Returns:
            dict: Dictionary containing stats like total count
        """
        return {
            'total_institutions': self.trie.size(),
            'is_initialized': self.is_initialized
        }


# Singleton instance for the autocomplete service
_autocomplete_service = None


def get_autocomplete_service():
    """
    Get the singleton autocomplete service instance.
    
    Returns:
        AutocompleteService: The singleton instance
    """
    global _autocomplete_service
    if _autocomplete_service is None:
        _autocomplete_service = AutocompleteService()
    return _autocomplete_service


def initialize_autocomplete(csv_path):
    """
    Initialize the autocomplete service with data from a CSV file.
    
    Args:
        csv_path (str): Path to the CSV file containing university data
    """
    service = get_autocomplete_service()
    service.load_from_csv(csv_path)
    return service
