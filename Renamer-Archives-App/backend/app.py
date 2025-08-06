from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json

app = Flask(__name__)
CORS(app)  # habilita CORS para todos los dominios

UPLOAD_FOLDER = 'backend/static/uploads'
DATA_FOLDER = 'backend/data'
METADATA_FILE = os.path.join(DATA_FOLDER, 'metadata.json')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_metadata(data):
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    metadata = load_metadata()

    for file in files:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        # Aquí puedes agregar la función de clasificación real o dejarlo vacío
        file_type = 'texto'  # ejemplo estático, puedes reemplazarlo con clasificación automática
        metadata.append({
            'filename': filename,
            'path': filepath,
            'type': file_type,
            'validated': False,
            'page_number': None
        })
    save_metadata(metadata)
    return jsonify(metadata)

@app.route('/images', methods=['GET'])
def list_images():
    return jsonify(load_metadata())

@app.route('/validate', methods=['POST'])
def validate_image():
    data = request.get_json()
    metadata = load_metadata()
    for item in metadata:
        if item['filename'] == data['filename']:
            item.update(data)
    save_metadata(metadata)
    return jsonify({"message": "updated"})

@app.route('/export', methods=['GET'])
def export_metadata():
    return send_from_directory(DATA_FOLDER, 'metadata.json', as_attachment=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
