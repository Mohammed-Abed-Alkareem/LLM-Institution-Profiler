# Autocomplete and Spell Check System Documentation

## Overview

This system provides intelligent autocomplete and spell correction functionality for institution names (universities, banks, hospitals). It combines a fast Trie-based autocomplete system with smart spell correction that validates suggestions against real institution data.

## Architecture

The system is composed of two main modules:

### 1. **Autocomplete Module** (`autocomplete/`)
Provides fast prefix-based institution name suggestions using a Trie data structure.

### 2. **Spell Check Module** (`spell_check/`)
Provides smart spell correction that validates corrections against actual institution names.

### 3. **Service Factory** (`service_factory.py`)
Coordinates the modules and provides high-level initialization functions.

---

## Autocomplete Module (`autocomplete/`)

### Core Components

#### **1. Trie Implementation** (`trie.py`)

**Classes:**
- `TrieNode`: Individual node in the Trie structure
- `Trie`: Main Trie data structure for fast prefix searches

**Key Features:**
- **Case-insensitive search**: All searches are normalized to lowercase
- **Frequency-based ranking**: Institutions can have weights for better ordering
- **Institution type support**: Tracks whether institution is Educational, Financial, or Medical
- **Original name preservation**: Stores both normalized and original forms

**Main Methods:**
```python
# Insert institution into trie
trie.insert(word, frequency=1, institution_type="Edu", original_name=None)

# Get autocomplete suggestions
suggestions = trie.get_suggestions(prefix, max_suggestions=5)

# Check if word exists
exists = trie.search(word)

# Check if prefix has any matches
has_matches = trie.starts_with(prefix)
```

**Performance:** O(m) search time where m is the length of the prefix.

#### **2. Autocomplete Service** (`autocomplete_service.py`)

**Main Class:** `AutocompleteService`

**Purpose:** High-level service that coordinates autocomplete functionality with spell correction fallback.

**Key Features:**
- **Multi-source loading**: Loads from multiple CSV files with different institution types
- **Intelligent prefix handling**: Tries variations with common institutional prefixes
- **Spell correction integration**: Falls back to spell correction when no autocomplete matches found
- **Smart deduplication**: Prevents duplicate suggestions across different sources

**Main Methods:**
```python
# Initialize service
service = AutocompleteService(csv_paths=None, spell_dict_path=None)

# Load data from multiple CSV files
service.load_from_multiple_csvs(csv_configs)

# Get suggestions with spell correction fallback
result = service.get_suggestions(prefix, max_suggestions=5, include_spell_correction=True)

# Get only spell corrections (when autocomplete fails)
corrections = service.get_spell_corrections(phrase, max_suggestions=3)
```

**Response Format:**
```python
{
    'suggestions': [list of institution objects],
    'source': 'autocomplete' | 'spell_correction' | 'no_match' | 'error',
    'original_query': 'user input',
    'message': 'status message'
}
```

#### **3. CSV Loader** (`csv_loader.py`)

**Class:** `CSVLoader`

**Purpose:** Handles loading institution data from various CSV file formats.

**Features:**
- **Multi-format support**: Handles different CSV structures for different institution types
- **Special handling**: Custom logic for university lists, financial institutions, hospitals
- **Data cleaning**: Removes invalid entries and normalizes names
- **Progress tracking**: Reports loading statistics

**Main Methods:**
```python
# Load single CSV file
count = CSVLoader.load_from_csv(csv_path, trie, name_column='name', 
                               frequency_column=None, institution_type='Edu')

# Load multiple CSV files
total = CSVLoader.load_from_multiple_csvs(csv_configs, trie)
```

**Supported CSV Formats:**
- **Universities**: Column index 5 or 'name' column
- **Financial institutions**: 'NAME' column
- **Hospitals**: 'hospital_name' column

#### **4. Institution Normalizer** (`institution_normalizer.py`)

**Class:** `InstitutionNormalizer`

**Purpose:** Cleans and normalizes institution names for better matching.

**Features:**
- **Prefix handling**: Manages common prefixes like "University of", "Bank of"
- **Suffix removal**: Removes corporate suffixes like "Inc.", "LLC"
- **Name cleaning**: Removes special characters, extra whitespace
- **Prefix variations**: Generates search variations for better matches

**Institution Type Prefixes:**
- **Educational**: "University of", "College of", "Institute of", "School of"
- **Financial**: "Bank of", "Credit Union of", "Federal Credit Union of"
- **Medical**: "Hospital of", "Medical Center of", "Clinic of"

**Main Methods:**
```python
# Clean institution name
clean_name = InstitutionNormalizer.clean_institution_name(name)

# Generate normalized variations
variations = InstitutionNormalizer.normalize_institution_name(name, institution_type)

# Generate prefix variations for search
variations = InstitutionNormalizer.generate_prefix_variations(query, institution_type)
```

