from flask import Flask, render_template, request, jsonify
from institution_processor import process_institution_pipeline # Import the processor
import json # Import json for pretty printing the dictionary
from symspellpy import SymSpell, Verbosity
import pandas as pd
import os
from autocomplete import initialize_autocomplete, get_autocomplete_service

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize SymSpell for spell checking
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = os.path.join(BASE_DIR, 'spell_check', 'symspell_dict.txt') # Renamed from symspell_dict_new.txt

# Load dictionary with proper encoding handling
try:
    sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1, encoding='utf-8')
    print(f"Successfully loaded symspell dictionary with {sym_spell.word_count} words") # Corrected to .word_count (attribute)
except Exception as e:
    print(f"Warning: Could not load symspell dictionary: {e}")
    print("Spell checking will be disabled, but autocomplete will still work.")

# Initialize autocomplete service with Trie
csv_path = os.path.join(BASE_DIR, 'spell_check', 'list_of_univs.csv')
initialize_autocomplete(csv_path)
autocomplete_service = get_autocomplete_service()

# Keep the original list for backward compatibility if needed
df = pd.read_csv(csv_path, usecols=[5])
institution_names = df['name'].tolist()

@app.route('/', methods=['GET', 'POST'])
def index():

    institution_data_str = None
    corrected = None

    if request.method == 'POST':
        institution_name = request.form.get('institution_name')
        if institution_name:

            # Check for spelling corrections
            suggestions = sym_spell.lookup_compound(institution_name, max_edit_distance=2)
            if suggestions:
                print("Suggestions:", suggestions)
                #TODO: return the suggestions to the user

            # Process the institution name
            processed_data = process_institution_pipeline(institution_name)
            # show as pure text for now
            institution_data_str = json.dumps(processed_data, indent=2)
        else:
            institution_data_str = "Please enter an institution name."
            
    return render_template('index.html', institution_data_str=institution_data_str)


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    """
    Autocomplete endpoint using Trie-based search for fast prefix matching.
    Returns top 5 university suggestions for the given prefix.
    """
    term = request.args.get('term', '').strip()
    
    if not term:
        return jsonify([])
    
    # Get suggestions from the Trie-based autocomplete service
    suggestions = autocomplete_service.get_suggestions(term, max_suggestions=5)
    
    return jsonify(suggestions)


@app.route('/autocomplete/debug', methods=['GET'])
def autocomplete_debug():
    """
    Debug endpoint to check autocomplete service status and statistics.
    """
    stats = autocomplete_service.get_stats()
    sample_suggestions = autocomplete_service.get_suggestions('university', max_suggestions=3)
    
    debug_info = {
        'service_stats': stats,
        'sample_suggestions_for_university': sample_suggestions,
        'service_initialized': autocomplete_service.is_initialized
    }
    
    return jsonify(debug_info)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
