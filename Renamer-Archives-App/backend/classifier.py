from PIL import Image
import numpy as np

def classify_image(path):
    img = Image.open(path).convert('L')
    arr = np.array(img)
    white_ratio = np.sum(arr > 245) / arr.size
    if white_ratio > 0.95:
        return 'página blanca'
    elif white_ratio < 0.3:
        return 'ilustración'
    else:
        return 'texto'
