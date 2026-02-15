import cv2
import numpy as np
from paddleocr import PaddleOCR
from Analyser import EWGSkindeepAPI
import Levenshtein
import re


def preprocess_text_with_punctuation(image_path, output_path=None):
    """
    Complete preprocessing pipeline optimized for ingredient labels with punctuation.
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    display_image(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Save result if output path is provided
    if output_path:
        cv2.imwrite(output_path, binary)
    display_image(binary)
    return binary


def display_image(image, title="Image", wait=True):
    cv2.imshow(title, image)
    if wait:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def find_ingredient_word(all_text):
    # confidence = line[1][1]
    # text = line[1][0].split(",")
    line = all_text.split(",")
    combined_words = line[0].split()  # text[0].split()
    combined_words.append(line[1].split()[0])

    # 1 find the word ingredient/ingredients or words that are similaallr to ingredient, high threshold allowed
    if (len(combined_words[0]) <= len("ingredients")) and (
        Levenshtein.ratio("ingredients", combined_words[0].lower()) > 0.75
        or Levenshtein.ratio("ingred", combined_words[0].lower()) > 0.75
        or Levenshtein.ratio("ients", combined_words[0].lower()) > 0.75
    ):
        # If the first word has a good match then we accept it
        first_word_ingredient = True
        print(
            f"ingredient found on first try: {first_word_ingredient}, word found: {combined_words[0]}"
        )
        line[0] = " ".join(line[0].split()[1:])
        return line

    elif (
        int(len("ingredients") * 0.8)
        < len(combined_words[0] + combined_words[1])
        < int(len("ingredients") * 1.2)
    ) and Levenshtein.ratio(
        "ingredients", (combined_words[0] + combined_words[1]).lower()
    ) > 0.75:

        first_and_second_word_is_ingredient = True
        print("###")

    if first_word_ingredient:
        combined_words.pop(0)
    elif first_and_second_word_is_ingredient:
        combined_words.pop(0)
        combined_words.pop(0)
    line[0] = combined_words[0]
    return line


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

    # ocr_text = find_ingredient_word(ocr_text)

    # find_ingredient_word(ocr_text[0])
    if ocr_text is None:
        return

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


def parse_results(result):
    """
    Extract and parse ingredients from a product image using PaddleOCR
    """
    # Initialize PaddleOCR

    # Read image and extract text
    if result[0] is None:
        return
    # Extract text
    all_text = ""
    for line in result:
        for item in line:
            all_text += item[1][0] + " "

    # Parse ingredients from the OCR text
    ingredient_list = parse_ingredients_from_ocr(all_text)

    return ingredient_list


def smart_analyze(ingredient, ewg):
    """
    Smartly analyze an ingredient by trying various combinations

    Args:
        ingredient (str): The ingredient to analyze

    Returns:
        dict: Best analysis result
    """
    # First try the original ingredient
    result = ewg.analyze_ingredient(ingredient)

    if result["ingredient_found"] and result.get("exact_match", False):
        return {
            "original": ingredient,
            "corrected": ingredient,
            "match_type": "exact",
            "data": result,
        }

    # Try to split the ingredient and check each part
    words = re.split(r"[\s,/\-]+", ingredient)
    words = [
        w
        for w in words
        if len(w) > 2 and w.lower() not in ["and", "with", "plus", "the"]
    ]

    # If we only have one word, skip to partial match
    if len(words) > 1:
        found_matches = []

        for word in words:
            result = ewg.analyze_ingredient(word)

            if result["ingredient_found"] and result.get("exact_match", False):
                found_matches.append(
                    {
                        "original": word,
                        "corrected": word,
                        "match_type": "split_exact",
                        "data": result,
                    }
                )

        if found_matches:
            return found_matches[0]  # Return the first match for now

    # If we didn't find any exact matches from splits, try a fuzzy match on the original
    result = EWGSkindeepAPI().get_ingredient_data(ingredient, exact_match_only=False)

    if result["ingredient_found"]:
        return {
            "original": ingredient,
            "corrected": result["ingredient_info"]["name"],
            "match_type": "fuzzy",
            "data": result,
        }

    # No match found
    return {
        "original": ingredient,
        "corrected": None,
        "match_type": "no_match",
        "data": None,
    }


def smart_analyze_list(ingredient_list, ewg):
    """
    Intelligently analyze a list of ingredients

    Args:
        ingredient_list (list): List of ingredients

    Returns:
        list: List of analysis results
    """

    results = []
    unmatched = []

    # Phase 1: Try direct matches first
    print("PHASE 1: Testing direct matches...")
    for ingredient in ingredient_list:
        result = smart_analyze(ingredient, ewg)

        if result["match_type"] in ["exact", "fuzzy"]:
            print(f"✓ Found match for: {ingredient}")
            results.append(result)
        else:
            print(f"✗ No match for: {ingredient}")
            unmatched.append(ingredient)

    # Phase 2: Try combinations of adjacent unmatched ingredients
    print("\nPHASE 2: Testing combinations of adjacent unmatched ingredients...")
    if len(unmatched) >= 2:
        i = 0
        while i < len(unmatched) - 1:
            # Try combining with the next ingredient
            combined = unmatched[i] + " " + unmatched[i + 1]
            combined_result = ewg.analyze_ingredient(combined)

            if combined_result["ingredient_found"] and combined_result.get(
                "exact_match", False
            ):
                print(f"✓ Found exact match for combined: {combined}")
                results.append(
                    {
                        "original": f"{unmatched[i]} + {unmatched[i+1]}",
                        "corrected": combined,
                        "match_type": "combined_exact",
                        "data": combined_result,
                    }
                )
                # Skip both ingredients as they've been combined
                i += 2
            else:
                # Also try with a comma
                combined_comma = unmatched[i] + ", " + unmatched[i + 1]
                comma_result = ewg.analyze_ingredient(combined_comma)

                if comma_result["ingredient_found"] and comma_result.get(
                    "exact_match", False
                ):
                    print(
                        f"✓ Found exact match for combined with comma: {combined_comma}"
                    )
                    results.append(
                        {
                            "original": f"{unmatched[i]} + {unmatched[i+1]}",
                            "corrected": combined_comma,
                            "match_type": "combined_comma_exact",
                            "data": comma_result,
                        }
                    )
                    i += 2
                else:
                    # Only increment by 1 to try next pair
                    i += 1

        # Add any remaining unmatched ingredients with their best fuzzy matches
        while i < len(unmatched):
            fuzzy_result = ewg.get_ingredient_data(unmatched[i], exact_match_only=False)

            if fuzzy_result["ingredient_found"]:
                print(
                    f"~ Found closest match for: {unmatched[i]} -> {fuzzy_result['ingredient_info']['name']}"
                )
                results.append(
                    {
                        "original": unmatched[i],
                        "corrected": fuzzy_result["ingredient_info"]["name"],
                        "match_type": "final_fuzzy",
                        "data": fuzzy_result,
                    }
                )
            else:
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

    # For split matches, we might have multiple results
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


# Process the image
processed = preprocess_text_with_punctuation("product_images/image2.jpeg")

# Configure PaddleOCR with specialized settings for ingredient labels
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en",
    rec_algorithm="SVTR_LCNet",  # More accurate recognition model
    rec_batch_num=1,
    rec_image_shape="3, 48, 320",  # Higher resolution recognition
    cls_thresh=0.9,  # Higher confidence for text orientation
    det_db_thresh=0.3,  # Lower threshold to detect text regions
    det_db_box_thresh=0.5,  # Lower threshold for text boxes
    max_batch_size=10,
    use_space_char=True,  # Important for ingredient lists
)

# Run OCR
result = ocr.ocr(processed, cls=True)
ingredients = parse_results(result)
ewg = EWGSkindeepAPI()

result = smart_analyze_list(ingredients, ewg)
for ing in result:
    pretty_print_ingredient(ing)
# print(result)
print("###")
