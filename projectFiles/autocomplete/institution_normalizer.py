"""
Institution name normalization and cleaning utilities.
Handles common prefixes, suffixes, and name standardization for different institution types.
"""

import re


class InstitutionNormalizer:
    """
    Utility class for normalizing and cleaning institution names.
    """
    
    # Common prefixes for different institution types
    INSTITUTION_PREFIXES = {
        'Edu': ['University of', 'College of', 'Institute of', 'School of'],
        'Fin': ['Bank of', 'Credit Union of', 'Federal Credit Union of', 'Savings Bank of'],
        'Med': ['Hospital of', 'Medical Center of', 'Clinic of', 'Healthcare of']
    }
    
    # Common suffixes to remove from institution names
    SUFFIXES_TO_REMOVE = [
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
    
    @classmethod
    def clean_institution_name(cls, name):
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
        for suffix in cls.SUFFIXES_TO_REMOVE:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
                break
        
        return cleaned
    
    @classmethod
    def normalize_institution_name(cls, name, institution_type):
        """
        Create normalized versions of institution names by removing common prefixes.
        
        Args:
            name (str): Original institution name
            institution_type (str): Type of institution (Edu, Fin, Med)
            
        Returns:
            list: List of normalized name variations
        """
        if not name or not isinstance(name, str):
            return []
            
        normalized_names = []
        name_lower = name.lower()
        
        # Get prefixes for this institution type
        prefixes = cls.INSTITUTION_PREFIXES.get(institution_type, [])
        
        for prefix in prefixes:
            prefix_lower = prefix.lower()
            if name_lower.startswith(prefix_lower):
                # Remove the prefix and add the normalized version
                normalized = name[len(prefix):].strip()
                if normalized and normalized not in normalized_names:
                    normalized_names.append(normalized)
                break
        
        return normalized_names
    
    @classmethod
    def generate_prefix_variations(cls, query, institution_type=None):
        """
        Generate query variations by adding common prefixes.
        
        Args:
            query (str): Original search query
            institution_type (str): Institution type to focus on (optional)
            
        Returns:
            list: List of query variations with prefixes
        """
        variations = []
        
        if institution_type and institution_type in cls.INSTITUTION_PREFIXES:
            # Focus on the specific institution type
            prefixes = cls.INSTITUTION_PREFIXES[institution_type]
        else:
            # Try all prefixes if type is unknown
            prefixes = []
            for type_prefixes in cls.INSTITUTION_PREFIXES.values():
                prefixes.extend(type_prefixes)
        
        for prefix in prefixes:
            variation = f"{prefix} {query}"
            variations.append(variation)
            
        return variations
