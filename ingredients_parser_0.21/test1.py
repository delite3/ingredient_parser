import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import argparse
from paddleocr import PaddleOCR
import re

# Import the preprocessing functions from your existing code
# You can either import directly if the file is in your path, or copy the functions here
# For this example, I'll assume you have the file as 'ingredient_processor.py'
# and import the necessary functions

# Alternatively, if you prefer to keep it self-contained:
from image2text import (
    preprocess_image,
    _adaptive_threshold,
    _enhance_contrast,
    _basic_threshold,
    _reduce_glare,
    _apply_morphology,
    multi_process,
    parse_ingredients_from_ocr,
    extract_ingredients_from_ocr,
)


def visualize_all_methods(
    image_path, save_output=False, with_ocr=False, display_size=(15, 12)
):
    """
    Process an image with all methods and display them in subplots for comparison.

    Args:
        image_path (str): Path to the input image
        save_output (bool): Whether to save the visualization
        with_ocr (bool): Whether to run OCR on each processed image
        display_size (tuple): Figure size for the display (width, height)

    Returns:
        None (displays the plot)
    """
    # Check if the file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return

    # Read the original image
    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"Error: Unable to read image at {image_path}")
        return

    # Define all preprocessing methods
    methods = [
        "original",
        "adaptive",
        "contrast",
        "threshold",
        "glare",
        "morphology",
        "multi",
        "punctuation_enhancement",
        "small_text",
    ]

    # Create a mapping from method name to processed image
    processed_images = {}
    original_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    processed_images["original"] = original_rgb

    # Process with standard methods
    for method in methods[1:7]:  # Skip 'original'
        try:
            if method == "adaptive":
                processed = _adaptive_threshold(original_img.copy())
            elif method == "contrast":
                processed = _enhance_contrast(original_img.copy())
            elif method == "threshold":
                processed = _basic_threshold(original_img.copy())
            elif method == "glare":
                processed = _reduce_glare(original_img.copy())
            elif method == "morphology":
                processed = _apply_morphology(original_img.copy())
            elif method == "multi":
                processed = multi_process(original_img.copy())

            processed_images[method] = processed
        except Exception as e:
            print(f"Error processing with method {method}: {e}")
            # Add a blank image if processing fails
            processed_images[method] = np.ones_like(original_img) * 255

    # Add custom punctuation-optimized methods
    # Punctuation Enhancement preset
    try:
        img = original_img.copy()
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply bilateral filter to preserve small details
        bilateral = cv2.bilateralFilter(gray, 9, 15, 15)
        # Apply slight sharpening
        kernel = np.array([[-1, -1, -1], [-1, 10, -1], [-1, -1, -1]]) / 5
        sharpened = cv2.filter2D(bilateral, -1, kernel)
        # Apply adaptive threshold with smaller block size
        punctuation = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2
        )
        # Apply closing to connect broken parts
        kernel = np.ones((2, 2), np.uint8)
        punctuation = cv2.morphologyEx(
            punctuation, cv2.MORPH_CLOSE, kernel, iterations=1
        )
        processed_images["punctuation_enhancement"] = punctuation
    except Exception as e:
        print(f"Error processing with punctuation enhancement: {e}")
        processed_images["punctuation_enhancement"] = np.ones_like(original_img) * 255

    # Small Text Enhancement preset
    try:
        img = original_img.copy()
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Increase contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        # Apply bilateral filter with smaller diameter
        bilateral = cv2.bilateralFilter(gray, 7, 10, 10)
        # Apply heavy sharpening
        kernel = np.array([[-1, -1, -1], [-1, 12, -1], [-1, -1, -1]]) / 4
        sharpened = cv2.filter2D(bilateral, -1, kernel)
        # Apply adaptive threshold with small block size
        small_text = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 7, 2
        )
        processed_images["small_text"] = small_text
    except Exception as e:
        print(f"Error processing with small text enhancement: {e}")
        processed_images["small_text"] = np.ones_like(original_img) * 255

    # Initialize OCR if needed
    ocr_results = {}
    if with_ocr:
        print("Initializing OCR and processing images...")
        try:
            ocr = PaddleOCR(use_angle_cls=True, lang="en")

            # Create temporary directory for saving processed images
            tmp_dir = "tmp_ocr_processed"
            os.makedirs(tmp_dir, exist_ok=True)

            for method, img in processed_images.items():
                # Skip original for OCR if it's RGB (need to convert back to BGR)
                if method == "original":
                    ocr_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                else:
                    # If grayscale, no need to convert
                    ocr_img = img

                # Save temporarily
                tmp_path = os.path.join(tmp_dir, f"{method}.jpg")
                cv2.imwrite(tmp_path, ocr_img)

                # Run OCR
                ocr_text = extract_ingredients_from_ocr(tmp_path, ocr)
                if ocr_text:
                    ingredients = parse_ingredients_from_ocr(ocr_text)
                    ocr_results[method] = {
                        "raw_text": ocr_text,
                        "ingredients": ingredients,
                        "count": len(ingredients) if ingredients else 0,
                    }
                else:
                    ocr_results[method] = {
                        "raw_text": "OCR failed",
                        "ingredients": [],
                        "count": 0,
                    }

            # Clean up temporary files
            for file in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, file))
            os.rmdir(tmp_dir)
        except Exception as e:
            print(f"Error running OCR: {e}")
            with_ocr = False

    # Create figure with subplots
    n_methods = len(methods)
    n_cols = 3  # Number of columns in the grid
    n_rows = (n_methods + n_cols - 1) // n_cols  # Ceiling division

    fig = plt.figure(figsize=display_size)
    gs = GridSpec(n_rows, n_cols, figure=fig)

    # Add title to the overall figure
    fig.suptitle(
        f"Image Processing Methods Comparison: {os.path.basename(image_path)}",
        fontsize=16,
        y=0.98,
    )

    # Plot each processed image
    for i, method in enumerate(methods):
        row = i // n_cols
        col = i % n_cols

        ax = fig.add_subplot(gs[row, col])

        # Get the processed image
        processed = processed_images.get(
            method, np.ones((100, 100), dtype=np.uint8) * 255
        )

        # Display the image
        if len(processed.shape) == 3:  # Color image
            ax.imshow(processed)
        else:  # Grayscale image
            ax.imshow(processed, cmap="gray")

        # Add title
        method_name = method.replace("_", " ").title()
        if with_ocr and method in ocr_results:
            ingredient_count = ocr_results[method]["count"]
            ax.set_title(f"{method_name}\nIngredients: {ingredient_count}", fontsize=12)
        else:
            ax.set_title(method_name, fontsize=12)

        # Remove ticks
        ax.set_xticks([])
        ax.set_yticks([])

    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for the suptitle

    # Add OCR summary if available
    if with_ocr:
        best_method = max(ocr_results.items(), key=lambda x: x[1]["count"])[0]
        best_count = ocr_results[best_method]["count"]

        plt.figtext(
            0.5,
            0.01,
            f"Best method: {best_method.replace('_', ' ').title()} with {best_count} ingredients detected",
            ha="center",
            fontsize=14,
            bbox={"facecolor": "orange", "alpha": 0.2, "pad": 5},
        )

    # Save or display the plot
    if save_output:
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = f"{base_name}_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Visualization saved to {output_path}")

    plt.show()


