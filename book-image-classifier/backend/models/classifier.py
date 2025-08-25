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
        
        # Análisis mejorado de páginas blancas
        blank_result = self._detect_blank_page(image)
        if blank_result['is_blank']:
            return {'type': 'pagina_blanca', 'confidence': blank_result['confidence']}
        
        # Detección de texto
        text_info = self._detect_text(image)
        
        # Análisis de color y complejidad
        color_complexity = self._analyze_color_complexity(image)
        
        # Detección de patrones de calibración
        calibration_result = self._detect_calibration_target(image)
        if calibration_result['is_calibration']:
            return {'type': 'imagen_calibracion', 'confidence': calibration_result['confidence']}
        
        # Lógica de clasificación combinada
        return self._combine_content_features(text_info, color_complexity, blank_result)
    
    def _detect_blank_page(self, image):
        """
        Detección mejorada de páginas blancas usando múltiples criterios
        
        Args:
            image: Imagen en formato OpenCV
            
        Returns:
            dict: {'is_blank': bool, 'confidence': float, 'metrics': dict}
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Métrica 1: Desviación estándar de la intensidad
        std_dev = np.std(gray.astype(np.float32))
        
        # Métrica 2: Rango de intensidades
        min_intensity = np.min(gray)
        max_intensity = np.max(gray)
        intensity_range = max_intensity - min_intensity
        
        # Métrica 3: Análisis de histograma
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_norm = hist / hist.sum()
        
        # Calcular entropía del histograma (baja entropía = menos variación)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        
        # Métrica 4: Detección de bordes
        edges = cv2.Canny(gray, 30, 100)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Métrica 5: Porcentaje de píxeles muy claros
        very_light_pixels = np.sum(gray > 240) / gray.size
        
        # Métrica 6: Media de intensidad
        mean_intensity = np.mean(gray)
        
        # Criterios para página blanca (más restrictivos)
        metrics = {
            'std_dev': std_dev,
            'intensity_range': intensity_range,
            'entropy': entropy,
            'edge_density': edge_density,
            'very_light_pixels': very_light_pixels,
            'mean_intensity': mean_intensity
        }
        
        # Evaluación combinada
        is_blank = (
            std_dev < 5 and           # Muy poca variación
            intensity_range < 50 and  # Rango de colores muy pequeño
            entropy < 3 and           # Baja entropía
            edge_density < 0.001 and  # Muy pocos bordes
            very_light_pixels > 0.9 and # Mayoría de píxeles claros
            mean_intensity > 230      # Media de intensidad alta
        )
        
        # Calcular confianza basada en qué tan bien se cumplen los criterios
        confidence = 0.0
        if std_dev < 2: confidence += 0.2
        elif std_dev < 5: confidence += 0.15
        
        if intensity_range < 20: confidence += 0.2
        elif intensity_range < 50: confidence += 0.15
        
        if entropy < 2: confidence += 0.2
        elif entropy < 3: confidence += 0.15
        
        if edge_density < 0.0005: confidence += 0.2
        elif edge_density < 0.001: confidence += 0.15
        
        if very_light_pixels > 0.95: confidence += 0.2
        elif very_light_pixels > 0.9: confidence += 0.15
        
        return {
            'is_blank': is_blank,
            'confidence': min(confidence, 0.95) if is_blank else 0.0,
            'metrics': metrics
        }
    
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
        """
        Detectar patrones de calibración (IT8, X-Rite, etc.)
        
        Returns:
            dict: {'is_calibration': bool, 'confidence': float}
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar contornos rectangulares (patches de color típicos en targets)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangular_patches = 0
        regular_patches = 0
        patch_sizes = []
        
        for contour in contours:
            # Aproximar contorno
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            area = cv2.contourArea(contour)
            
            # Contar rectángulos de tamaño apropiado
            if len(approx) == 4 and 500 < area < 50000:
                rectangular_patches += 1
                patch_sizes.append(area)
                
                # Verificar regularidad (aspecto ratio cercano a 1:1)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                if 0.7 <= aspect_ratio <= 1.3:  # Aproximadamente cuadrado
                    regular_patches += 1
        
        # Análisis de color para targets de calibración
        color_variety = self._analyze_color_patches(image)
        
        # Criterios para target de calibración
        is_calibration = (
            rectangular_patches >= 10 and    # Muchos patches rectangulares
            regular_patches >= 8 and         # Muchos patches regulares
            color_variety > 0.7              # Alta variedad de colores
        )
        
        # Calcular confianza
        confidence = 0.0
        if rectangular_patches >= 15: confidence += 0.4
        elif rectangular_patches >= 10: confidence += 0.3
        
        if regular_patches >= 10: confidence += 0.3
        elif regular_patches >= 8: confidence += 0.2
        
        if color_variety > 0.8: confidence += 0.3
        elif color_variety > 0.7: confidence += 0.2
        
        return {
            'is_calibration': is_calibration,
            'confidence': min(confidence, 0.9) if is_calibration else 0.0,
            'rectangular_patches': rectangular_patches,
            'regular_patches': regular_patches,
            'color_variety': color_variety
        }
    
    def _analyze_color_patches(self, image):
        """Analizar variedad de colores en la imagen para detectar targets"""
        # Dividir imagen en grid para analizar parches de color
        height, width = image.shape[:2]
        grid_size = 8
        
        patch_height = height // grid_size
        patch_width = width // grid_size
        
        patch_colors = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                y1 = i * patch_height
                y2 = min((i + 1) * patch_height, height)
                x1 = j * patch_width
                x2 = min((j + 1) * patch_width, width)
                
                patch = image[y1:y2, x1:x2]
                
                # Calcular color promedio del patch
                mean_color = np.mean(patch.reshape(-1, 3), axis=0)
                patch_colors.append(mean_color)
        
        # Calcular variedad de colores
        patch_colors = np.array(patch_colors)
        
        # Calcular distancias entre colores
        color_distances = []
        for i in range(len(patch_colors)):
            for j in range(i+1, len(patch_colors)):
                distance = np.linalg.norm(patch_colors[i] - patch_colors[j])
                color_distances.append(distance)
        
        if not color_distances:
            return 0.0
        
        # Normalizar variedad (0-1)
        avg_distance = np.mean(color_distances)
        variety = min(avg_distance / 100.0, 1.0)  # Normalizar a 0-1
        
        return variety
    
    def _combine_content_features(self, text_info, color_complexity, blank_result):
        """Combinar características para clasificación final"""
        
        # Página blanca ya fue detectada arriba, pero verificar por si acaso
        if blank_result['is_blank']:
            return {'type': 'pagina_blanca', 'confidence': blank_result['confidence']}
        
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
        
        # Guardia: página con muy poco contenido pero no completamente blanca
        if (not text_info['has_text'] and 
            not color_complexity['is_complex'] and
            blank_result['metrics']['very_light_pixels'] > 0.8):
            return {'type': 'guardia', 'confidence': 0.6}
        
        # Por defecto: texto con baja confianza
        return {'type': 'texto', 'confidence': 0.4}