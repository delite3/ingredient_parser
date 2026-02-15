import re
from paddleocr import PaddleOCR
import cv2
import numpy as np
import os
import argparse


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


def extract_ingredients_from_ocr(img_path, ocr):
    """
    Extract and parse ingredients from a product image using PaddleOCR
    """
    # Initialize PaddleOCR

    # Read image and extract text
    result = ocr.ocr(img_path, cls=True)
    if result[0] is None:
        return
    # Extract text
    all_text = ""
    for line in result:
        for item in line:
            all_text += item[1][0] + " "

    # Parse ingredients from the OCR text
    # ingredients = parse_ingredients(all_text)
    return all_text


def preprocess_image(image_path, method="adaptive", display=False, save_path=None):
    """
    Preprocess an image to enhance text visibility for OCR.

    Args:
        image_path (str): Path to the input image
        method (str): Preprocessing method to use. Options:
                     'adaptive' - Adaptive thresholding (good for varied lighting)
                     'contrast' - Contrast enhancement
                     'threshold' - Basic thresholding
                     'glare' - Glare reduction
                     'morphology' - Morphological operations
                     'multi' - Apply multiple methods sequentially
        display (bool): If True, display the original and processed images
        save_path (str, optional): Path to save the processed image

    Returns:
        str: Path to the processed image
    """
    # Read the input image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found at {image_path}")

    # Keep a copy of the original image for display
    original = img.copy()

    # Apply the selected preprocessing method
    if method == "adaptive_threshold1":
        processed = _adaptive_threshold1(img)
    elif method == "adaptive_threshold2":
        processed = _adaptive_threshold2(img)
    elif method == "adaptive_threshold3":
        processed = _adaptive_threshold3(img)
    elif method == "enhance_contrast1":
        processed = _enhance_contrast1(img)
    elif method == "enhance_contrast2":
        processed = _enhance_contrast2(img)
    elif method == "enhance_contrast3":
        processed = _enhance_contrast3(img)
    elif method == "basic_threshold1":
        processed = _basic_threshold1(img)
    elif method == "basic_threshold2":
        processed = _basic_threshold2(img)
    elif method == "basic_threshold3":
        processed = _basic_threshold3(img)
    elif method == "reduce_glare1":
        processed = _reduce_glare1(img)
    elif method == "reduce_glare2":
        processed = _reduce_glare2(img)
    elif method == "morphology1":
        processed = _apply_morphology1(img)
    elif method == "morphology2":
        processed = _apply_morphology2(img)
    elif method == "morphology3":
        processed = _apply_morphology3(img)
    # elif method == "multi":
    # processed = multi_process(img)
    else:
        raise ValueError(f"Unknown preprocessing method: {method}")

    # Display the images if requested
    if display:
        cv2.imshow("Original Image", original)
        cv2.imshow(f"Processed Image ({method})", processed)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Save the processed image if a path is provided
    if save_path:
        output_path = save_path
    else:
        # Create a default path based on the original image path
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(
            os.path.dirname(image_path), f"{name}_processed_{method}{ext}"
        )

    cv2.imwrite(output_path, processed)
    return output_path


def _adaptive_threshold1(img):
    """Apply adaptive thresholding to enhance text visibility."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter for noise reduction while preserving edges
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    return thresh


def _adaptive_threshold2(img):
    """Apply adaptive thresholding with smaller block size for finer details like commas and dots."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter with different parameters
    filtered = cv2.bilateralFilter(
        gray, 9, 25, 25
    )  # Increased sigmaColor and sigmaSpace

    # Apply adaptive thresholding with smaller block size
    thresh = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 7, 3
    )  # Block size 7 instead of 11, C=3 instead of 2

    return thresh


def _adaptive_threshold3(img):
    """Apply adaptive thresholding with mean method instead of gaussian."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Sharpen the image first
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    # Apply bilateral filter
    filtered = cv2.bilateralFilter(sharpened, 7, 15, 15)

    # Apply adaptive thresholding with mean method
    thresh = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 4
    )

    return thresh


def _enhance_contrast1(img):
    """Enhance contrast and normalize the image."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Normalize the image
    normalized = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX)

    return normalized


