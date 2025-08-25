import re
from typing import Dict, List, Optional

class PageNumbering:
    """Sistema de numeración automática de páginas"""
    
    def __init__(self):
        # Tipos de página que NO llevan numeración
        self.non_numbered_types = {
            'portada', 'contraportada', 'guardia', 'pagina_blanca', 
            'frontispicio', 'referencia'
        }
        
        # Tipos que SÍ llevan numeración
        self.numbered_types = {
            'texto', 'ilustracion', 'imagen_calibracion', 'inserto'
        }
        
        # Numeración romana (para páginas preliminares)
        self.roman_numerals = [
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'
        ]
    
    def auto_number_pages(self, images_db: Dict) -> None:
        """Numera páginas, manejando el caso de que no haya imágenes."""
        if not images_db:
            # Si no hay imágenes, no hay nada que hacer.
            return

        sorted_images = sorted(
            images_db.values(),
            key=lambda x: x['original_filename']
        )
    
    def _analyze_book_structure(self, images: List[Dict]) -> Dict:
        """
        Analizar la estructura del libro para determinar esquema de numeración
        
        Args:
            images (List[Dict]): Lista ordenada de imágenes
            
        Returns:
            Dict: Información sobre la estructura del libro
        """
        structure = {
            'has_preliminaries': False,
            'preliminary_end_index': 0,
            'main_content_start_index': 0,
            'total_images': len(images)
        }
        
        # Buscar inicio del contenido principal
        for i, image in enumerate(images):
            if image['type'] in self.numbered_types:
                structure['main_content_start_index'] = i
                break
        
        # Determinar si hay páginas preliminares
        preliminary_count = 0
        for i in range(structure['main_content_start_index']):
            if images[i]['type'] in ['frontispicio', 'guardia']:
                preliminary_count += 1
        
        if preliminary_count > 0:
            structure['has_preliminaries'] = True
            structure['preliminary_end_index'] = structure['main_content_start_index'] - 1
        
        return structure
    
    def _apply_numbering(self, images: List[Dict], structure: Dict) -> None:
        """
        Aplicar numeración a las páginas según la estructura identificada
        
        Args:
            images (List[Dict]): Lista ordenada de imágenes
            structure (Dict): Estructura del libro
        """
        # Contadores de páginas
        roman_counter = 1
        arabic_counter = 1
        
        for i, image in enumerate(images):
            # Resetear numeración
            image['page_number'] = None
            image['number_type'] = 'arabic'
            image['phantom_number'] = False
            
            # Páginas sin numeración
            if image['type'] in self.non_numbered_types:
                continue
            
            # Determinar tipo de numeración
            if (structure['has_preliminaries'] and 
                i <= structure['preliminary_end_index'] and
                image['type'] in self.numbered_types):
                
                # Numeración romana para preliminares
                if roman_counter <= len(self.roman_numerals):
                    image['page_number'] = self.roman_numerals[roman_counter - 1]
                    image['number_type'] = 'roman'
                    roman_counter += 1
                else:
                    # Fallback a arábigos si se exceden los romanos
                    image['page_number'] = arabic_counter
                    image['number_type'] = 'arabic'
                    arabic_counter += 1
            
            elif image['type'] in self.numbered_types:
                # Numeración arábiga para contenido principal
                image['page_number'] = arabic_counter
                image['number_type'] = 'arabic'
                arabic_counter += 1
    
    def renumber_from_page(self, images_db: Dict, start_image_id: str, 
                        start_number: int, number_type: str = 'arabic') -> None:
        """
        Renumerar páginas a partir de una página específica
        
        Args:
            images_db (Dict): Base de datos de imágenes
            start_image_id (str): ID de la imagen desde donde empezar
            start_number (int): Número inicial
            number_type (str): Tipo de numeración ('arabic' o 'roman')
        """
        if start_image_id not in images_db:
            raise ValueError("Image ID not found")
        
        # Ordenar imágenes por nombre de archivo
        sorted_images = sorted(
            images_db.values(),
            key=lambda x: x['original_filename']
        )
        
        # Encontrar índice de inicio
        start_index = None
        for i, image in enumerate(sorted_images):
            if image['id'] == start_image_id:
                start_index = i
                break
        
        if start_index is None:
            raise ValueError("Start image not found in sorted list")
        
        # Aplicar renumeración
        current_number = start_number
        
        for i in range(start_index, len(sorted_images)):
            image = sorted_images[i]
            
            if image['type'] in self.numbered_types:
                if number_type == 'roman' and current_number <= len(self.roman_numerals):
                    image['page_number'] = self.roman_numerals[current_number - 1]
                else:
                    image['page_number'] = current_number
                
                image['number_type'] = number_type
                current_number += 1
    
    def detect_page_exceptions(self, images_db: Dict) -> List[Dict]:
        """
        Detectar posibles excepciones en la numeración (bis, ter, etc.)
        
        Args:
            images_db (Dict): Base de datos de imágenes
            
        Returns:
            List[Dict]: Lista de posibles excepciones detectadas
        """
        exceptions = []
        
        # Buscar patrones en nombres de archivo
        exception_patterns = {
            'bis': [r'\bbis\b', r'_bis', r'-bis'],
            'ter': [r'\bter\b', r'_ter', r'-ter'],
            'quater': [r'\bquater\b', r'_quater', r'-quater']
        }
        
        for image in images_db.values():
            filename_lower = image['original_filename'].lower()
            
            for exception_type, patterns in exception_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, filename_lower):
                        exceptions.append({
                            'image_id': image['id'],
                            'filename': image['original_filename'],
                            'detected_exception': exception_type,
                            'confidence': 0.8
                        })
                        break
        
        return exceptions
    
    def apply_exception(self, images_db: Dict, image_id: str, 
                    base_number: int, exception: str) -> None:
        """
        Aplicar una excepción de numeración a una página específica
        
        Args:
            images_db (Dict): Base de datos de imágenes
            image_id (str): ID de la imagen
            base_number (int): Número base
            exception (str): Tipo de excepción ('bis', 'ter', etc.)
        """
        if image_id not in images_db:
            raise ValueError("Image ID not found")
        
        image = images_db[image_id]
        image['page_number'] = base_number
        image['number_exception'] = exception
    
    def set_phantom_number(self, images_db: Dict, image_id: str, 
                        page_number: int) -> None:
        """
        Marcar una página con número fantasma (no impreso pero secuencial)
        
        Args:
            images_db (Dict): Base de datos de imágenes
            image_id (str): ID de la imagen
            page_number (int): Número de página
        """
        if image_id not in images_db:
            raise ValueError("Image ID not found")
        
        image = images_db[image_id]
        image['page_number'] = page_number
        image['phantom_number'] = True
    
    def validate_numbering_sequence(self, images_db: Dict) -> List[Dict]:
        """
        Validar que la secuencia de numeración sea correcta
        
        Args:
            images_db (Dict): Base de datos de imágenes
            
        Returns:
            List[Dict]: Lista de problemas encontrados
        """
        problems = []
        
        # Obtener páginas numeradas ordenadas
        numbered_pages = [
            img for img in images_db.values() 
            if img['page_number'] is not None and img['type'] in self.numbered_types
        ]
        
        numbered_pages.sort(key=lambda x: x['original_filename'])
        
        # Verificar secuencia arábiga
        arabic_pages = [p for p in numbered_pages if p['number_type'] == 'arabic']
        expected_arabic = 1
        
        for page in arabic_pages:
            if page['page_number'] != expected_arabic and not page.get('number_exception'):
                problems.append({
                    'type': 'sequence_break',
                    'image_id': page['id'],
                    'expected': expected_arabic,
                    'found': page['page_number'],
                    'message': f"Expected page {expected_arabic}, found {page['page_number']}"
                })
            expected_arabic += 1
        
        # Verificar secuencia romana
        roman_pages = [p for p in numbered_pages if p['number_type'] == 'roman']
        for i, page in enumerate(roman_pages):
            expected_roman = self.roman_numerals[i] if i < len(self.roman_numerals) else f">{len(self.roman_numerals)}"
            
            if page['page_number'] != expected_roman:
                problems.append({
                    'type': 'roman_sequence_break',
                    'image_id': page['id'],
                    'expected': expected_roman,
                    'found': page['page_number'],
                    'message': f"Expected roman {expected_roman}, found {page['page_number']}"
                })
        
        return problems