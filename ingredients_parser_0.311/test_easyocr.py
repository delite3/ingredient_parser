import cv2
import numpy as np
import easyocr
from Analyser import EWGSkindeepAPI
import Levenshtein
import re


def preprocess_image_light(image_path, output_path=None):
    """
    Light preprocessing for EasyOCR - it handles most issues internally.
    Resizes image if needed to avoid edge cases.
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Resize if image is too large or has extreme aspect ratio
    # EasyOCR works best with moderate-sized images
    height, width = image.shape[:2]
    max_dimension = 1920
    
    # Resize if too large
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    
    # Ensure minimum size (some images might be too small)
    if min(height, width) < 100:
        scale = 100 / min(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        print(f"Upscaled small image to {new_width}x{new_height}")

    # Optional: Light denoising for very noisy images
    # EasyOCR is robust enough that heavy preprocessing often hurts more than helps
    # Uncomment if needed:
    # image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    
    if output_path:
        cv2.imwrite(output_path, image)
    
    return image


def display_image(image, title="Image", wait=True):
    """Display image for debugging"""
    cv2.imshow(title, image)
    if wait:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def find_ingredient_section(ocr_results):
    """
    Find the text that contains ingredients section from OCR results.
    EasyOCR returns results as: [(bbox, text, confidence), ...]
    
    Args:
        ocr_results: List of (bbox, text, confidence) tuples from EasyOCR
    
    Returns:
        str: Combined text, potentially filtered to ingredient section
    """
    all_text = []
    ingredient_start_idx = None
    
    for idx, (bbox, text, confidence) in enumerate(ocr_results):
        # Look for "ingredients" keyword
        if ingredient_start_idx is None:
            if re.search(r'\bingredient[s]?\b', text, re.IGNORECASE):
                ingredient_start_idx = idx
        
        all_text.append((text, confidence, idx))
    
    # If we found an ingredients section, prioritize text from that point onward
    if ingredient_start_idx is not None:
        # Get text from ingredient section onward
        ingredient_text = [text for text, conf, idx in all_text if idx >= ingredient_start_idx]
        return " ".join(ingredient_text)
    
    # If no clear ingredient section found, return all text
    return " ".join([text for text, conf, idx in all_text])


def parse_ingredients_from_ocr(ocr_text):
    """
    Parse ingredient list from OCR text with advanced handling of:
    - Ingredient section identification
    - OCR errors and hyphenation
    - Combined ingredients without comma separation
    - Multi-word ingredients and abbreviations

    Args:
        ocr_text (str): The raw OCR text from the product label

    Returns:
        list: A clean list of individual ingredients
    """
    
    if ocr_text is None or not ocr_text.strip():
        return []

    # Step 1: Extract the ingredients section
    ingredient_patterns = [
        r"ingredients\s*[:\-;]?\s*(.*?)(?=\b(?:directions|use|warning|caution|disclaimer|made in|for external use|how to use)\b|\Z)",
        r"ingredient[s]?[:\-;]?\s*(.*?)(?=\b(?:directions|use|warning|caution|disclaimer|made in|for external use|how to use)\b|\Z)",
        r"contains[:\-;]?\s*(.*?)(?=\b(?:directions|use|warning|caution|disclaimer|made in|for external use|how to use)\b|\Z)",
    ]

    ingredients_text = None
    for pattern in ingredient_patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE | re.DOTALL)
        if match:
            ingredients_text = match.group(1).strip()
            break

    if not ingredients_text:
        ingredients_text = ocr_text

    # Step 2: Pre-processing
    # 2.1: Fix hyphenation at line breaks (common OCR issue)
    ingredients_text = re.sub(r"(\w+)\-\s*[\n\r]+\s*(\w+)", r"\1\2", ingredients_text)

    # 2.2: Fix OCR errors where spaces are inserted in hyphenated words
    ingredients_text = re.sub(r"(\w+)\s+\-\s+(\w+)", r"\1-\2", ingredients_text)

    # 2.3: Normalize whitespace and line breaks
    ingredients_text = re.sub(r"[\n\r]+", " ", ingredients_text)
    ingredients_text = re.sub(r"\s+", " ", ingredients_text)

    # 2.4: Replace common separators with commas
    ingredients_text = re.sub(r"[;:]", ",", ingredients_text)

    # 2.5: Fix parentheses spacing (OCR sometimes adds spaces around parentheses)
    ingredients_text = re.sub(r"\(\s+", "(", ingredients_text)
    ingredients_text = re.sub(r"\s+\)", ")", ingredients_text)

    # Step 3: Initial split by commas
    comma_split = [item.strip() for item in ingredients_text.split(",")]
    processed_items = []

    # Step 4: Process each item for combined ingredients and OCR errors
    for item in comma_split:
        if not item or len(item) <= 2:  # Skip empty or very short items
            continue

        # 4.1: Temporarily protect periods in common abbreviations
        protected_item = item
        common_abbrev = [
            "vit.", "var.", "spp.", "sp.", "subsp.", "vol.", 
            "no.", "dr.", "st.", "ext.", "etc."
        ]

        for abbrev in common_abbrev:
            pattern = re.compile(re.escape(abbrev), re.IGNORECASE)
            protected_item = pattern.sub(
                lambda m: m.group().replace(".", "@"), protected_item
            )

        # 4.2: Split by periods that likely separate ingredients
        split_by_period = re.split(r"(\.\s+)(?=[A-Z])", protected_item)

        parts = []
        for i in range(0, len(split_by_period), 2):
            part = split_by_period[i]
            if i + 1 < len(split_by_period):
                part += "."
            parts.append(part)

        if not parts:
            parts = [protected_item]

        # 4.3: Process for combined ingredients
        for part in parts:
            part = part.replace("@", ".")

            subparts = []
            matches = list(re.finditer(r"([a-z])([A-Z][a-z])", part))

            if matches:
                valid_splits = []

                for match in matches:
                    idx = match.start() + 1

                    # Skip if within parentheses
                    open_parens = part[:idx].count("(")
                    close_parens = part[:idx].count(")")
                    if open_parens > close_parens:
                        continue

                    # Skip if after common chemical prefixes
                    prefix_context = part[max(0, idx - 6) : idx].lower()
                    if any(
                        prefix in prefix_context
                        for prefix in ["di", "tri", "tetra", "poly", "mono", "iso"]
                    ):
                        continue

                    # Skip if part of known patterns
                    context = part[max(0, idx - 10) : min(len(part), idx + 10)]
                    if any(
                        pattern in context.lower()
                        for pattern in ["vitamin", "extract", "oil"]
                    ):
                        continue

                    valid_splits.append(idx)

                if valid_splits:
                    start_idx = 0
                    for idx in valid_splits:
                        subpart = part[start_idx:idx].strip()
                        if subpart:
                            subparts.append(subpart)
                        start_idx = idx

                    if start_idx < len(part):
                        subparts.append(part[start_idx:].strip())
                else:
                    subparts.append(part)
            else:
                subparts.append(part)

            processed_items.extend(subparts)

    # Step 5: Final cleaning and normalization
    final_ingredients = []

    for ing in processed_items:
        # 5.1: Remove non-alphanumeric characters from ends
        ing = ing.strip()
        ing = re.sub(r"^[^a-zA-Z0-9(]+|[^a-zA-Z0-9)]+$", "", ing)

        # 5.2: Normalize whitespace
        ing = re.sub(r"\s+", " ", ing)

        # 5.3: Fix common OCR errors
        # Fix "l" instead of "1" in numbers
        ing = re.sub(r"([A-Za-z])l([0-9])", r"\1-\2", ing)

        # Fix "O" instead of "0" in numbers
        ing = re.sub(r"([A-Za-z])O([0-9])", r"\1-\2", ing)

        # 5.4: Skip invalid ingredients
        if ing and len(ing) > 1:
            final_ingredients.append(ing)

    return final_ingredients


def parse_results_easyocr(ocr_results):
    """
    Extract and parse ingredients from EasyOCR results.
    
    Args:
        ocr_results: List of (bbox, text, confidence) tuples from EasyOCR
    
    Returns:
        list: Parsed ingredient list
    """
    if not ocr_results:
        return []
    
    # Extract and combine text from OCR results
    all_text = find_ingredient_section(ocr_results)
    
    # Parse ingredients from the OCR text
    ingredient_list = parse_ingredients_from_ocr(all_text)
    
    return ingredient_list


def smart_analyze(ingredient, ewg):
    """
    Smartly analyze an ingredient by trying various combinations

    Args:
        ingredient (str): The ingredient to analyze
        ewg: EWGSkindeepAPI instance

    Returns:
        dict: Best analysis result
    """
    # Use the built-in get_ingredient_data method
    result = ewg.get_ingredient_data(ingredient, exact_match_only=False)
    
    if result.get("ingredient_found"):
        return {
            "original": ingredient,
            "corrected": result["ingredient_info"].get("name"),
            "match_type": "direct_match" if result.get("exact_match") else "fuzzy_match",
            "data": result,
        }
    
    # If no match, try common variations
    variations = [
        ingredient.replace("-", " "),  # Replace hyphens with spaces
        ingredient.replace(" ", ""),  # Remove spaces
        ingredient.split("(")[0].strip(),  # Remove parenthetical info
        ingredient.split("/")[0].strip(),  # Take first part if slash separated
    ]

    for variation in variations:
        if variation != ingredient and variation:  # Don't retest the original
            result = ewg.get_ingredient_data(variation, exact_match_only=False)
            
            if result.get("ingredient_found"):
                return {
                    "original": ingredient,
                    "corrected": result["ingredient_info"].get("name"),
                    "match_type": "variation_match",
                    "data": result,
                }

    return {
        "original": ingredient,
        "corrected": None,
        "match_type": "no_match",
        "data": None,
    }


def smart_analyze_list(ingredients, ewg):
    """
    Analyze a list of ingredients with smart matching and error handling.

    Args:
        ingredients (list): List of ingredient strings to analyze
        ewg: EWGSkindeepAPI instance

    Returns:
        list: List of analysis results
    """
    results = []
    unmatched = []

    for ingredient in ingredients:
        print(f"\n--- Analyzing: {ingredient} ---")
        result = smart_analyze(ingredient, ewg)

        if result["match_type"] != "no_match":
            results.append(result)
            print(f"✓ Matched: {result['corrected']}")
        else:
            unmatched.append(ingredient)

    # Second pass for unmatched ingredients
    if unmatched:
        print("\n=== Second pass for unmatched ingredients ===")
        i = 0
        while i < len(unmatched):
            # Try combining with next ingredient
            if i < len(unmatched) - 1:
                combined = f"{unmatched[i]} {unmatched[i + 1]}"
                print(f"\nTrying combined: {combined}")

                result = smart_analyze(combined, ewg)

                if result["match_type"] != "no_match":
                    print(f"✓ Match found by combining!")
                    results.append(result)
                    i += 2  # Skip next ingredient as we combined it
                    continue

            # If combining didn't work, add as unmatched
            print(f"✗ Could not find any match for: {unmatched[i]}")
            results.append(
                {
                    "original": unmatched[i],
                    "corrected": None,
                    "match_type": "no_match",
                    "data": None,
                }
            )
            i += 1

    return results


def pretty_print_ingredient(result):
    """
    Pretty print the results for a single ingredient.

    Args:
        result (dict): The result dictionary from analyze_ingredient
    """
    if not result or result.get("match_type") == "no_match":
        print("✗ No match found")
        return

    data = result.get("data", {})

    if isinstance(result, list):
        print("Multiple matches found from splitting:")
        for r in result:
            print(f"- {r['corrected']} (split from original)")
        return

    original = result.get("original", "Unknown")
    corrected = result.get("corrected", "Unknown")
    match_type = result.get("match_type", "Unknown")

    print(f"Original: {original}")

    if original != corrected and corrected:
        print(f"Corrected: {corrected}")

    print(f"Match type: {match_type}")

    if data and "ingredient_info" in data:
        info = data["ingredient_info"]

        if "score_range" in info:
            print(f"Score Range: {info['score_range']}")

        if "data_level" in info:
            print(f"Data Level: {info['data_level']}")

        if "concerns" in info and info["concerns"]:
            print("\nConcerns:")
            for concern in info["concerns"]:
                print(f"- {concern['concern']} [{concern['reference']}]")


def visualize_detections(image_path, ocr_results, save_path=None):
    """
    Visualize OCR detections on the image.
    
    Args:
        image_path: Path to original image
        ocr_results: Results from EasyOCR
        save_path: Optional path to save visualization
    """
    image = cv2.imread(image_path)
    
    for (bbox, text, confidence) in ocr_results:
        # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        pts = np.array(bbox, dtype=np.int32)
        
        # Draw bounding box
        cv2.polylines(image, [pts], True, (0, 255, 0), 2)
        
        # Add text label
        cv2.putText(image, f"{text} ({confidence:.2f})", 
                   (int(bbox[0][0]), int(bbox[0][1]) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    if save_path:
        cv2.imwrite(save_path, image)
    
    display_image(image, "OCR Detections", wait=True)
    
    return image


# ============= Main Execution =============

if __name__ == "__main__":
    # Path to your image
    image_path = "product_images/image0.jpeg"
    
    print("Initializing EasyOCR (this may take a moment on first run)...")
    # Initialize EasyOCR Reader
    # gpu=True if you have CUDA-enabled GPU, False for CPU
    # Set gpu=True for better performance if you have a compatible GPU
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    
    print(f"\nProcessing image: {image_path}")
    
    # Preprocess to ensure compatible image size/format
    print("Preprocessing image...")
    processed_image_path = "temp_processed.jpg"
    try:
        processed_image = preprocess_image_light(image_path, processed_image_path)
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        print("Trying to use original image...")
        processed_image_path = image_path
    
    # Run OCR directly on the image
    # EasyOCR can handle full images and will detect text regions automatically
    print("Running OCR...")
    try:
        ocr_results = reader.readtext(
            processed_image_path,
            paragraph=False,
            detail=1  # Include bounding boxes and confidence
        )
    except Exception as e:
        print(f"Error during OCR: {e}")
        print("Note: Some images may have incompatible dimensions or formats.")
        print("Try with a different image or check the EASYOCR_USAGE.md guide.")
        exit(1)
    
    print(f"\nFound {len(ocr_results)} text regions")
    
    # Optional: Visualize detections
    # Uncomment to see what text was detected and where
    # visualize_detections(image_path, ocr_results, "product_images/test_results/detections.jpg")
    
    # Parse ingredients from OCR results
    print("\nParsing ingredients...")
    ingredients = parse_results_easyocr(ocr_results)
    
    print(f"\nFound {len(ingredients)} ingredients:")
    for i, ing in enumerate(ingredients, 1):
        print(f"{i}. {ing}")
    
    # Analyze ingredients using EWG database
    print("\n" + "="*50)
    print("Analyzing ingredients with EWG Skindeep database...")
    print("="*50)
    
    ewg = EWGSkindeepAPI()
    results = smart_analyze_list(ingredients, ewg)
    
    print("\n" + "="*50)
    print("FINAL RESULTS")
    print("="*50)
    
    for result in results:
        print("\n" + "-"*50)
        pretty_print_ingredient(result)
