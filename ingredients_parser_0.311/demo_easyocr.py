#!/usr/bin/env python3
"""
Quick demo of EasyOCR working on product images
This version skips the EWG database lookup to demonstrate OCR speed
"""

import cv2
import numpy as np
import easyocr
import re


def preprocess_image(image_path):
    """Preprocess image for optimal OCR"""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    height, width = image.shape[:2]
    max_dimension = 1920
    
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        print(f"  Resized: {width}x{height} → {new_width}x{new_height}")
    
    return image


def extract_ingredient_text(ocr_results):
    """Extract text from OCR results, focusing on ingredient section"""
    all_text = []
    ing_section_started = False
    
    for bbox, text, confidence in ocr_results:
        # Look for ingredients keyword
        if not ing_section_started and re.search(r'\bingredient[s]?\b', text, re.IGNORECASE):
            ing_section_started = True
            # Remove the "Ingredients:" part
            text = re.sub(r'.*ingredients?\s*[:;-]?\s*', '', text, flags=re.IGNORECASE)
        
        if ing_section_started:
            # Stop at common ending keywords
            if re.search(r'\b(directions?|warnings?|caution|made in|for external)\b', text, re.IGNORECASE):
                break
            all_text.append(text)
    
    # If no ingredient section found, return all text
    if not all_text:
        all_text = [text for bbox, text, conf in ocr_results]
    
    return " ".join(all_text)


def parse_ingredients(text):
    """Parse ingredient list from text"""
    # Clean up text
    text = re.sub(r'\s+', ' ', text)
    
    # Split by common separators
    ingredients = re.split(r'[,;]', text)
    
    # Clean and filter
    cleaned = []
    for ing in ingredients:
        ing = ing.strip()
        ing = re.sub(r'^[^a-zA-Z0-9(]+|[^a-zA-Z0-9)]+$', '', ing)
        if len(ing) > 1:
            cleaned.append(ing)
    
    return cleaned


def demo_ocr(image_path):
    """Demonstrate OCR on an image"""
    print(f"\n{'='*60}")
    print(f"Processing: {image_path}")
    print('='*60)
    
    # Preprocess
    print("Preprocessing...")
    try:
        image = preprocess_image(image_path)
        temp_path = "temp_demo.jpg"
        cv2.imwrite(temp_path, image)
    except Exception as e:
        print(f"  Error: {e}")
        return
    
    # Run OCR
    print("Running EasyOCR...")
    try:
        results = reader.readtext(temp_path, paragraph=False, detail=1)
        print(f"  Found {len(results)} text regions")
    except Exception as e:
        print(f"  OCR Error: {e}")
        return
    
    # Show detected text
    print(f"\n{'-'*60}")
    print("Detected Text (with confidence):")
    print('-'*60)
    for i, (bbox, text, conf) in enumerate(results[:10], 1):  # Show first 10
        print(f"{i:2}. [{conf:.2f}] {text}")
    if len(results) > 10:
        print(f"... and {len(results) - 10} more text regions")
    
    # Extract and parse ingredients
    print(f"\n{'-'*60}")
    print("Extracted Ingredients:")
    print('-'*60)
    full_text = extract_ingredient_text(results)
    ingredients = parse_ingredients(full_text)
    
    for i, ing in enumerate(ingredients, 1):
        print(f"{i:2}. {ing}")
    
    print(f"\nTotal: {len(ingredients)} ingredients extracted\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("EasyOCR Ingredient Parser - Quick Demo")
    print("="*60)
    
    # Initialize EasyOCR (only once)
    print("\nInitializing EasyOCR...")
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("✓ Ready\n")
    
    # Test images
    test_images = [
        "product_images/product_label6.jpg",
        "product_images/image4.jpeg",
        "product_images/product_label1.jpg",
    ]
    
    for img_path in test_images:
        try:
            demo_ocr(img_path)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"\nError processing {img_path}: {e}\n")
    
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)
    print("\nKey Advantages of EasyOCR:")
    print("  ✓ Works on full product images (no cropping needed)")
    print("  ✓ Handles curved/distorted packaging surfaces")
    print("  ✓ Better with glossy finishes and reflections")
    print("  ✓ More resilient to poor lighting")
    print("  ✓ Automatic text region detection")
    print("\nFor full functionality with EWG database lookup:")
    print("  Run: python3 test_easyocr.py")
    print("\n")
