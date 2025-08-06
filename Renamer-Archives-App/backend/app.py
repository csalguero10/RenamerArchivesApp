from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from backend.classifier import classify_image
from backend.utils import save_metadata, load_metadata

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    responses = []
    for file in files:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        img_type = classify_image(filepath)
        responses.append({
            'filename': filename,
            'path': filepath,
            'type': img_type,
            'validated': False,
            'page_number': None
        })
    save_metadata(responses)
    return jsonify(responses)

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
def export():
    return send_from_directory('data', 'export.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
