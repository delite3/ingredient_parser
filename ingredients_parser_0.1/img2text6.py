import re
from paddleocr import PaddleOCR
import cv2

def extract_ingredients_from_ocr(img_path, ocr):
    """
    Extract and parse ingredients from a product image using PaddleOCR
    """
    # Initialize PaddleOCR
    
    # Read image and extract text
    result = ocr.ocr(img_path, cls=True)
    
    # Extract text
    all_text = ""
    for line in result:
        for item in line:
            all_text += item[1][0] + " "
    
    # Parse ingredients from the OCR text
    ingredients = parse_ingredients(all_text)
    return ingredients

def parse_ingredients(ocr_text):
    """
    Parse ingredients from OCR text with improved handling of common issues
    """
    # Step 1: Find the ingredients section
    patterns = [
        r'ingredients\s*[:\-;]?\s*(.*)',
        r'((?:ingredients|INGREDIENTS)[^:]*:.*?)(?:\.|\n|$)',
        r'((?:ingredients|INGREDIENTS).*?)(?:\.|$)',
        r'((?:contents|CONTENTS):.*?)(?:\.|$)'
    ]
    
    ingredients_text = None
    for pattern in patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE | re.DOTALL)
        if match:
            ingredients_text = match.group(1)
            break
    
    if not ingredients_text:
        return []
    
    # Step 2: Normalize separators and split by proper delimiters
    # Replace semicolons and other separators with commas
    ingredients_text = re.sub(r'[;:\|]', ',', ingredients_text)
    
    # Replace periods that are likely acting as separators
    ingredients_text = re.sub(r'(?<!\w\.\w)\.\s+(?=[A-Z])', ', ', ingredients_text)
    
    # Initial split by commas
    raw_ingredients = [ing.strip() for ing in ingredients_text.split(',')]
    raw_ingredients = [ing for ing in raw_ingredients if ing]
    
    # Step 3: Fix hyphenated words from line breaks
    raw_ingredients = fix_hyphenated_words(raw_ingredients)
    
    # Step 4: Process each ingredient for potential combined ingredients
    parsed_ingredients = []
    for raw_ing in raw_ingredients:
        split_ingredients = split_combined_ingredients(raw_ing)
        parsed_ingredients.extend(split_ingredients)
    
    # Step 5: Clean and normalize each ingredient
    cleaned_ingredients = [clean_ingredient(ing) for ing in parsed_ingredients]
    cleaned_ingredients = [ing for ing in cleaned_ingredients if ing and len(ing) > 1]
    
    # Step 6: Post-process to remove duplicates and non-ingredients
    final_ingredients = remove_non_ingredients(cleaned_ingredients)
    
    return final_ingredients

def fix_hyphenated_words(ingredients_list):
    """
    Fix ingredients that were split due to hyphenation at line breaks
    """
    fixed_list = []
    i = 0
    
    while i < len(ingredients_list):
        current = ingredients_list[i]
        
        # Check if current ingredient ends with a hyphen
        if current.endswith('-') and i + 1 < len(ingredients_list):
            # Combine with next ingredient without the hyphen
            fixed_list.append(current[:-1] + ingredients_list[i+1])
            i += 2
        else:
            # Handle mid-word hyphens with spaces around them
            current = re.sub(r'(\w+)\s*-\s*(\w+)', r'\1\2', current)
            fixed_list.append(current)
            i += 1
    
    return fixed_list

