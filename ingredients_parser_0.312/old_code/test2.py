import cv2
import numpy as np


def display_image(image, title="Image", wait=True):
    """Display an image in a window."""
    cv2.imshow(title, image)
    if wait:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def superresolution_sharpen(image, scale=2):
    """Increase resolution and apply advanced sharpening."""
    # Resize to larger dimensions
    height, width = image.shape[:2] if len(image.shape) > 1 else image.shape
    enlarged = cv2.resize(
        image, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC
    )

    # Apply unsharp mask with careful parameters to preserve small details
    blurred = cv2.GaussianBlur(enlarged, (0, 0), 3)
    sharpened = cv2.addWeighted(enlarged, 1.5, blurred, -0.5, 0)

    # Resize back to original dimensions
    result = cv2.resize(sharpened, (width, height), interpolation=cv2.INTER_AREA)

    return result


def pure_black_and_white(image_path, output_path=None, stretch_factor=1.2):
    """
    Convert any label image to pure black and white with horizontal stretching.
    Works with any color combination labels.
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Stretch horizontally
    height, width = image.shape[:2]
    new_width = int(width * stretch_factor)
    stretched = cv2.resize(image, (new_width, height), interpolation=cv2.INTER_CUBIC)

    # Step 1: Denoise while preserving edges
    denoised = cv2.fastNlMeansDenoisingColored(stretched, None, 10, 10, 7, 21)

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

    # Step 3: Enhance with superresolution sharpening
    enhanced = superresolution_sharpen(gray)

    # Step 4: Apply Otsu's thresholding for robust black and white conversion
    # This automatically determines the optimal threshold value
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Alternatively, try adaptive thresholding if Otsu doesn't work well
    # adaptive = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    #                                cv2.THRESH_BINARY, 11, 2)

    # Save result if output path is provided
    if output_path:
        cv2.imwrite(output_path, binary)

    return binary


def detect_text_any_color(image_path, output_path=None, stretch_factor=1.2):
    """
    Detect text in any color combination and convert to pure black and white.
    Works by detecting edges and then thresholding.
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Stretch horizontally
    height, width = image.shape[:2]
    new_width = int(width * stretch_factor)
    stretched = cv2.resize(image, (new_width, height), interpolation=cv2.INTER_CUBIC)

    # Step 1: Denoise
    denoised = cv2.fastNlMeansDenoisingColored(stretched, None, 10, 10, 7, 21)

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

    # Step 3: Apply Canny edge detection to find text edges
    edges = cv2.Canny(gray, 100, 200)

    # Step 4: Dilate edges slightly to connect text components
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)

    # Step 5: Fill small gaps in text
    kernel = np.ones((3, 3), np.uint8)
    closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)

    # Step 6: Invert so text is black on white
    inverted = cv2.bitwise_not(closed)

    # Step 7: Clean up small noise
    cleaned = cv2.medianBlur(inverted, 3)

    # Save result if output path is provided
    if output_path:
        cv2.imwrite(output_path, cleaned)

    return cleaned


def extreme_contrast(image_path, output_path=None, stretch_factor=1.2):
    """
    Create extreme black and white contrast with no noise.
    Combines multiple approaches to handle even the trickiest labels.
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Stretch horizontally
    height, width = image.shape[:2]
    new_width = int(width * stretch_factor)
    stretched = cv2.resize(image, (new_width, height), interpolation=cv2.INTER_CUBIC)

    # Step 1: Denoise while preserving edges
    denoised = cv2.fastNlMeansDenoisingColored(stretched, None, 10, 10, 7, 21)

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

    # Step 3: Apply CLAHE for local contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray)

    # Step 4: Sharpen
    sharpened = superresolution_sharpen(contrast_enhanced)

    # Try multiple binarization methods and combine results

    # Method 1: Otsu's thresholding
    _, otsu = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Method 2: Adaptive thresholding
    adaptive = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Method 3: Simple global threshold at mid-level
    _, global_thresh = cv2.threshold(sharpened, 127, 255, cv2.THRESH_BINARY)

    # Combine the results (voting system)
    combined = np.zeros_like(otsu)
    combined[(otsu == 255) & (adaptive == 255)] = (
        255  # Pixels that both methods agree are white
    )
    combined[(global_thresh == 0) & (otsu == 0)] = (
        0  # Pixels that both methods agree are black
    )

    # For the rest, use the values from the adaptive threshold
    mask = ((otsu == 255) & (adaptive == 255)) | ((global_thresh == 0) & (otsu == 0))
    combined[~mask] = adaptive[~mask]

    # Save result if output path is provided
    if output_path:
        cv2.imwrite(output_path, combined)

    return combined


# Process a single image
result = pure_black_and_white(
    "product_images/image0.jpeg", "processed_label.jpg", stretch_factor=1.2
)
display_image(result)

# If that doesn't work well, try the alternative
result2 = detect_text_any_color("product_images/image0.jpeg", "processed_label2.jpg")
display_image(result2)

# For the most difficult labels
result3 = extreme_contrast("product_images/image0.jpeg", "processed_label3.jpg")
display_image(result3)
