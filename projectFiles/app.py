from flask import Flask, render_template, request
from institution_processor import process_institution_pipeline # Import the processor
import json # Import json for pretty printing the dictionary

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    institution_data_str = None
    if request.method == 'POST':
        institution_name = request.form.get('institution_name')
        if institution_name:
            # Process the institution name
            processed_data = process_institution_pipeline(institution_name)
            # show as pure text for now
            institution_data_str = json.dumps(processed_data, indent=2)
        else:
            institution_data_str = "Please enter an institution name."
            
    return render_template('index.html', institution_data_str=institution_data_str)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
