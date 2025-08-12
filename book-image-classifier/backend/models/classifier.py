import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
import os
from pathlib import Path

class ImageClassifier:
    """Clasificador automático de páginas de libros"""
    
    def __init__(self):
        self.page_types = {
            'portada': 'portada',
            'contraportada': 'contraportada', 
            'guardia': 'guardia',
            'frontispicio': 'frontispicio',
            'pagina_blanca': 'pagina_blanca',
            'texto': 'texto',
            'ilustracion': 'ilustracion',
            'imagen_calibracion': 'imagen_calibracion',
            'inserto': 'inserto',
            'referencia': 'referencia'
        }
        
        # Configurar Tesseract si está disponible
        self.ocr_available = self._check_ocr_availability()
    
    def _check_ocr_availability(self):
        """Verificar si Tesseract está disponible"""
        try:
            pytesseract.image_to_string(Image.new('RGB', (100, 100), color='white'))
            return True
        except:
            print("Warning: Tesseract OCR not available. Text detection will be limited.")
            return False
    
    def classify_image(self, image_path, original_filename):
        """
        Clasificar una imagen automáticamente
        
        Args:
            image_path (str): Ruta a la imagen
            original_filename (str): Nombre original del archivo
            
        Returns:
            dict: {'type': str, 'confidence': float}
        """
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Análisis basado en nombre de archivo (alta confianza)
            filename_result = self._classify_by_filename(original_filename)
            if filename_result['confidence'] > 0.8:
                return filename_result
            
            # Análisis de contenido de imagen
            content_result = self._classify_by_content(image)
            
            # Combinar resultados
            if filename_result['confidence'] > content_result['confidence']:
                return filename_result
            else:
                return content_result
                
        except Exception as e:
            print(f"Classification error for {image_path}: {e}")
            return {'type': 'texto', 'confidence': 0.1}  # Fallback
    
    def _classify_by_filename(self, filename):
        """Clasificar basándose en patrones del nombre de archivo"""
        filename_lower = filename.lower()
        
        # Patrones específicos con alta confianza
        patterns = {
            'portada': [r'00001', r'_001\b', r'cover', r'portada'],
            'contraportada': [r'final', r'back', r'contraportada', r'ultimo'],
            'guardia': [r'00002', r'_002\b', r'guard', r'guardia'],
            'inserto': [r'\bins\b', r'insert', r'inserto'],
            'referencia': [r'\bref\b', r'reference', r'target', r'it8', r'calibr'],
            'imagen_calibracion': [r'target', r'it8', r'calibr', r'color.*chart']
        }
        
        for page_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, filename_lower):
                    return {'type': page_type, 'confidence': 0.9}
        
        # Patrones de posición (menor confianza)
        if re.search(r'00001|_001\b', filename_lower):
            return {'type': 'portada', 'confidence': 0.7}
        
        if re.search(r'00002|_002\b', filename_lower):
            return {'type': 'guardia', 'confidence': 0.6}
        
        return {'type': 'texto', 'confidence': 0.3}
    
    def _classify_by_content(self, image):
        """Clasificar basándose en el contenido visual de la imagen"""
        height, width = image.shape[:2]
        
        # Análisis de contenido blanco
        white_ratio = self._calculate_white_ratio(image)
        if white_ratio > 0.9:
            return {'type': 'pagina_blanca', 'confidence': 0.8}
        
        # Detección de texto
        text_info = self._detect_text(image)
        
        # Análisis de color y complejidad
        color_complexity = self._analyze_color_complexity(image)
        
        # Detección de patrones de calibración
        if self._detect_calibration_target(image):
            return {'type': 'imagen_calibracion', 'confidence': 0.9}
        
        # Lógica de clasificación combinada
        return self._combine_content_features(text_info, color_complexity, white_ratio)
    
    def _calculate_white_ratio(self, image):
        """Calcular el porcentaje de píxeles blancos en la imagen"""
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Umbral para considerarlos "blancos"
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        white_pixels = np.sum(binary == 255)
        total_pixels = binary.size
        
        return white_pixels / total_pixels
    
    def _detect_text(self, image):
        """Detectar texto en la imagen"""
        if not self.ocr_available:
            return {'has_text': False, 'text_lines': 0, 'confidence': 0}
        
        try:
            # Preprocesar imagen para OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar threshold adaptativo
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Extraer texto
            text = pytesseract.image_to_string(processed, lang='spa+eng')
            
            # Analizar resultado
            text_lines = len([line for line in text.split('\n') if line.strip()])
            word_count = len(text.split())
            
            # Detectar si es título centrado (posible frontispicio)
            is_centered_title = self._detect_centered_title(text, image.shape)
            
            return {
                'has_text': word_count > 3,
                'text_lines': text_lines,
                'word_count': word_count,
                'is_centered_title': is_centered_title,
                'confidence': min(word_count / 10, 1.0)  # Máximo 1.0
            }
            
        except Exception as e:
            print(f"OCR error: {e}")
            return {'has_text': False, 'text_lines': 0, 'confidence': 0}
    
    def _detect_centered_title(self, text, image_shape):
        """Detectar si el texto parece ser un título centrado"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) <= 3 and len(lines) >= 1:
            # Pocas líneas podrían indicar un título
            total_chars = sum(len(line) for line in lines)
            if 10 <= total_chars <= 100:  # Longitud típica de título
                return True
        
        return False
    
    def _analyze_color_complexity(self, image):
        """Analizar complejidad de color y formas"""
        # Calcular histograma de colores
        hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        # Normalizar histograma
        hist_norm = hist / hist.sum()
        
        # Calcular entropía (medida de diversidad de colores)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        
        # Detectar bordes para analizar complejidad de formas
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        return {
            'color_entropy': entropy,
            'edge_density': edge_density,
            'is_complex': entropy > 12 or edge_density > 0.1
        }
    
    def _detect_calibration_target(self, image):
        """Detectar patrones de calibración (IT8, X-Rite, etc.)"""
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar contornos rectangulares (patches de color típicos en targets)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangular_patches = 0
        for contour in contours:
            # Aproximar contorno
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Contar rectángulos de tamaño apropiado
            if len(approx) == 4 and cv2.contourArea(contour) > 100:
                rectangular_patches += 1
        
        # Si hay muchos parches rectangulares, probablemente es un target
        return rectangular_patches > 10
    
    def _combine_content_features(self, text_info, color_complexity, white_ratio):
        """Combinar características para clasificación final"""
        
        # Página blanca (ya verificada arriba, pero por si acaso)
        if white_ratio > 0.85:
            return {'type': 'pagina_blanca', 'confidence': 0.8}
        
        # Frontispicio: texto centrado, poca complejidad visual
        if (text_info.get('is_centered_title', False) and 
            not color_complexity['is_complex']):
            return {'type': 'frontispicio', 'confidence': 0.7}
        
        # Ilustración: alta complejidad visual, poco texto
        if (color_complexity['is_complex'] and 
            text_info['word_count'] < 10):
            return {'type': 'ilustracion', 'confidence': 0.6}
        
        # Texto: tiene texto significativo
        if text_info['has_text'] and text_info['word_count'] > 10:
            return {'type': 'texto', 'confidence': 0.7}
        
        # Por defecto: texto con baja confianza
        return {'type': 'texto', 'confidence': 0.4}