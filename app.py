from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json

app = Flask(__name__)
CORS(app)

def validate_data(df):
    errors = []
    
    
    if 'id' in df.columns:
        duplicate_ids = df[df.duplicated('id', keep=False)]
        for idx in duplicate_ids.index:
            errors.append({'row': int(idx), 'field': 'id', 'error': 'Duplicate ID'})
    else:
        errors.append({'row': None, 'field': 'id', 'error': 'Missing "id" column'})
    
   
    if 'details' in df.columns:
        for i, val in enumerate(df['details']):
            try:
                json.loads(val)
            except:
                errors.append({'row': i, 'field': 'details', 'error': 'Invalid JSON'})

    return errors

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    result = {}

    for file in files:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        errors = validate_data(df)
        result[file.filename] = {
            'data': df.to_dict(orient='records'),
            'errors': errors
        }

    return jsonify(result)


@app.route('/generate-rules', methods=['POST'])
def generate_rules():
    text = request.json.get('text', '').lower()
    rules = {}

    if 'run together' in text or 'co-run' in text:
        import re
        task_ids = re.findall(r'\b(t\d+)\b', text)
        if task_ids:
            rules['coRun'] = [task_ids]

    if 'max' in text and 'parallel' in text:
        match = re.search(r'max(?:imum)?\s*(\d+).*group\s*(\w+)', text)
        if match:
            max_tasks = int(match.group(1))
            group = match.group(2)
            rules['loadLimit'] = {'group': group, 'max': max_tasks}

    if 'phase' in text:
        match = re.search(r'phase\s*(\d).*?t(\w+)', text)
        if match:
            phase = int(match.group(1))
            task_id = "T" + match.group(2)
            rules['preferredPhases'] = {task_id: [phase]}

    return jsonify(rules or {'error': 'No rules recognized'})

@app.route('/save-rules', methods=['POST'])
def save_rules():
    data = request.get_json()

    if not data or 'rules' not in data:
        return jsonify({"error": "Missing 'rules' in request"}), 400

    rules = data['rules']

    # ✅ Optional: Add rule validation logic here
    # For now, just echo the rules back
    print("Received rules:", rules)

    # ✅ You could write to a file like this:
    # with open("rules.json", "w") as f:
    #     json.dump(rules, f, indent=2)

    return jsonify({"status": "success", "message": "Rules received!"})


if __name__ == '__main__':
    app.run(debug=True)