def split_combined_ingredients(text):
    """
    Split potentially combined ingredients based on capitalization patterns
    """
    # Protect common chemical notations and abbreviations
    protected_patterns = {
        r'C\d+-\d+': 'CARBON_RANGE',  # Like C10-16
        r'PEG-\d+': 'PEG_NUM',         # Like PEG-40
        r'PPG-\d+': 'PPG_NUM',         # Like PPG-20
        r'\bSD\s+Alcohol': 'SD_ALCOHOL', # SD Alcohol
        r'Vitamin [ABCDE]\b': 'VITAMIN_X',
        r'Glyceryl Stearate SE': 'GLYCERYL_STEARATE_SE',
    }
    
    # Temporarily replace protected patterns
    for pattern, replacement in protected_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Check for special case: "Alcohol Denat."
    if re.search(r'alcohol\s+denat', text, re.IGNORECASE):
        text = re.sub(r'(alcohol\s+denat\.?)', r'ALCOHOL_DENAT', text, flags=re.IGNORECASE)
    
    # Find potential split points where capital letters follow lowercase
    # and are not at start of the text
    split_points = []
    for i in range(1, len(text)):
        # Look for capital letters preceded by lowercase or space
        if text[i].isupper() and text[i-1].islower():
            # Make sure we're not in the middle of a protected pattern
            split_points.append(i)
    
    # Split the text at the identified points
    if not split_points:
        result = [text]
    else:
        result = []
        start = 0
        for point in split_points:
            result.append(text[start:point])
            start = point
        result.append(text[start:])
    
    # Restore protected patterns
    for i, item in enumerate(result):
        for pattern, replacement in protected_patterns.items():
            item = re.sub(replacement, pattern.replace('\\', ''), item)
        
        # Restore "Alcohol Denat."
        item = re.sub(r'ALCOHOL_DENAT', 'Alcohol Denat.', item)
        result[i] = item
    
    # Remove empty items
    result = [r.strip() for r in result if r.strip()]
    
    return result

def clean_ingredient(text):
    """
    Clean up an individual ingredient
    """
    # Handle "Denat." attached to Alcohol
    if text.lower().startswith('alcohol') and 'denat' in text.lower():
        return 'Alcohol Denat.'
    
    # Remove trailing periods unless they are part of abbreviations
    if text.endswith(".") and len(text) > 2 and not text[-2].isupper():
        text = text[:-1]
    
    # Fix mid-word hyphens with spaces
    text = re.sub(r'(\w+)\s*-\s*(\w+)', r'\1\2', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Handle common abbreviations in cosmetic ingredients
    abbrev_map = {
        "Peg": "PEG",
        "Ppg": "PPG",
        "Edta": "EDTA",
        "Mea": "MEA",
        "Tea": "TEA",
        "Dea": "DEA",
        "Bht": "BHT",
        "Sd": "SD"
    }
    
    for abbr, repl in abbrev_map.items():
        # Replace only whole words, not parts of words
        text = re.sub(rf'\b{abbr}\b', repl, text)
    
    # Fix capitalization of first letter
    if text and len(text) > 0:
        text = text[0].upper() + text[1:]
    
    return text

def remove_non_ingredients(ingredients_list):
    """
    Remove items that are likely not actual ingredients
    """
    non_ingredient_patterns = [
        r'^[0-9.]+$',                     # Just numbers
        r'^[0-9.]+\s*%$',                 # Percentages
        r'^may\s+contain',                # May contain statements
        r'^and$',                         # Just the word "and"
        r'^contains$',                    # Just the word "contains"
        r'^ingredients$',                 # Just the word "ingredients"
        r'^warnings?$',                   # Warnings
        r'^caution',                      # Caution statements
        r'^direction',                    # Directions
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ingredients = []
    for ing in ingredients_list:
        if ing.lower() not in seen:
            seen.add(ing.lower())
            unique_ingredients.append(ing)
    
    # Filter out non-ingredients
    filtered_ingredients = []
    for ing in unique_ingredients:
        if not any(re.search(pattern, ing, re.IGNORECASE) for pattern in non_ingredient_patterns):
            if len(ing) >= 2:  # Ensure ingredients have at least 2 characters
                filtered_ingredients.append(ing)
    
    return filtered_ingredients

# Example usage
if __name__ == "__main__":

    ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)
    for i in range(1,7):
        pl = f"product_images/product_label{i}.jpg"
        ingredients = extract_ingredients_from_ocr(pl, ocr)
        print("\nExtracted Ingredients:")
        for i, ingredient in enumerate(ingredients, 1):
            print(f"{i}. {ingredient}")