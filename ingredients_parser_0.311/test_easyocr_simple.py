import cv2
import numpy as np
import easyocr

# Simple test to verify EasyOCR installation

print("Testing EasyOCR installation...")
print("="*50)

# Initialize reader
print("Initializing EasyOCR reader...")
try:
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("✓ Reader initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize reader: {e}")
    exit(1)

# Test with a simple synthetic image
print("\nTest 1: Synthetic image")
try:
    # Create a simple test image with text
    img = np.zeros((100, 400, 3), dtype=np.uint8)
    img.fill(255)
    cv2.putText(img, 'Test Ingredients: Water, Salt', (10, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Save test image
    cv2.imwrite('test_synthetic.jpg', img)
    
    # Try OCR
    result = reader.readtext('test_synthetic.jpg', detail=0)
    print(f"✓ Detected text: {result}")
except Exception as e:
    print(f"✗ Failed on synthetic image: {e}")

# Test with real images
print("\nTest 2: Real product images")
import os
image_files = [f for f in os.listdir('product_images') if f.endswith(('.jpg', '.jpeg', '.png'))]

for img_file in image_files[:3]:  # Test first 3 images
    img_path = os.path.join('product_images', img_file)
    print(f"\nTrying {img_file}...")
    
    # Check if image is readable
    img = cv2.imread(img_path)
    if img is None:
        print(f"  ✗ Cannot read image")
        continue
    
    print(f"  Image shape: {img.shape}")
    
    # Resize if too large (EasyOCR works better with moderate sizes)
    max_dimension = 1920
    height, width = img.shape[:2]
    
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height))
        temp_path = 'temp_resized.jpg'
        cv2.imwrite(temp_path, img)
        print(f"  Resized to: {img.shape}")
    else:
        temp_path = img_path
    
    try:
        # Try with detail=0 first (returns only text, not boxes)
        result = reader.readtext(temp_path, detail=0)
        print(f"  ✓ Successfully read {len(result)} text regions")
        if result:
            print(f"  First few detected texts: {result[:3]}")
    except Exception as e:
        print(f"  ✗ OCR failed: {str(e)[:100]}")
        
        # Try alternative parameters
        try:
            print("  Trying with batch_size=1...")
            result = reader.readtext(temp_path, detail=0, batch_size=1)
            print(f"  ✓ Success with batch_size=1: {len(result)} regions")
        except Exception as e2:
            print(f"  ✗ Still failed: {str(e2)[:100]}")

print("\n" + "="*50)
print("Diagnosis complete")
