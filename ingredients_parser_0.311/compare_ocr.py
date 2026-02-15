#!/usr/bin/env python3
"""
Compare PaddleOCR vs EasyOCR on the same image
This helps you see the improvement firsthand
"""

import cv2
import sys

def compare_ocr(image_path):
    """Compare both OCR engines on the same image"""
    
    print("\n" + "="*70)
    print("Ingredient Parser OCR Comparison: PaddleOCR vs EasyOCR")
    print("="*70)
    
    print(f"\nImage:  {image_path}")
    
    # Check image exists
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image from {image_path}")
        return
    
    print(f"Size: {img.shape[1]}x{img.shape[0]} pixels")
    
    # ============= EasyOCR =============
    print("\n" + "-"*70)
    print("Testing: EasyOCR (NEW)")
    print("-"*70)
    
    try:
        import easyocr
        print("Initializing EasyOCR...")
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        
        # Preprocess if needed
        max_dim = 1920
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img_easy = cv2.resize(img, (new_w, new_h))
            temp_path = "temp_compare.jpg"
            cv2.imwrite(temp_path, img_easy)
            print(f"Resized to {new_w}x{new_h}")
        else:
            temp_path = image_path
        
        print("Running OCR...")
        results = reader.readtext(temp_path, detail=0)
        
        print(f"\n✓ SUCCESS - Found {len(results)} text regions")
        print("\nDetected text:")
        for i, text in enumerate(results, 1):
            print(f"  {i}. {text}")
        
        easy_text = " ".join(results)
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        easy_text = None
    
    # ============= PaddleOCR =============
    print("\n" + "-"*70)
    print("Testing: PaddleOCR (OLD)")
    print("-"*70)
    
    try:
        from paddleocr import PaddleOCR
        print("Initializing PaddleOCR...")
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            rec_algorithm="SVTR_LCNet",
            use_space_char=True,
            show_log=False
        )
        
        print("Running OCR...")
        result = ocr.ocr(image_path, cls=True)
        
        if result and result[0]:
            texts = [line[1][0] for line in result[0]]
            print(f"\n✓ SUCCESS - Found {len(texts)} text regions")
            print("\nDetected text:")
            for i, text in enumerate(texts, 1):
                print(f"  {i}. {text}")
            
            paddle_text = " ".join(texts)
        else:
            print("✗ No text detected")
            paddle_text = None
            
    except Exception as e:
        print(f"✗ FAILED: {e}")
        paddle_text = None
    
    # ============= Comparison =============
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    if easy_text and paddle_text:
        print(f"\nEasyOCR detected: {len(easy_text.split())} words")
        print(f"PaddleOCR detected: {len(paddle_text.split())} words")
        
        # Simple comparison
        easy_words = set(easy_text.lower().split())
        paddle_words = set(paddle_text.lower().split())
        
        common = easy_words & paddle_words
        easy_only = easy_words - paddle_words
        paddle_only = paddle_words - easy_words
        
        print(f"\nWords detected by both: {len(common)}")
        print(f"Only EasyOCR detected: {len(easy_only)}")
        print(f"Only PaddleOCR detected: {len(paddle_only)}")
        
        if easy_only:
            print(f"\nEasyOCR extras (first 10): {list(easy_only)[:10]}")
        if paddle_only:
            print(f"PaddleOCR extras (first 10): {list(paddle_only)[:10]}")
    
    elif easy_text:
        print("\n✓ EasyOCR succeeded")
        print("✗ PaddleOCR failed")
        print("\n→ EasyOCR is more robust for this image!")
    
    elif paddle_text:
        print("\n✗ EasyOCR failed")
        print("✓ PaddleOCR succeeded")
        print("\n→ PaddleOCR works for this image")
    
    else:
        print("\n✗ Both failed on this image")
        print("→ Try preprocessing or using a different image")
    
    print("\n")


if __name__ == "__main__":
    # Default test images
    test_images = [
        "product_images/product_label6.jpg",
        "product_images/image4.jpeg",
        "product_images/image0.jpeg",
    ]
    
    # Use command line argument if provided
    if len(sys.argv) > 1:
        test_images = [sys.argv[1]]
    
    for img_path in test_images:
        try:
            compare_ocr(img_path)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
    
    print("="*70)
    print("Comparison complete!")
    print("\nUsage: python3 compare_ocr.py [image_path]")
    print("="*70 + "\n")
