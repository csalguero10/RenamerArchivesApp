import cv2
import numpy as np
from PIL import Image, ImageStat
import os
from pathlib import Path

class ImageProcessor:
    """Utilidades para procesamiento de imágenes"""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    
    def get_image_info(self, image_path):
        """
        Obtener información básica de una imagen
        
        Args:
            image_path (str): Ruta a la imagen
            
        Returns:
            dict: Información de la imagen
        """
        try:
            with Image.open(image_path) as img:
                file_stats = os.stat(image_path)
                
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': file_stats.st_size,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    'dpi': img.info.get('dpi', (72, 72))
                }
                
        except Exception as e:
            raise ValueError(f"Cannot process image {image_path}: {str(e)}")
    
    def create_thumbnail(self, image_path, output_path, size=(200, 200)):
        """
        Crear miniatura de una imagen
        
        Args:
            image_path (str): Ruta a la imagen original
            output_path (str): Ruta para guardar la miniatura
            size (tuple): Tamaño de la miniatura (width, height)
        """
        try:
            with Image.open(image_path) as img:
                # Mantener aspecto ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Si la imagen tiene transparencia, usar fondo blanco
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img, mask=img.split()[-1])
                    img = background
                
                img.save(output_path, 'JPEG', quality=85)
                
        except Exception as e:
            raise ValueError(f"Cannot create thumbnail for {image_path}: {str(e)}")
    
    def preprocess_for_ocr(self, image_path):
        """
        Preprocesar imagen para mejorar el OCR
        
        Args:
            image_path (str): Ruta a la imagen
            
        Returns:
            numpy.ndarray: Imagen preprocesada
        """
        # Cargar imagen
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtro bilateral para reducir ruido manteniendo bordes
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Mejorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Aplicar threshold adaptativo
        processed = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return processed
    
    def detect_page_orientation(self, image_path):
        """
        Detectar orientación de la página
        
        Args:
            image_path (str): Ruta a la imagen
            
        Returns:
            dict: Información sobre orientación
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        height, width = image.shape[:2]
        
        # Determinar orientación básica
        if height > width:
            orientation = 'portrait'
            rotation_needed = 0
        else:
            orientation = 'landscape'
            rotation_needed = 0  # Podría necesitar rotación
        
        # Análisis más avanzado usando detección de texto
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar líneas horizontales y verticales
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        horizontal_score = np.sum(horizontal_lines > 0)
        vertical_score = np.sum(vertical_lines > 0)
        
        return {
            'orientation': orientation,
            'width': width,
            'height': height,
            'aspect_ratio': width / height,
            'rotation_needed': rotation_needed,
            'horizontal_lines_score': horizontal_score,
            'vertical_lines_score': vertical_score,
            'text_orientation': 'horizontal' if horizontal_score > vertical_score else 'vertical'
        }
    
    def calculate_image_stats(self, image_path):
        """
        Calcular estadísticas de la imagen para clasificación
        
        Args:
            image_path (str): Ruta a la imagen
            
        Returns:
            dict: Estadísticas de la imagen
        """
        try:
            with Image.open(image_path) as img:
                # Convertir a RGB si es necesario
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Estadísticas básicas
                stat = ImageStat.Stat(img)
                
                # Calcular histograma
                histogram = img.histogram()
                
                # Análisis de brillo
                brightness = sum(stat.mean) / 3
                
                # Análisis de contraste
                contrast = sum(stat.stddev) / 3
                
                # Detectar si es principalmente blanco/negro
                r_hist, g_hist, b_hist = histogram[:256], histogram[256:512], histogram[512:]
                
                # Píxeles muy claros (>240)
                white_pixels = sum(r_hist[240:]) + sum(g_hist[240:]) + sum(b_hist[240:])
                total_pixels = img.width * img.height * 3
                white_ratio = white_pixels / total_pixels
                
                # Píxeles muy oscuros (<15)
                black_pixels = sum(r_hist[:15]) + sum(g_hist[:15]) + sum(b_hist[:15])
                black_ratio = black_pixels / total_pixels
                
                return {
                    'brightness': brightness,
                    'contrast': contrast,
                    'white_ratio': white_ratio,
                    'black_ratio': black_ratio,
                    'mean_rgb': stat.mean,
                    'stddev_rgb': stat.stddev,
                    'is_grayscale': self._is_grayscale(stat.mean, stat.stddev),
                    'color_diversity': self._calculate_color_diversity(histogram)
                }
                
        except Exception as e:
            raise ValueError(f"Cannot calculate stats for {image_path}: {str(e)}")
    
    def _is_grayscale(self, mean_rgb, stddev_rgb):
        """Determinar si la imagen es principalmente en escala de grises"""
        # Si los valores RGB son similares, probablemente es escala de grises
        r_mean, g_mean, b_mean = mean_rgb
        r_std, g_std, b_std = stddev_rgb
        
        mean_diff = max(abs(r_mean - g_mean), abs(g_mean - b_mean), abs(r_mean - b_mean))
        std_diff = max(abs(r_std - g_std), abs(g_std - b_std), abs(r_std - b_std))
        
        return mean_diff < 10 and std_diff < 10
    
    def _calculate_color_diversity(self, histogram):
        """Calcular diversidad de colores usando entropía"""
        # Normalizar histograma
        total = sum(histogram)
        if total == 0:
            return 0
        
        normalized = [count / total for count in histogram if count > 0]
        
        # Calcular entropía de Shannon
        entropy = -sum(p * np.log2(p) for p in normalized if p > 0)
        
        return entropy
    
    def enhance_image_quality(self, image_path, output_path):
        """
        Mejorar calidad de imagen para mejor procesamiento
        
        Args:
            image_path (str): Ruta a la imagen original
            output_path (str): Ruta para guardar imagen mejorada
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # Reducir ruido
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        # Mejorar contraste
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Aplicar sharpening suave
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel * 0.1)
        
        # Guardar imagen mejorada
        cv2.imwrite(output_path, sharpened, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    def resize_for_web(self, image_path, output_path, max_width=1200):
        """
        Redimensionar imagen para visualización web manteniendo calidad
        
        Args:
            image_path (str): Ruta a la imagen original
            output_path (str): Ruta para guardar imagen redimensionada
            max_width (int): Ancho máximo en píxeles
        """
        try:
            with Image.open(image_path) as img:
                # Calcular nuevo tamaño manteniendo aspecto ratio
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Optimizar para web
                if img.mode in ('RGBA', 'LA'):
                    # Crear fondo blanco para transparencias
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                
                # Guardar optimizada
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                
        except Exception as e:
            raise ValueError(f"Cannot resize image {image_path}: {str(e)}")
    
    def validate_image_file(self, file_path):
        """
        Validar que un archivo sea una imagen válida
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            dict: Resultado de validación
        """
        try:
            # Verificar extensión
            extension = Path(file_path).suffix.lower()
            if extension not in self.supported_formats:
                return {
                    'valid': False,
                    'error': f'Unsupported format: {extension}',
                    'format': None
                }
            
            # Intentar abrir con PIL
            with Image.open(file_path) as img:
                # Verificar que se puede cargar completamente
                img.load()
                
                return {
                    'valid': True,
                    'error': None,
                    'format': img.format,
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'format': None
            }