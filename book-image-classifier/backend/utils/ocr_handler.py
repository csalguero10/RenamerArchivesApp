import pytesseract
from PIL import Image
import os

class OCRHandler:
    def __init__(self):
        # Configurar path de Tesseract si es necesario
        tesseract_cmd = os.environ.get('TESSERACT_CMD')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_text(self, image_path, lang='spa+eng'):
        try:
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img, lang=lang)
                return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            return ""