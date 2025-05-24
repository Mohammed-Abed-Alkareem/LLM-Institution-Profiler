from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    institution = None
    if request.method == 'POST':
        institution = request.form.get('institution_name')
        # TODO: here you have the institution name from the user
        # You can process it or store it as needed
    return render_template('index.html', institution=institution)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