---

## Spell Check Module (`spell_check/`)

### Core Components

#### **1. Spell Correction Service** (`spell_correction_service.py`)

**Class:** `SpellCorrectionService`

**Purpose:** Provides smart spell correction that validates all suggestions against real institution data.

**Strategy: Smart Correction Only**
- Generates candidate corrections using SymSpell
- Creates combinations of corrected words
- Validates ALL combinations against the institution trie
- Only returns corrections that match real institutions
- No false positives - if it's suggested, it exists in the database

**Key Features:**
- **Phrase-level correction**: Corrects individual words and tries combinations
- **Institution term suggestions**: Tries common terms like "university", "college"
- **Real-time validation**: All suggestions verified against actual data
- **Zero false positives**: Never suggests non-existent institutions

**Main Methods:**
```python
# Initialize service
service = SpellCorrectionService(dictionary_path=None, max_edit_distance=2)

# Get smart corrections (main method)
corrections = service.get_smart_corrections_for_phrase(phrase, trie, max_suggestions=5)

# Check if word exists in dictionary
exists = service.is_word_in_dictionary(word)

# Add words from institution trie
service.add_words_from_trie(trie)
```

**Smart Correction Process:**
1. Split input phrase into individual words
2. Generate correction candidates for each word using SymSpell
3. For the last word, also try common institution terms
4. Create combinations of all correction options
5. Test each combination against the institution trie
6. Return only combinations that match real institutions

**Example:**
```python
# Input: "harvrd university"
# Process:
# - "harvrd" → ["harvrd", "harvard"]
# - "university" → ["university"]
# - Test combinations: ["harvrd university", "harvard university"]
# - Validate: "harvard university" ✓ exists → return Harvard University
# - Result: [{"corrected_phrase": "harvard university", "suggestions": [Harvard University]}]
```

#### **2. Dictionary Manager** (`dictionary_manager.py`)

**Class:** `DictionaryManager`

**Purpose:** Manages SymSpell dictionaries for spell checking.

**Features:**
- **Dictionary creation**: Builds SymSpell dictionaries from CSV files
- **Word frequency management**: Tracks word frequencies for better corrections
- **Multi-source support**: Combines words from multiple institution types
- **Efficient loading**: Optimized dictionary loading and management

**Main Methods:**
```python
# Initialize manager
manager = DictionaryManager(max_edit_distance=2, prefix_length=7)

# Create dictionary from CSV files
success = manager.create_symspell_dict(csv_configs, dictionary_path)

# Load existing dictionary
sym_spell = manager.load_dictionary(dictionary_path)

# Add words from trie
manager.add_words_from_trie(trie)
```

**Dictionary Creation Process:**
1. Read institution names from multiple CSV files
2. Extract individual words from institution names
3. Clean and normalize words (remove punctuation, short words)
4. Calculate word frequencies across all institutions
5. Save to SymSpell-compatible format (word,frequency)

---

## Service Factory (`service_factory.py`)

### Purpose
Provides high-level initialization and coordination between autocomplete and spell check modules.

### Features
- **Singleton management**: Ensures single instance of autocomplete service
- **Cross-module coordination**: Integrates autocomplete with spell checking
- **Application configuration**: Contains CSV file paths and institution mappings
- **Easy initialization**: Simple functions for different use cases

### Main Functions

#### **1. get_autocomplete_service()**
```python
service = get_autocomplete_service(spell_dict_path=None)
```
Returns singleton autocomplete service instance.

#### **2. initialize_autocomplete_with_all_institutions()**
```python
service = initialize_autocomplete_with_all_institutions(base_dir)
```
Initializes the complete system with all institution types:

**Data Sources:**
- **Educational**: `list_of_univs.csv` (9,682 universities)
- **Financial**: 
  - `national-by-name.csv` (712 national banks)
  - `thrifts-by-name.csv` (226 thrift institutions)
  - `trust-by-name.csv` (61 trust companies)
- **Medical**: `world_hospitals_globalsurg.csv` (917 hospitals worldwide)

**Total**: ~11,598 institutions across all types

---

## Data Flow

### 1. Initialization Flow
```
service_factory.initialize_autocomplete_with_all_institutions()
  ↓
AutocompleteService.__init__()
  ↓
CSVLoader.load_from_multiple_csvs() → loads data into Trie
  ↓
SpellCorrectionService.add_words_from_trie() → builds spell dictionary
```

### 2. Autocomplete Request Flow
```
User Input: "harv"
  ↓
AutocompleteService.get_suggestions()
  ↓
Trie.get_suggestions() → ["Harvard University", "Harvey Mudd College"]
  ↓
Return: autocomplete results
```

