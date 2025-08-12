import os
from pathlib import Path

class Config:
    """Configuración base de la aplicación"""
    
    # Directorios base
    BASE_DIR = Path(__file__).parent
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    EXPORT_FOLDER = BASE_DIR / 'exports'
    
    # Límites de archivos
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tiff', 'tif'}
    
    # Configuración de clasificación
    CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.7
    
    # Patrones para detección automática
    FILENAME_PATTERNS = {
        'portada': ['00001', '_001', 'cover', 'portada'],
        'contraportada': ['final', 'back', 'contraportada'],
        'guardia': ['00002', '_002', 'guard'],
        'inserto': ['ins', 'insert'],
        'referencia': ['ref', 'reference', 'target', 'it8']
    }
    
    # Configuración OCR
    OCR_CONFIG = {
        'lang': 'spa+eng',  # Español e inglés
        'psm': 6,           # Modo de segmentación de página
        'oem': 3            # Modo de motor OCR
    }
    
    # Umbrales para clasificación automática
    THRESHOLDS = {
        'white_page_threshold': 0.9,      # % de píxeles blancos
        'text_confidence_threshold': 60,   # Confianza mínima OCR
        'target_pattern_threshold': 0.8    # Confianza detección de target
    }
    
    # Configuración de numeración
    NUMBERING = {
        'roman_numerals': ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'],
        'exceptions': ['bis', 'ter', 'quater'],
        'auto_number_types': ['texto', 'ilustracion', 'imagen_calibracion', 'inserto']
    }

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    ENV = 'production'
    
    # En producción, usar variables de entorno
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', Config.UPLOAD_FOLDER)
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER', Config.EXPORT_FOLDER)

# Mapeo de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}