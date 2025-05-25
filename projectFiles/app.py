from flask import Flask, render_template, request, jsonify
from institution_processor import process_institution_pipeline # Import the processor
import json # Import json for pretty printing the dictionary
from symspellpy import SymSpell, Verbosity
import pandas as pd
import os

app = Flask(__name__)

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = 'spell_check/symspell_dict.txt'
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

df = pd.read_csv('spell_check/list_of_univs.csv', usecols=[5])
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
    term = request.args.get('term', '').lower()

    matches = [name for name in institution_names if term in name.lower()]
    return jsonify(matches[:10])  # Return up to 10 matches


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
