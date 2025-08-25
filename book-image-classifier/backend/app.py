from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import zipfile
import io

# Importaciones de módulos
from models.classifier import ImageClassifier
from models.page_numbering import PageNumbering
from utils.image_processing import ImageProcessor
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# --- Componentes de la aplicación ---
try:
    classifier = ImageClassifier()
    page_numberer = PageNumbering()
    image_processor = ImageProcessor()
except Exception as e:
    raise RuntimeError(f"Failed to initialize application components: {e}")

# --- Base de Datos en Memoria (para desarrollo) ---
images_db = {}

# --- Funciones de Ayuda ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Rutas de la API ---

@app.route('/api/upload', methods=['POST'])
def upload_images():
    if 'files' not in request.files:
        return jsonify({'error': 'No se proporcionaron archivos en la clave "files"'}), 400
    
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
    results = []
    for file in files:
        if file and allowed_file(file.filename):
            try:
                image_id = str(uuid.uuid4())
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{image_id}_{filename}")
                file.save(filepath)

                image_info = image_processor.get_image_info(filepath)
                classification = classifier.classify_image(filepath, filename)
                
                image_record = {
                    'id': image_id,
                    'original_filename': filename,
                    'filepath': filepath,
                    'type': classification['type'],
                    'confidence': classification['confidence'],
                    'validated': False,
                    'page_number': None,
                    'number_type': 'arabic',
                    'number_exception': '',
                    'phantom_number': False,
                    'created_at': datetime.now().isoformat(),
                    **image_info
                }
                
                images_db[image_id] = image_record
                results.append(image_record)
            except Exception as e:
                app.logger.error(f"Error procesando el archivo {file.filename}: {e}")

    if not results:
        return jsonify({'error': 'Ninguno de los archivos pudo ser procesado.'}), 400

    try:
        # AQUÍ ESTÁ LA CORRECCIÓN
        page_numberer.auto_number_pages(images_db)
    except Exception as e:
        app.logger.warning(f"La auto-numeración falló después de la carga: {e}")

    all_images = sorted(list(images_db.values()), key=lambda x: x['original_filename'])
    return jsonify({
        'message': f'Se cargaron y procesaron {len(results)} imágenes.',
        'images': all_images
    }), 201


@app.route('/api/images', methods=['GET'])
def get_images():
    all_images = sorted(list(images_db.values()), key=lambda x: x['original_filename'])
    return jsonify({'images': all_images, 'total': len(all_images)})

@app.route('/api/images/<string:image_id>', methods=['PUT'])
def update_image(image_id):
    if image_id not in images_db:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    
    data = request.json
    if not data:
        return jsonify({'error': 'No se proporcionaron datos para actualizar'}), 400
        
    image = images_db[image_id]
    updateable_fields = ['type', 'page_number', 'number_type', 'number_exception', 'phantom_number', 'validated']
    
    for field in updateable_fields:
        if field in data:
            image[field] = data[field]
            
    return jsonify(image)

@app.route('/api/images/bulk-update', methods=['PUT'])
def bulk_update_images():
    data = request.json
    if not data or 'image_ids' not in data or 'updates' not in data:
        return jsonify({'error': 'Formato de petición inválido.'}), 400
    
    image_ids = data['image_ids']
    updates = data['updates']
    updated_images = []
    
    for image_id in image_ids:
        if image_id in images_db:
            image = images_db[image_id]
            for field, value in updates.items():
                if field in ['type', 'page_number', 'validated']:
                    image[field] = value
            updated_images.append(image)

    return jsonify({
        'message': f'Se actualizaron {len(updated_images)} imágenes.',
        'updated_images': updated_images
    })

@app.route('/api/images/<string:image_id>/file', methods=['GET'])
def get_image_file(image_id):
    if image_id not in images_db:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    
    image = images_db[image_id]
    try:
        directory = os.path.dirname(image['filepath'])
        filename = os.path.basename(image['filepath'])
        return send_from_directory(directory, filename)
    except FileNotFoundError:
        return jsonify({'error': 'El archivo de la imagen no se encuentra en el servidor'}), 404

@app.route('/api/export', methods=['POST'])
def export_images():
    data = request.json
    if not data or 'images' not in data or 'metadata' not in data:
        return jsonify({'error': 'Formato de petición de exportación inválido'}), 400

    image_ids_to_export = data['images']
    metadata_list = data['metadata']
    config = data.get('config', {})

    if not image_ids_to_export:
        return jsonify({'error': 'No hay imágenes para exportar'}), 400

    try:
        metadata_map = {item['id']: item for item in metadata_list}

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_filename = f"book-export-{timestamp}.zip"
        zip_filepath = os.path.join(app.config['EXPORT_FOLDER'], zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if config.get('includeMetadata', True):
                zipf.writestr('metadata.json', json.dumps(metadata_list, indent=4))

            if config.get('includeImages', True):
                for image_id in image_ids_to_export:
                    if image_id in images_db and image_id in metadata_map:
                        image_record = images_db[image_id]
                        metadata_item = metadata_map[image_id]
                        
                        filepath = image_record['filepath']
                        arcname = metadata_item.get('new_filename', image_record['original_filename'])
                        
                        if os.path.exists(filepath):
                            zipf.write(filepath, arcname=arcname)
                        else:
                            app.logger.warning(f"Archivo no encontrado para exportar: {filepath}")

        download_url = f"/exports/{zip_filename}"
        return jsonify({'success': True, 'download_url': download_url})

    except Exception as e:
        app.logger.error(f"Error durante la exportación: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno durante la exportación: {e}'}), 500

@app.route('/exports/<path:filename>')
def download_export_file(filename):
    return send_from_directory(
        app.config['EXPORT_FOLDER'],
        filename,
        as_attachment=True
    )

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)