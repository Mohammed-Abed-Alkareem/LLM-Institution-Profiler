"""
Main autocomplete service class for managing institution name suggestions.
Simplified version that delegates specific functionality to specialized modules.
"""

from .trie import Trie
from .csv_loader import CSVLoader
from .institution_normalizer import InstitutionNormalizer


class AutocompleteService:
    """
    Service class for managing autocomplete functionality using a Trie data structure.
    Handles loading university and financial institution data and providing fast prefix-based suggestions.
    """
    
    def __init__(self, csv_paths=None):
        self.trie = Trie()
        self.is_initialized = False
        
        if csv_paths:
            if isinstance(csv_paths, str):
                csv_paths = [csv_paths]
            self.load_from_multiple_csvs(csv_paths)
    
    def load_from_multiple_csvs(self, csv_configs):
        """
        Load institution names from multiple CSV files with different types.
        
        Args:
            csv_configs (list): List of dictionaries with csv file configurations
                               Each dict should have: path, name_column, institution_type
        """
        total_loaded = CSVLoader.load_from_multiple_csvs(csv_configs, self.trie)
        self.is_initialized = True
    
    def load_from_csv(self, csv_path, name_column='name', frequency_column=None, institution_type='Unknown'):
        """
        Load institution names from a CSV file into the trie.
        
        Args:
            csv_path (str): Path to the CSV file
            name_column (str): Name of the column containing institution names
            frequency_column (str): Optional column for frequency/ranking data
            institution_type (str): Type of institution (Edu, Fin, Med)
            
        Returns:
            int: Number of institutions loaded
        """
        return CSVLoader.load_from_csv(csv_path, self.trie, name_column, frequency_column, institution_type)

    def add_institution(self, name, frequency=1, institution_type=None):
        """
        Add a single institution name to the trie.
        
        Args:
            name (str): Institution name
            frequency (int): Frequency/ranking for the institution
            institution_type (str): Type of institution (Edu, Fin, Med)
        """
        if name and isinstance(name, str) and name.strip():
            cleaned_name = InstitutionNormalizer.clean_institution_name(name.strip())
            if cleaned_name:
                self.trie.insert(cleaned_name, frequency, institution_type)
                
                # Also insert normalized versions (without prefixes) for better search
                normalized_names = InstitutionNormalizer.normalize_institution_name(cleaned_name, institution_type)
                for normalized_name in normalized_names:
                    # Insert with slightly lower frequency to prefer original names
                    self.trie.insert(normalized_name, max(1, frequency - 1), institution_type, original_name=cleaned_name)
                
                if not self.is_initialized:
                    self.is_initialized = True    
    def get_suggestions(self, prefix, max_suggestions=5):
        """
        Get autocomplete suggestions for a given prefix with enhanced prefix handling.
        
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
        
        # First, try direct search
        suggestions = self.trie.get_suggestions(clean_prefix, max_suggestions)
        
        # If we have very few suggestions (≤2), try with common prefixes
        if len(suggestions) <= 2:
            additional_suggestions = []
            
            # Try each institution type's prefixes
            for institution_type in ['Edu', 'Fin', 'Med']:
                prefix_variations = InstitutionNormalizer.generate_prefix_variations(clean_prefix, institution_type)
                
                for variation in prefix_variations:
                    variation_suggestions = self.trie.get_suggestions(variation, max_suggestions)
                    additional_suggestions.extend(variation_suggestions)
            
            # Combine and deduplicate suggestions
            all_suggestions = suggestions + additional_suggestions
            seen_names = set()
            unique_suggestions = []
            
            for suggestion in all_suggestions:
                full_name = suggestion['full_name']
                if full_name.lower() not in seen_names:
                    seen_names.add(full_name.lower())
                    unique_suggestions.append(suggestion)
                    
                if len(unique_suggestions) >= max_suggestions:
                    break
            
            return unique_suggestions[:max_suggestions]
        
        return suggestions
    
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
