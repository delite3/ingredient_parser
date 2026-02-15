import easyocr
import cv2
import re

reader = easyocr.Reader(['en'])
image = cv2.imread('product_label.jpg')
results = reader.readtext(image)

# Combine all text
all_text = " ".join([text for (_, text, _) in results])

# Clean up common OCR errors in ingredient lists
cleaned_text = all_text

# Fix specific punctuation issues you mentioned
cleaned_text = cleaned_text.replace("; ", ", ")
cleaned_text = cleaned_text.replace(";", ",")
cleaned_text = cleaned_text.replace(": ", ", ")
cleaned_text = cleaned_text.replace(":", ",")

# Fix cases where there should be hyphens
# You may need to adjust these patterns based on your specific ingredient list structure
cleaned_text = re.sub(r'(\w+)(\s+)(\w+benzimidazole)', r'\1-\3', cleaned_text)
cleaned_text = re.sub(r'(\w+)(\s+)(\w+zoylmethane)', r'\1-\3', cleaned_text)

# Remove any double commas created during cleaning
cleaned_text = cleaned_text.replace(",,", ",")

# Split into individual ingredients
if "Ingredients" in cleaned_text:
    # Remove the "Ingredients:" prefix
    ingredients_text = re.sub(r'^.*?Ingredients[,:]?\s*', '', cleaned_text)
else:
    ingredients_text = cleaned_text

# Get final list of ingredients
ingredients = [ingredient.strip() for ingredient in ingredients_text.split(',')]

# Print clean list
print("Cleaned Ingredient List:")
for ingredient in ingredients:
    if ingredient:  # Skip empty entries
        print(f"- {ingredient}")