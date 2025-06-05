import pandas as pd
from .trie import Trie
import os
import re


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
    
    def clean_institution_name(self, name):
        """
        Clean institution name by removing text after commas and unnecessary suffixes.
        
        Args:
            name (str): Original institution name
            
        Returns:
            str: Cleaned institution name
        """
        if not name or not isinstance(name, str):
            return name
            
        # Remove text after comma (like "BancCentral, National Association" -> "BancCentral")
        cleaned = name.split(',')[0].strip()
        
        # Remove common unnecessary suffixes
        suffixes_to_remove = [
            'National Association',
            'N.A.',
            'F.S.B.',
            'Federal Savings Bank',
            'Trust Company',
            'Inc.',
            'LLC',
            'Corporation',
            'Corp.'
        ]
        
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
                break
        
        return cleaned
    
    def load_from_multiple_csvs(self, csv_configs):
        """
        Load institution names from multiple CSV files with different types.
        
        Args:
            csv_configs (list): List of dictionaries with csv file configurations
                               Each dict should have: path, name_column, institution_type
        """
        total_loaded = 0
        
        for config in csv_configs:
            try:
                count = self.load_from_csv(
                    config['path'], 
                    config.get('name_column', 'name'),
                    config.get('frequency_column'),
                    config.get('institution_type', 'Unknown')
                )
                total_loaded += count
                print(f"Loaded {count} {config.get('institution_type', 'Unknown')} institutions from {config['path']}")
            except Exception as e:
                print(f"Error loading from {config['path']}: {str(e)}")
        
        self.is_initialized = True
        print(f"Total loaded: {total_loaded} institutions into autocomplete trie")
    
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
        loaded_count = 0
        seen_names = set()  # To track duplicates
        
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
            # Read CSV file, skip header rows that don't contain data
            df = pd.read_csv(csv_path)
            
            # Handle different CSV formats
            if name_column not in df.columns:
                # Try to find the name column automatically
                possible_name_columns = ['name', 'NAME', 'Name', 'institution_name', 'bank_name']
                name_column = None
                for col in possible_name_columns:
                    if col in df.columns:
                        name_column = col
                        break
                
                if name_column is None:
                    # For financial institution CSVs, the name might be in the second column
                    if len(df.columns) > 1:
                        name_column = df.columns[1]  # Usually the name column
                    else:
                        available_cols = ', '.join(df.columns.tolist())
                        raise ValueError(f"No name column found. Available columns: {available_cols}")
            
            # Load names into trie
            for idx, row in df.iterrows():
                try:
                    name = row[name_column]
                    if pd.notna(name) and isinstance(name, str) and name.strip():
                        # Clean the institution name
                        cleaned_name = self.clean_institution_name(name.strip())
                        
                        # Skip if empty after cleaning or if it's a duplicate
                        if not cleaned_name or cleaned_name.lower() in seen_names:
                            continue
                        
                        seen_names.add(cleaned_name.lower())
                        
                        # Use frequency if available, otherwise use inverse index for basic ranking
                        frequency = 1
                        if frequency_column and frequency_column in df.columns:
                            freq_val = row[frequency_column]
                            if pd.notna(freq_val) and isinstance(freq_val, (int, float)):
                                frequency = int(freq_val)
                        else:
                            # Higher frequency for earlier entries (assumes some ordering)
                            frequency = len(df) - idx
                        
                        self.trie.insert(cleaned_name, frequency, institution_type)
                        loaded_count += 1
                except Exception as e:
                    # Skip problematic rows
                    continue
            
            return loaded_count
            
        except Exception as e:
            print(f"Error loading CSV data from {csv_path}: {str(e)}")
            raise
    
    def add_institution(self, name, frequency=1, institution_type=None):
        """
        Add a single institution name to the trie.
        
        Args:
            name (str): Institution name
            frequency (int): Frequency/ranking for the institution
            institution_type (str): Type of institution (Edu, Fin, Med)
        """
        if name and isinstance(name, str) and name.strip():
            cleaned_name = self.clean_institution_name(name.strip())
            if cleaned_name:
                self.trie.insert(cleaned_name, frequency, institution_type)
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
