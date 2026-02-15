import cv2
import numpy as np
from skimage import exposure, morphology, filters
from paddleocr import PaddleOCR


def binarize_with_detail_preservation(gray, block_size=15, offset=10):
    """
    Advanced binarization that preserves small details like commas and periods.
    Uses Sauvola thresholding which is better for document images than standard methods.
    """
    """image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    display_image(gray)"""
    # Apply bilateral filter to reduce noise while preserving edges
    smoothed = cv2.bilateralFilter(gray, 5, 75, 75)

    # Calculate local threshold using Sauvola method (better for text)
    from skimage.filters import threshold_sauvola

    threshold = threshold_sauvola(smoothed, window_size=block_size, k=0.2)

    # Apply threshold
    binary = (smoothed > threshold).astype(np.uint8) * 255

    return binary


def enhance_punctuation(gray, min_size=2, max_size=10):
    """
    Specifically designed to enhance small elements like commas and periods.
    Uses morphological operations to identify and enhance small connected components.
    """
    """image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Ensure binary image
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    display_image(gray)"""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find all connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)

    # Create mask for small components (punctuation)
    punctuation_mask = np.zeros_like(binary)
    for i in range(1, num_labels):  # Skip background (label 0)
        area = stats[i, cv2.CC_STAT_AREA]
        if min_size <= area <= max_size:  # Filter based on typical punctuation size
            component_mask = (labels == i).astype(np.uint8) * 255
            # Dilate slightly to enhance visibility
            kernel = np.ones((3, 3), np.uint8)
            component_mask = cv2.dilate(component_mask, kernel, iterations=1)
            punctuation_mask = cv2.bitwise_or(punctuation_mask, component_mask)

    # Combine enhanced punctuation with original binary
    result = cv2.bitwise_or(binary, punctuation_mask)

    # Invert back to get black text on white background
    return cv2.bitwise_not(result)


def superresolution_sharpen(gray, scale=2):
    """
    Increase resolution and apply advanced sharpening to make fine details more distinct.
    """
    # Convert to grayscale if needed
    """  
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    display_image(gray)
    # Resize to larger dimensions"""
    height, width = gray.shape
    enlarged = cv2.resize(
        gray, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC
    )
    display_image(enlarged)
    # Apply unsharp mask with careful parameters to preserve small details
    blurred = cv2.GaussianBlur(enlarged, (0, 0), 3)
    sharpened = cv2.addWeighted(enlarged, 1.5, blurred, -0.5, 0)
    display_image(sharpened)
    # Apply edge enhancement
    edge_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    enhanced = cv2.filter2D(sharpened, -1, edge_kernel)
    display_image(enhanced)
    # Resize back to original dimensions
    result = cv2.resize(enhanced, (width, height), interpolation=cv2.INTER_AREA)
    display_image(result)
    return result


def preprocess_text_with_punctuation(image_path, output_path=None):
    """
    Complete preprocessing pipeline optimized for ingredient labels with punctuation.
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Step 1: Denoise while preserving edges
    denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    display_image(denoised)
    # Step 2: Convert to grayscale and enhance contrast
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    display_image(gray)
    # Step 3: Superresolution and sharpening
    enhanced = superresolution_sharpen(gray)
    display_image(enhanced)
    # Step 4: Binarize with detail preservation
    # binary = binarize_with_detail_preservation(enhanced)
    # display_image(binary)
    # Step 5: Specifically enhance small elements like punctuation
    # result = enhance_punctuation(enhanced)
    # display_image(result)
    # Save result if output path is provided
    if output_path:
        cv2.imwrite(output_path, enhanced)
    display_image(enhanced)
    return enhanced


def optimize_for_paddleocr(image_path, output_path=None):
    """
    Process specifically for PaddleOCR with focus on punctuation recognition.
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # Increase resolution - helps with fine details
    height, width = image.shape[:2]
    image = cv2.resize(image, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

    # Step 1: Reduce noise while preserving edges with guided filter
    denoised = cv2.ximgproc.guidedFilter(image, image, 3, 0.2)

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

    # Step 3: Increase contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray)

    # Step 4: Thin-plate spline (approximated) sharpening for fine details
    blurred = cv2.GaussianBlur(contrast_enhanced, (0, 0), 3)
    sharpened = cv2.addWeighted(contrast_enhanced, 1.75, blurred, -0.75, 0)

    # Step 5: Black and white with adaptive threshold
    binary = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Step 6: Clean up small noise
    kernel = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # Create punctuation mask by finding very small circular elements
    circles = cv2.HoughCircles(
        binary,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=10,
        param1=50,
        param2=10,
        minRadius=1,
        maxRadius=4,
    )

    punctuation_mask = np.zeros_like(binary)
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for x, y, r in circles:
            cv2.circle(punctuation_mask, (x, y), r, 255, -1)

    # Combine with original binary
    result = cv2.bitwise_or(opened, punctuation_mask)

    # Save result if output path is provided
    if output_path:
        cv2.imwrite(output_path, result)

    return result


def display_image(image, title="Image", wait=True):
    """
    Display an image in a window.

    Args:
        image: The image to display (numpy array)
        title: Window title (string)
        wait: If True, waits for a key press before continuing
    """
    cv2.imshow(title, image)
    if wait:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


# Process the image
processed = preprocess_text_with_punctuation("product_images/image0.jpeg")

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

print(result)
print("###")
