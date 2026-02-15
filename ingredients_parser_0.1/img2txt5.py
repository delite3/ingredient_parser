# Install with: pip install paddlepaddle paddleocr
from paddleocr import PaddleOCR
import cv2
import re


# Clean up the ingredients list
def clean_ingredient_list(text):
    # Find the ingredients section
    match = re.search(r"ingredients\s*[:\-;]?\s*(.*)", text, re.IGNORECASE)
    if not match:
        return "No ingredients section found."

    ingredients_text = match.group(1)

    # Normalize separators
    ingredients_text = re.sub(r"[;:]", ",", ingredients_text)

    # Split by commas
    ingredients = [ing.strip() for ing in ingredients_text.split(",")]

    # Remove empty items and clean up
    ingredients = [ing for ing in ingredients if ing]

    return ingredients


def extract_txt(img_path):
    # Initialize PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=True)

    # Read image
    # img_path = 'product_label.jpg'
    result = ocr.ocr(img_path, cls=True)

    # Extract text
    all_text = ""
    for line in result:
        if result[0] is None:
            return None
        for item in line:
            all_text += item[1][0] + " "

    # print("Raw OCR Result:", all_text)

    ingredients = clean_ingredient_list(all_text)
    return ingredients


"""
ingredients = extract_txt("product_label.jpg")
print("\nExtracted Ingredients:")
for i, ingredient in enumerate(ingredients, 1):
    print(f"{i}. {ingredient}")
"""