def _enhance_contrast2(img):
    """Enhanced contrast with higher CLAHE clip limit for stronger local contrast."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE with higher clip limit
    clahe = cv2.createCLAHE(
        clipLimit=4.0, tileGridSize=(4, 4)
    )  # Increased clip limit, smaller tiles
    enhanced = clahe.apply(gray)

    # Add sharpen filter
    kernel = np.array([[-1, -1, -1], [-1, 10, -1], [-1, -1, -1]]) / 2
    enhanced = cv2.filter2D(enhanced, -1, kernel)

    # Normalize the image
    normalized = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX)

    return normalized


def _enhance_contrast3(img):
    """Two-pass contrast enhancement focusing on fine details."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # First CLAHE pass
    clahe1 = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced1 = clahe1.apply(gray)

    # Apply bilateral filter to preserve edges
    filtered = cv2.bilateralFilter(enhanced1, 5, 10, 10)

    # Second CLAHE pass with different parameters
    clahe2 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    enhanced2 = clahe2.apply(filtered)

    # Normalize the image
    normalized = cv2.normalize(enhanced2, None, 0, 255, cv2.NORM_MINMAX)

    return normalized


def _basic_threshold1(img):
    """Apply basic thresholding for high-contrast images."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Otsu's thresholding
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh


def _basic_threshold2(img):
    """Apply basic thresholding with different blur and threshold parameters."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply median blur instead of Gaussian
    blurred = cv2.medianBlur(gray, 3)

    # Apply binary thresholding with fixed value
    _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY)

    return thresh


