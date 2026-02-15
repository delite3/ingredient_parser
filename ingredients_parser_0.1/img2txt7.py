import re
from paddleocr import PaddleOCR


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
        found_ingredient_list = False
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
        # This prevents incorrect splitting of items like "Vit. E"
        protected_item = item
        # List of common abbreviations that shouldn't cause splits
        common_abbrev = [
            "vit.",
            "var.",
            "spp.",
            "sp.",
            "subsp.",
            "vol.",
            "no.",
            "dr.",
            "st.",
        ]

        for abbrev in common_abbrev:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(abbrev), re.IGNORECASE)
            protected_item = pattern.sub(
                lambda m: m.group().replace(".", "@"), protected_item
            )

        # 4.2: Split by periods that likely separate ingredients
        # Look for pattern: period + whitespace + capital letter
        split_by_period = re.split(r"(\.\s+)(?=[A-Z])", protected_item)

        parts = []
        for i in range(0, len(split_by_period), 2):
            part = split_by_period[i]
            if i + 1 < len(split_by_period):
                part += "."  # Add back the period that was in the splitting pattern
            parts.append(part)

        if not parts:
            parts = [protected_item]

        # 4.3: Process for combined ingredients (lowercase followed by uppercase)
        for part in parts:
            # Restore protected periods
            part = part.replace("@", ".")

            # Look for lowercase followed by uppercase not at word boundaries
            # This pattern indicates two ingredients may have been combined without proper separation
            subparts = []
            matches = list(re.finditer(r"([a-z])([A-Z][a-z])", part))

            if matches:
                # Process potential split points
                valid_splits = []

                for match in matches:
                    idx = match.start() + 1

                    # Skip if within parentheses (likely a scientific name or similar)
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

                    # Skip if part of known patterns that shouldn't be split
                    context = part[max(0, idx - 10) : min(len(part), idx + 10)]
                    if any(
                        pattern in context.lower()
                        for pattern in ["vitamin", "extract", "oil"]
                    ):
                        # These terms often have legitimate capital letters following
                        continue

                    valid_splits.append(idx)

                if valid_splits:
                    # Process the splits
                    start_idx = 0
                    for idx in valid_splits:
                        subpart = part[start_idx:idx].strip()
                        if subpart:
                            subparts.append(subpart)
                        start_idx = idx

                    # Add the last part
                    if start_idx < len(part):
                        subparts.append(part[start_idx:].strip())
                else:
                    # No valid splits found
                    subparts.append(part)
            else:
                # No combined ingredients detected
                subparts.append(part)

            # Add all subparts to processed items
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
        if ing and len(ing) > 1:  # Skip single characters and empty strings
            final_ingredients.append(ing)

    return final_ingredients


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
    # ingredients = parse_ingredients(all_text)
    return all_text


"""if __name__ == "__main__":

    image_path = "product_images/product_label5.jpg"
    ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=True, savefile=True)

    image_txt = extract_ingredients_from_ocr(image_path, ocr)

    results = parse_ingredients_from_ocr(image_txt)
    for i, ing in enumerate(results):
        print(f"{i}: {ing}")
"""
