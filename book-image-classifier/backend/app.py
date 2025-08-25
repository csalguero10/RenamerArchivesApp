
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

# Se mantienen las importaciones de tus módulos
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
    # Si los componentes fallan al iniciar, el servidor no debería arrancar.
    raise RuntimeError(f"Failed to initialize application components: {e}")

# --- Base de Datos en Memoria (para desarrollo) ---
# En un entorno de producción, esto debería ser reemplazado por una base de datos real
# como SQLite, PostgreSQL, etc.
images_db = {}

# --- Funciones de Ayuda ---
def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_new_filename(image):
    """Genera un nuevo nombre de archivo basado en metadatos (refactorizado para claridad)."""
    base_name, extension = os.path.splitext(image['original_filename'])
    new_name = f"{base_name} {image.get('type', 'unknown')}"
    
    if image.get('page_number') is not None:
        page_num_str = str(image['page_number'])
        if image.get('phantom_number', False):
            page_num_str = f"[{page_num_str}]"
        if image.get('number_exception'):
            page_num_str = f"{page_num_str} {image['number_exception']}"
        new_name += f" p {page_num_str}"
        
    return f"{new_name}{extension}"

# --- Rutas de la API ---

@app.route('/api/upload', methods=['POST'])
def upload_images():
    """Carga y procesa múltiples imágenes."""
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
                # Si una imagen falla, se informa del error pero se continúa con las demás.
                app.logger.error(f"Error procesando el archivo {file.filename}: {e}")
                # Podrías añadir un registro de errores aquí
    
    if not results:
        return jsonify({'error': 'Ninguno de los archivos pudo ser procesado. Verifique los formatos.'}), 400

    try:
        page_numberer.auto_number_pages(list(images_db.values()))
    except Exception as e:
        app.logger.warning(f"La auto-numeración falló después de la carga: {e}")

    return jsonify({
        'message': f'Se cargaron y procesaron {len(results)} imágenes.',
        'images': list(images_db.values())
    }), 201

@app.route('/api/images', methods=['GET'])
def get_images():
    """Obtiene la lista completa de imágenes, ordenadas por nombre de archivo."""
    # Convertir el diccionario a una lista y ordenar
    all_images = sorted(list(images_db.values()), key=lambda x: x['original_filename'])
    return jsonify({'images': all_images, 'total': len(all_images)})

@app.route('/api/images/<string:image_id>', methods=['PUT'])
def update_image(image_id):
    """Actualiza los metadatos de una sola imagen."""
    if image_id not in images_db:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    
    data = request.json
    if not data:
        return jsonify({'error': 'No se proporcionaron datos para actualizar'}), 400
        
    image = images_db[image_id]
    updateable_fields = ['type', 'page_number', 'number_type', 'number_exception', 'phantom_number', 'validated']
    
    for field in updateable_fields:
        if field in data:
            # Aquí se podría añadir validación de tipos de datos
            image[field] = data[field]
            
    return jsonify(image)

@app.route('/api/images/bulk-update', methods=['PUT'])
def bulk_update_images():
    """Actualiza un lote de imágenes con los mismos datos."""
    data = request.json
    if not data or 'image_ids' not in data or 'updates' not in data:
        return jsonify({'error': 'Formato de petición inválido. Se requieren "image_ids" y "updates"'}), 400
    
    image_ids = data['image_ids']
    updates = data['updates']
    updated_images = []
    
    for image_id in image_ids:
        if image_id in images_db:
            image = images_db[image_id]
            for field, value in updates.items():
                if field in ['type', 'page_number', 'number_type', 'number_exception', 'phantom_number', 'validated']:
                    image[field] = value
            updated_images.append(image)

    return jsonify({
        'message': f'Se actualizaron {len(updated_images)} imágenes.',
        'updated_images': updated_images
    })

@app.route('/api/images/<string:image_id>/file', methods=['GET'])
def get_image_file(image_id):
    """Sirve el archivo de una imagen específica."""
    if image_id not in images_db:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    
    image = images_db[image_id]
    try:
        directory = os.path.dirname(image['filepath'])
        filename = os.path.basename(image['filepath'])
        return send_from_directory(directory, filename)
    except FileNotFoundError:
        return jsonify({'error': 'El archivo de la imagen no se encuentra en el servidor'}), 404

# --- Endpoint de Exportación (AÑADIDO) ---
@app.route('/api/export', methods=['POST'])
def export_images():
    """Exporta las imágenes y metadatos seleccionados a un archivo zip."""
    data = request.json
    if not data or 'images' not in data or 'metadata' not in data:
        return jsonify({'error': 'Formato de petición de exportación inválido'}), 400

    image_ids = data['images']
    metadata_list = data['metadata']
    config = data.get('config', {})

    if not image_ids:
        return jsonify({'error': 'No hay imágenes para exportar'}), 400

    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_filename = f"book-export-{timestamp}.zip"
        zip_filepath = os.path.join(app.config['EXPORT_FOLDER'], zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Añadir archivo de metadatos
            if config.get('includeMetadata', True):
                # Usamos un diccionario para asegurar que cada imagen solo aparezca una vez
                final_metadata = {item['original_filename']: item for item in metadata_list}
                zipf.writestr('metadata.json', json.dumps(list(final_metadata.values()), indent=4))

            # 2. Añadir imágenes (renombradas si es necesario)
            if config.get('includeImages', True):
                for metadata_item in metadata_list:
                    # Encontrar el ID de la imagen a partir del nombre original
                    image_id = next((img['id'] for img in images_db.values() if img['original_filename'] == metadata_item['original_filename']), None)
                    
                    if image_id and image_id in images_db:
                        image_record = images_db[image_id]
                        filepath = image_record['filepath']
                        
                        # Determinar el nombre del archivo dentro del ZIP
                        arcname = metadata_item.get('new_filename') if config.get('renameFiles', True) else image_record['original_filename']
                        
                        if os.path.exists(filepath):
                            zipf.write(filepath, arcname=arcname)
                        else:
                            app.logger.warning(f"No se encontró el archivo para exportar: {filepath}")

        # La URL de descarga debe ser relativa para que el frontend la construya
        download_url = f"/exports/{zip_filename}"
        
        return jsonify({'success': True, 'download_url': download_url})

    except Exception as e:
        app.logger.error(f"Error durante la exportación: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ocurrió un error interno durante la exportación: {e}'}), 500

# --- Ruta para descargar archivos exportados (AÑADIDO) ---
@app.route('/exports/<path:filename>')
def download_export_file(filename):
    """Sirve un archivo desde la carpeta de exportaciones."""
    return send_from_directory(
        app.config['EXPORT_FOLDER'],
        filename,
        as_attachment=True
    )
    
# --- Arranque de la aplicación ---
if __name__ == '__main__':
    # Asegurarse de que los directorios necesarios existan al iniciar
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)