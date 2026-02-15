# Install with: pip install pytesseract
import pytesseract
import cv2

# Configure Tesseract for list-type content
custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'

# Read and preprocess image
image = cv2.imread('product_label.jpg')
#gray = cv2.cvtColor(image, cv2.threshold(cv2.GaussianBlur(
#    cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])

# Run OCR
text = pytesseract.image_to_string(image, config=custom_config)
print("Tesseract Result:", text)