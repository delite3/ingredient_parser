# Install with: pip install paddlepaddle paddleocr
from paddleocr import PaddleOCR
import cv2

# Initialize with language and detection type
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Read image
img_path = 'product_label.jpg'
result = ocr.ocr(img_path, cls=True)

print(result)
# Extract text
all_text = ""
for line in result:
    for item in line:
        all_text += item[1][0] + " "

print("PaddleOCR Result:", all_text)