### 3. Spell Correction Flow
```
User Input: "harvrd university"
  ↓
AutocompleteService.get_suggestions() → no autocomplete matches
  ↓
SpellCorrectionService.get_smart_corrections_for_phrase()
  ↓
Generate candidates: ["harvrd"→"harvard"] + ["university"]
  ↓
Test combinations against Trie: "harvard university" ✓
  ↓
Return: [{"corrected_phrase": "harvard university", "suggestions": [...]}]
```

---

## Configuration

### CSV File Configuration
```python
csv_configs = [
    {
        'path': 'path/to/universities.csv',
        'name_column': 'name',           # Column containing institution names
        'institution_type': 'Edu'        # Institution type: Edu/Fin/Med
    },
    # ... more configurations
]
```

### Institution Types
- **Edu**: Educational institutions (universities, colleges)
- **Fin**: Financial institutions (banks, credit unions)
- **Med**: Medical institutions (hospitals, clinics)

### Performance Parameters
- **max_edit_distance**: Maximum spelling errors to correct (default: 2)
- **max_suggestions**: Maximum number of suggestions to return (default: 5)
- **prefix_length**: SymSpell optimization parameter (default: 7)

---

## Usage Examples

### Basic Initialization
```python
from service_factory import initialize_autocomplete_with_all_institutions
import os

# Initialize with all institution data
base_dir = os.path.dirname(os.path.abspath(__file__))
service = initialize_autocomplete_with_all_institutions(base_dir)
```

### Getting Autocomplete Suggestions
```python
# Get autocomplete suggestions
result = service.get_suggestions("harv", max_suggestions=5)

print(f"Source: {result['source']}")  # 'autocomplete'
for suggestion in result['suggestions']:
    print(f"- {suggestion['full_name']} ({suggestion['institution_type']})")
```

### Spell Correction
```python
# Get spell corrections when autocomplete fails
result = service.get_suggestions("harvrd university", include_spell_correction=True)

if result['source'] == 'spell_correction':
    print("Did you mean:")
    for suggestion in result['suggestions']:
        print(f"- {suggestion['full_name']}")
```

### Custom CSV Loading
```python
from autocomplete import AutocompleteService

# Load custom CSV data
service = AutocompleteService()
csv_configs = [
    {
        'path': 'my_institutions.csv',
        'name_column': 'institution_name',
        'institution_type': 'Edu'
    }
]
service.load_from_multiple_csvs(csv_configs)
```

---

## Performance Characteristics

### Autocomplete Performance
- **Search Time**: O(m) where m = prefix length
- **Memory**: O(n*k) where n = number of institutions, k = average name length
- **Throughput**: ~1000+ searches/second for typical datasets

### Spell Correction Performance
- **Correction Time**: O(w*c*v) where w = words in phrase, c = correction candidates, v = validation time
- **Memory**: Additional O(d) where d = dictionary size
- **Accuracy**: 100% precision (no false positives), high recall for real institutions

### Memory Usage
- **Trie Structure**: ~50-100 MB for 12,000 institutions
- **Spell Dictionary**: ~10-20 MB for extracted words
- **Total**: ~100-150 MB loaded in memory

---

## Key Benefits

### 1. **High Accuracy**
- Zero false positives in spell correction
- All suggestions are validated against real data
- No misleading or non-existent institution suggestions

### 2. **Fast Performance**
- Sub-millisecond autocomplete responses
- Efficient Trie-based prefix matching
- Optimized SymSpell for spell correction

### 3. **Comprehensive Coverage**
- 11,598+ institutions across educational, financial, and medical sectors
- Multi-format CSV support
- Handles various naming conventions

### 4. **Intelligent Matching**
- Smart prefix handling with institutional prefixes
- Phrase-level spell correction
- Frequency-based ranking

### 5. **Production Ready**
- Singleton pattern for efficient resource usage
- Comprehensive error handling
- Clean separation of concerns
- Extensive documentation and type hints

---

## Error Handling

The system includes comprehensive error handling:

- **File not found**: Gracefully skips missing CSV files with warnings
- **Invalid data**: Filters out malformed or empty institution names
- **Memory limits**: Efficient data structures to handle large datasets
- **Encoding issues**: Proper UTF-8 handling for international names
- **Service unavailable**: Clear error states when services aren't initialized

---

## Future Enhancements

Potential areas for expansion:

1. **Fuzzy Matching**: Add phonetic matching for names with unusual spellings
2. **Ranking Improvements**: Incorporate usage statistics and popularity metrics
3. **Multi-language Support**: Handle institution names in multiple languages
4. **API Rate Limiting**: Add throttling for high-volume usage
5. **Caching Layer**: Implement Redis caching for frequently accessed suggestions
6. **Analytics**: Track search patterns and correction effectiveness

---

This system provides a robust, accurate, and fast solution for institution name autocomplete and spell correction, with a focus on data integrity and user experience.
