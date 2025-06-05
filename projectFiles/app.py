from flask import Flask, render_template, request, jsonify
from institution_processor import process_institution_pipeline # Import the processor
import json # Import json for pretty printing the dictionary
import pandas as pd
import os
from service_factory import initialize_autocomplete_with_all_institutions, get_autocomplete_service
from spell_check import SpellCorrectionService, DictionaryManager

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize spell checking service
dictionary_path = os.path.join(BASE_DIR, 'spell_check', 'symspell_dict.txt')
spell_service = SpellCorrectionService(dictionary_path=dictionary_path)

# Check if spell correction is available
if not spell_service.is_initialized:
    print("Warning: Spell checking service is not initialized.")
    print("Spell checking will be disabled, but autocomplete will still work.")

# Initialize autocomplete service with all institution types
initialize_autocomplete_with_all_institutions(BASE_DIR)
autocomplete_service = get_autocomplete_service()

# Keep the original list for backward compatibility if needed
csv_path = os.path.join(BASE_DIR, 'spell_check', 'list_of_univs.csv')
df = pd.read_csv(csv_path, usecols=[5])
institution_names = df['name'].tolist()

@app.route('/', methods=['GET', 'POST'])
def index():

    institution_data_str = None
    corrected = None

    if request.method == 'POST':
        institution_name = request.form.get('institution_name')
        if institution_name:

            # Check for spelling corrections if service is initialized
            if spell_service.is_initialized:
                corrections = spell_service.get_corrections_for_phrase(institution_name)
                if corrections:
                    corrected = corrections[0]['corrected_phrase']
                    print(f"Spell correction: '{institution_name}' → '{corrected}'")
                    # TODO: return the suggestions to the user

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
    Falls back to spell correction if no matches found.
    """
    term = request.args.get('term', '').strip()
    
    if not term:
        return jsonify([])    # Get suggestions from the Trie-based autocomplete service (now includes spell correction)
    result = autocomplete_service.get_suggestions(term, max_suggestions=5)
    
    # Return the full result object for new format support
    if isinstance(result, dict):
        return jsonify(result)
    else:
        # Fallback for old format
        return jsonify(result)


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


@app.route('/spell-check', methods=['GET'])
def spell_check():
    """
    Spell correction endpoint for getting "did you mean" suggestions.
    Returns spell correction suggestions for misspelled institution names.
    """
    term = request.args.get('term', '').strip()
    
    if not term:
        return jsonify({
            'corrections': [],
            'original_query': term,
            'message': 'Empty query'
        })
    
    # Get spell corrections directly
    corrections = autocomplete_service.get_spell_corrections(term, max_suggestions=5)
    
    return jsonify({
        'corrections': corrections,
        'original_query': term,
        'message': f'Found {len(corrections)} suggestions' if corrections else 'No suggestions found'
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
