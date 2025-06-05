"""
CSV loading utilities for institutional data.
Handles loading and processing data from various CSV formats for different institution types.
"""

import pandas as pd
import os
from .institution_normalizer import InstitutionNormalizer


class CSVLoader:
    """
    Utility class for loading institution data from CSV files.
    """
    
    @staticmethod
    def load_from_csv(csv_path, trie, name_column='name', frequency_column=None, institution_type='Unknown'):
        """
        Load institution names from a CSV file into the trie.
        
        Args:
            csv_path (str): Path to the CSV file
            trie: Trie instance to load data into
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
                        cleaned_name = InstitutionNormalizer.clean_institution_name(name.strip())
                        
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
                        
                        trie.insert(cleaned_name, frequency, institution_type)
                        loaded_count += 1
                        
                        # Also insert normalized versions (without prefixes) for better search
                        normalized_names = InstitutionNormalizer.normalize_institution_name(
                            cleaned_name, institution_type
                        )
                        for normalized_name in normalized_names:
                            # Insert with slightly lower frequency to prefer original names
                            trie.insert(
                                normalized_name, 
                                max(1, frequency - 1), 
                                institution_type, 
                                original_name=cleaned_name
                            )
                except Exception as e:
                    # Skip problematic rows
                    continue
            
            return loaded_count
        except Exception as e:
            print(f"Error loading CSV data from {csv_path}: {str(e)}")
            raise
    
    @staticmethod
    def load_from_multiple_csvs(csv_configs, trie):
        """
        Load institution names from multiple CSV files with different types.
        
        Args:
            csv_configs (list): List of dictionaries with csv file configurations
                               Each dict should have: path, name_column, institution_type
            trie: Trie instance to load data into
            
        Returns:
            int: Total number of institutions loaded
        """
        total_loaded = 0
        
        for config in csv_configs:
            try:
                count = CSVLoader.load_from_csv(
                    config['path'], 
                    trie,
                    config.get('name_column', 'name'),
                    config.get('frequency_column'),
                    config.get('institution_type', 'Unknown')
                )
                total_loaded += count
                print(f"Loaded {count} {config.get('institution_type', 'Unknown')} institutions from {config['path']}")
            except Exception as e:
                print(f"Error loading from {config['path']}: {str(e)}")
        
        print(f"Total loaded: {total_loaded} institutions into autocomplete trie")
        return total_loaded
