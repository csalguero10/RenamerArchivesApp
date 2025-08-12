from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from PIL import Image

from models.classifier import ImageClassifier
from models.page_numbering import PageNumbering
from utils.image_processing import ImageProcessor
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Inicializar componentes
classifier = ImageClassifier()
page_numberer = PageNumbering()
image_processor = ImageProcessor()

# Almacenamiento en memoria para demo (en producción usar base de datos)
images_db = {}

@app.route('/api/upload', methods=['POST'])
def upload_images():
    """Cargar múltiples imágenes y clasificarlas automáticamente"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    results = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            # Generar ID único para la imagen
            image_id = str(uuid.uuid4())
            
            # Guardar archivo
            filename = secure_filename(file.filename)
            original_filename = filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Procesamiento inicial de imagen
            try:
                image_info = image_processor.get_image_info(filepath)
                
                # Clasificación automática
                classification = classifier.classify_image(filepath, original_filename)
                
                # Crear registro
                image_record = {
                    'id': image_id,
                    'original_filename': original_filename,
                    'filepath': filepath,
                    'type': classification['type'],
                    'confidence': classification['confidence'],
                    'validated': False,
                    'page_number': None,
                    'number_type': 'arabic',  # 'arabic' | 'roman'
                    'number_exception': '',   # 'bis', 'ter', etc.
                    'phantom_number': False,  # [ ]
                    'created_at': datetime.now().isoformat(),
                    'width': image_info['width'],
                    'height': image_info['height'],
                    'size_bytes': image_info['size_bytes']
                }
                
                images_db[image_id] = image_record
                results.append({
                    'id': image_id,
                    'original_filename': original_filename,
                    'type': classification['type'],
                    'confidence': classification['confidence']
                })
                
            except Exception as e:
                return jsonify({'error': f'Error processing {filename}: {str(e)}'}), 500
    
    # Auto-numerar páginas después de la carga
    try:
        page_numberer.auto_number_pages(images_db)
    except Exception as e:
        print(f"Warning: Auto-numbering failed: {e}")
    
    return jsonify({
        'message': f'Successfully uploaded {len(results)} images',
        'images': results
    })

@app.route('/api/images', methods=['GET'])
def get_images():
    """Obtener lista de todas las imágenes con filtros opcionales"""
    validated = request.args.get('validated')
    image_type = request.args.get('type')
    
    filtered_images = []
    
    for image in images_db.values():
        # Aplicar filtros
        if validated is not None:
            if validated.lower() == 'true' and not image['validated']:
                continue
            if validated.lower() == 'false' and image['validated']:
                continue
        
        if image_type and image['type'] != image_type:
            continue
            
        filtered_images.append(image)
    
    # Ordenar por nombre de archivo
    filtered_images.sort(key=lambda x: x['original_filename'])
    
    return jsonify({
        'images': filtered_images,
        'total': len(filtered_images)
    })

@app.route('/api/images/<image_id>', methods=['GET'])
def get_image(image_id):
    """Obtener información de una imagen específica"""
    if image_id not in images_db:
        return jsonify({'error': 'Image not found'}), 404
    
    return jsonify(images_db[image_id])

@app.route('/api/images/<image_id>', methods=['PUT'])
def update_image(image_id):
    """Actualizar metadatos de una imagen"""
    if image_id not in images_db:
        return jsonify({'error': 'Image not found'}), 404
    
    data = request.json
    image = images_db[image_id]
    
    # Campos actualizables
    updateable_fields = [
        'type', 'page_number', 'number_type', 'number_exception', 
        'phantom_number', 'validated'
    ]
    
    for field in updateable_fields:
        if field in data:
            image[field] = data[field]
    
    return jsonify(image)

@app.route('/api/images/<image_id>/file', methods=['GET'])
def get_image_file(image_id):
    """Servir archivo de imagen"""
    if image_id not in images_db:
        return jsonify({'error': 'Image not found'}), 404
    
    image = images_db[image_id]
    directory = os.path.dirname(image['filepath'])
    filename = os.path.basename(image['filepath'])
    
    return send_from_directory(directory, filename)

@app.route('/api/classify/<image_id>', methods=['POST'])
def reclassify_image(image_id):
    """Re-clasificar una imagen específica"""
    if image_id not in images_db:
        return jsonify({'error': 'Image not found'}), 404
    
    image = images_db[image_id]
    
    try:
        classification = classifier.classify_image(
            image['filepath'], 
            image['original_filename']
        )
        
        image['type'] = classification['type']
        image['confidence'] = classification['confidence']
        image['validated'] = False  # Reset validation after reclassification
        
        return jsonify({
            'id': image_id,
            'type': classification['type'],
            'confidence': classification['confidence']
        })
        
    except Exception as e:
        return jsonify({'error': f'Classification failed: {str(e)}'}), 500

@app.route('/api/validate/<image_id>', methods=['POST'])
def validate_image(image_id):
    """Marcar una imagen como validada"""
    if image_id not in images_db:
        return jsonify({'error': 'Image not found'}), 404
    
    images_db[image_id]['validated'] = True
    return jsonify({'message': 'Image validated successfully'})

@app.route('/api/renumber', methods=['POST'])
def renumber_pages():
    """Renumerar páginas automáticamente"""
    try:
        page_numberer.auto_number_pages(images_db)
        return jsonify({'message': 'Pages renumbered successfully'})
    except Exception as e:
        return jsonify({'error': f'Renumbering failed: {str(e)}'}), 500

@app.route('/api/export', methods=['GET'])
def export_metadata():
    """Exportar metadatos en formato JSON"""
    export_data = []
    
    for image in images_db.values():
        # Generar nuevo nombre de archivo
        new_filename = generate_new_filename(image)
        
        export_record = {
            'original_filename': image['original_filename'],
            'new_filename': new_filename,
            'type': image['type'],
            'validated': image['validated'],
            'page_number': str(image['page_number']) if image['page_number'] else 'False'
        }
        
        export_data.append(export_record)
    
    # Guardar archivo de exportación
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_filename = f'metadata_export_{timestamp}.json'
    export_path = os.path.join(app.config['EXPORT_FOLDER'], export_filename)
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return jsonify({
        'export_file': export_filename,
        'data': export_data,
        'total_images': len(export_data)
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas del proyecto"""
    stats = {
        'total_images': len(images_db),
        'validated': sum(1 for img in images_db.values() if img['validated']),
        'pending': sum(1 for img in images_db.values() if not img['validated']),
        'by_type': {}
    }
    
    # Contar por tipo
    for image in images_db.values():
        image_type = image['type']
        if image_type not in stats['by_type']:
            stats['by_type'][image_type] = 0
        stats['by_type'][image_type] += 1
    
    return jsonify(stats)

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])

def generate_new_filename(image):
    """Generar nuevo nombre de archivo según las especificaciones"""
    base_name = os.path.splitext(image['original_filename'])[0]
    extension = os.path.splitext(image['original_filename'])[1]
    
    # Agregar sufijo de tipo
    new_name = f"{base_name} {image['type']}"
    
    # Agregar número de página si aplica
    if image['page_number'] is not None:
        page_num = image['page_number']
        
        # Manejar números fantasma
        if image['phantom_number']:
            page_num = f"[{page_num}]"
        
        # Agregar excepción si existe
        if image['number_exception']:
            page_num = f"{page_num} {image['number_exception']}"
        
        new_name += f" p {page_num}"
    
    return f"{new_name}{extension}"

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)