def extract_punctuation_marks(image_path, method="punctuation_enhancement"):
    """
    Process an image and highlight detected commas and dots

    Args:
        image_path (str): Path to the input image
        method (str): Preprocessing method to use

    Returns:
        None (displays the plot)
    """
    # Read the original image
    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"Error: Unable to read image at {image_path}")
        return

    # Process the image with the selected method
    if method == "punctuation_enhancement":
        img = original_img.copy()
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply bilateral filter to preserve small details
        bilateral = cv2.bilateralFilter(gray, 9, 15, 15)
        # Apply slight sharpening
        kernel = np.array([[-1, -1, -1], [-1, 10, -1], [-1, -1, -1]]) / 5
        sharpened = cv2.filter2D(bilateral, -1, kernel)
        # Apply adaptive threshold with smaller block size
        processed = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2
        )
        # Apply closing to connect broken parts
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel, iterations=1)
    else:
        # Use specified method from imported functions
        processed = preprocess_image(image_path, method=method, display=False)

    # Make a copy for visualization
    vis_img = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
    orig_vis = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)

    # Find contours
    contours, _ = cv2.findContours(
        processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter contours based on size (commas and dots are small)
    punctuation = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        # Filter by area and dimensions
        if area < 100 and area > 3:  # Adjust these thresholds based on your images
            if w < 10 and h < 10:  # Small size
                # Dots are roughly square
                if 0.8 < w / h < 1.2:
                    punctuation.append((contour, "dot", (x, y, w, h)))
                # Commas are taller than wide
                elif h / w > 1.2 and h / w < 3:
                    punctuation.append((contour, "comma", (x, y, w, h)))

    # Count dots and commas
    dot_count = sum(1 for c in punctuation if c[1] == "dot")
    comma_count = sum(1 for c in punctuation if c[1] == "comma")

    # Create figure with original, processed, and highlighted images
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Original image
    axes[0].imshow(orig_vis)
    axes[0].set_title("Original Image")
    axes[0].set_xticks([])
    axes[0].set_yticks([])

    # Processed image
    axes[1].imshow(processed, cmap="gray")
    axes[1].set_title(f"Processed Image ({method})")
    axes[1].set_xticks([])
    axes[1].set_yticks([])

    # Highlighted punctuation
    highlight_img = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
    for contour, punc_type, (x, y, w, h) in punctuation:
        if punc_type == "dot":
            # Draw blue rectangle around dots
            cv2.rectangle(highlight_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        else:
            # Draw green rectangle around commas
            cv2.rectangle(highlight_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    axes[2].imshow(highlight_img)
    axes[2].set_title(f"Detected Punctuation: {dot_count} dots, {comma_count} commas")
    axes[2].set_xticks([])
    axes[2].set_yticks([])

    plt.tight_layout()

    # Add summary
    fig.suptitle(
        f"Punctuation Detection: {os.path.basename(image_path)}", fontsize=16, y=0.98
    )
    plt.subplots_adjust(top=0.85)

    # Save or display
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = f"{base_name}_punctuation_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Punctuation analysis saved to {output_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize image processing methods for OCR"
    )
    parser.add_argument("image_path", type=str, help="Path to the input image")
    parser.add_argument(
        "--save", action="store_true", help="Save visualization to file"
    )
    parser.add_argument(
        "--ocr", action="store_true", help="Run OCR on each processed image"
    )
    parser.add_argument(
        "--punctuation",
        action="store_true",
        help="Analyze and highlight punctuation marks",
    )
    import glob

    # args = parser.parse_args()
    folder = glob.glob("product_images/*")
    for image in folder:
        extract_punctuation_marks(image)


"""    if args.punctuation:
        extract_punctuation_marks(image)
    else:
        visualize_all_methods(image, save_output=args.save, with_ocr=args.ocr)
"""

if __name__ == "__main__":
    main()