def _basic_threshold3(img):
    """Apply triangle thresholding (good for bimodal images like text)."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter
    filtered = cv2.bilateralFilter(gray, 5, 20, 20)

    # Apply Triangle thresholding
    _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)

    return thresh


def _reduce_glare1(img):
    """Reduce glare in the image."""
    # Convert to LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # Split the LAB channels
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    # Merge the channels back
    lab = cv2.merge((l, a, b))

    # Convert back to BGR
    bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Threshold to handle glare areas
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Create a mask from the thresholded image
    mask = cv2.bitwise_not(thresh)

    # Apply the mask to the original grayscale image
    result = cv2.bitwise_and(gray, gray, mask=mask)

    # Normalize result
    normalized = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX)

    return normalized


def _reduce_glare2(img):
    """Reduce glare using HSV color space instead of LAB."""
    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Split the HSV channels
    h, s, v = cv2.split(hsv)

    # Apply CLAHE to V channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    v = clahe.apply(v)

    # Reduce very bright areas in V channel
    _, bright_mask = cv2.threshold(v, 220, 255, cv2.THRESH_BINARY_INV)
    v = cv2.bitwise_and(v, v, mask=bright_mask)

    # Merge the channels back
    hsv = cv2.merge((h, s, v))

    # Convert back to BGR
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Normalize result
    normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    return normalized


def _apply_morphology1(img):
    """Apply morphological operations to enhance text clarity."""
    # Ensure image is grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Apply thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Create a kernel for morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

    # Apply morphological operations
    # Dilation followed by erosion (closing) helps connect broken parts of text
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Invert back
    result = cv2.bitwise_not(closed)

    return result


def _apply_morphology2(img):
    """Morphological operations optimized for preserving small details like commas."""
    # Ensure image is grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Apply adaptive threshold instead of Otsu
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )

    # Create a smaller kernel for morphological operations
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2, 2)
    )  # Ellipse kernel instead of rectangle

    # Apply opening to remove noise
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # Apply closing to connect text
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Invert back
    result = cv2.bitwise_not(closed)

    return result


def _apply_morphology3(img):
    """Morphological operations with top-hat transform to enhance small details."""
    # Ensure image is grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Create kernels
    small_kernel = np.ones((2, 2), np.uint8)
    large_kernel = np.ones((5, 5), np.uint8)

    # Apply top-hat transform to enhance small details
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, large_kernel)

    # Add tophat to original
    enhanced = cv2.add(gray, tophat)

    # Apply thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Apply closing to connect text
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, small_kernel, iterations=1)

    # Invert back
    result = cv2.bitwise_not(closed)

    return result


def compare_all_methods(image_path, display=True, save_dir=None):
    """
    Apply all preprocessing methods to an image and display/save the results.

    Args:
        image_path (str): Path to the input image
        display (bool): Whether to display the results
        save_dir (str, optional): Directory to save processed images

    Returns:
        dict: Dictionary mapping method names to processed image paths
    """
    methods = ["adaptive", "contrast", "threshold", "glare", "morphology", "multi"]
    results = {}

    # Create save directory if it doesn't exist
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for method in methods:
        # Create save path if directory is provided
        save_path = None
        if save_dir:
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            save_path = os.path.join(save_dir, f"{name}_{method}{ext}")

        # Process the image
        processed_path = preprocess_image(
            image_path, method=method, display=display, save_path=save_path
        )
        results[method] = processed_path

    return results


def test_all_preprocessing_methods(image_path, display=True):
    """
    Test all preprocessing methods on an image and evaluate OCR results for each

    Args:
        image_path (str): Path to the input image
        display (bool): Whether to display the processed images

    Returns:
        dict: Dictionary with evaluation results for each method
    """
    # Create a directory for processed images
    base_dir = os.path.dirname(image_path)
    test_dir = os.path.join(base_dir, "test_results")
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    # Initialize OCR
    ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=True)

    # Test original image as baseline
    print("\n===== TESTING ORIGINAL IMAGE =====")
    original_text = extract_ingredients_from_ocr(image_path, ocr)
    if original_text is not None:
        original_ingredients = parse_ingredients_from_ocr(original_text)
        print(f"Found {len(original_ingredients)} ingredients in original image")
    else:
        original_ingredients = None

    # Process with each method
    methods = [
        "adaptive_threshold1",
        "adaptive_threshold2",
        "adaptive_threshold3",
        "enhance_contrast1",
        "enhance_contrast2",
        "enhance_contrast3",
        "basic_threshold1",
        "basic_threshold2",
        "basic_threshold3",
        "reduce_glare1",
        "reduce_glare2",
        "morphology1",
        "morphology2",
        "morphology3",
    ]
    results = {}

    for method in methods:
        print(f"\n===== TESTING {method.upper()} PREPROCESSING =====")
        # Process the image
        processed_path = preprocess_image(
            image_path,
            method=method,
            display=display,
            save_path=os.path.join(test_dir, f"processed_{method}.jpg"),
        )

        # Extract text with OCR
        processed_text = extract_ingredients_from_ocr(processed_path, ocr)
        if processed_text is None:
            continue

        # Parse ingredients
        processed_ingredients = parse_ingredients_from_ocr(processed_text)

        # Store results
        results[method] = {
            "path": processed_path,
            "ingredient_count": len(processed_ingredients),
            "ingredients": processed_ingredients,
            "raw_text": processed_text,
        }

        print(
            f"Found {len(processed_ingredients)} ingredients with {method} preprocessing"
        )

    # Show results summary
    print("\n===== RESULTS SUMMARY =====")
    if original_ingredients is not None:
        print(f"Original image: {len(original_ingredients)} ingredients")
        best_count = len(original_ingredients)
    else:
        best_count = 0

    best_method = None
    for method, result in results.items():
        count = result["ingredient_count"]
        print(f"{method.capitalize()}: {count} ingredients")

        if count > best_count:
            best_count = count
            best_method = method

    if best_method:
        print(f"\nBest preprocessing method: {best_method} ({best_count} ingredients)")
        print("\nIngredients found:")
        for i, ing in enumerate(results[best_method]["ingredients"]):
            print(f"{i+1}. {ing}")
    else:
        print("\nOriginal image provided best results")
        print("\nIngredients found:")
        for i, ing in enumerate(original_ingredients):
            print(f"{i+1}. {ing}")

    return results, best_method, best_count


def test_image(image_path):
    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Process product label image to extract ingredients"
    )
    parser.add_argument(
        "--method",
        type=str,
        default="test_all",
        choices=[
            "adaptive",
            "contrast",
            "threshold",
            "glare",
            "morphology",
            "multi",
            "test_all",
        ],
        help="Image preprocessing method to use",
    )
    parser.add_argument(
        "--display", action="store_true", help="Display processed images"
    )
    parser.add_argument(
        "--output_dir", type=str, help="Directory to save processed images"
    )

    args = parser.parse_args()

    return test_all_preprocessing_methods(image_path, display=False)
    # Initialize PaddleOCR
    # ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)


"""    for i in range(1, 7):
        image_path = f"product_images/product_label{i}.jpg"
        if True:
            # Test all methods and find the best one
            print(f"Testing all preprocessing methods on {image_path}")
            results = test_all_preprocessing_methods(image_path, display=True)
"""


"""def multi_process(img):
    
    Apply multiple preprocessing techniques in a single pass to optimize text recognition.
    Handles the BGR/grayscale conversions properly at each step.

    Args:
        img: BGR input image

    Returns:
        processed: Grayscale processed image optimized for OCR
    
    # Keep a copy of the original image
    original = img.copy()

    # Step 2: Convert to grayscale with enhanced contrast
    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE again to the grayscale image
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray)

    # Step 3: Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(contrast_enhanced, 9, 15, 15)

    # Step 4: Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Step 5: Apply morphological operations to clean up the result
    # Create a kernel for morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

    # Remove small noise
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    # Close small gaps in text
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Optional: If text is inverted (white on black), invert it
    # Uncomment if needed:
    # closing = cv2.bitwise_not(closing)

    # Apply a slight blur to smooth edges
    final = cv2.GaussianBlur(closing, (3, 3), 0)

    return final"""
