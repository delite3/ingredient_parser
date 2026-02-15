import re
import easyocr
import cv2
from difflib import get_close_matches

def clean_ingredient_list(ocr_text):
    # First, standardize the "Ingredients:" part
    cleaned = re.sub(r'Ingredients\s*[:;]\s*', 'Ingredients: ', ocr_text)
    
    # Replace semicolons with commas (common OCR error)
    cleaned = re.sub(r'(\w+)\s*;\s*(\w+)', r'\1, \2', cleaned)
    
    # Replace colons between words (not at the beginning)
    cleaned = re.sub(r'(\w+)\s*:\s*(\w+)', r'\1, \2', cleaned)
    
    # Extract the ingredients part
    ingredients_part = re.sub(r'^Ingredients:\s*', '', cleaned)
    
    # Split into individual ingredients
    ingredients = [ing.strip() for ing in ingredients_part.split(',')]
    
    return {
        "cleaned_text": cleaned,
        "ingredients": ingredients
    }

def read_ingredients(image_file):
    reader = easyocr.Reader(['en'])
    image = cv2.imread('product_label.jpg')
    image = cv2.convertScaleAbs(image, alpha=1.5, beta=0)

    results = reader.readtext(image)
    all_text = " ".join([text for (_, text, _) in results])

    cleaned_result = clean_ingredient_list(all_text)
    #print(cleaned_result["cleaned_text"])
    #for ing in cleaned_result["ingredients"]:
    #    print(ing)
    return cleaned_result["ingredients"], cleaned_result["cleaned_text"]

