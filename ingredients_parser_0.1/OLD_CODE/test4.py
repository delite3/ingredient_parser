import requests
from bs4 import BeautifulSoup

# Set headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.ewg.org/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

search_term = "glycerin"
base_url = "http://www.ewg.org"
search_url = f"{base_url}/skindeep/search/?search={search_term}"

# Get search results page
response = requests.get(search_url, headers=headers)
print(f"Search page status code: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.select('.product-tile')
    
    if not products:
        print("No products found.")
        exit()
    
    # Get the first (best matching) product
    best_match = products[0]
    
    # Find the product link
    product_link_element = best_match.select_one('a')
    if not product_link_element:
        print("Could not find product link.")
        exit()
    
    product_url = base_url + product_link_element['href']
    product_name = best_match.select_one('.product-name').text.strip() if best_match.select_one('.product-name') else "Unknown"
    
    print(f"Best match: {product_name}")
    print(f"Product URL: {product_url}")
    
    # Get the detailed product page
    product_response = requests.get(product_url, headers=headers)
    print(f"Product page status code: {product_response.status_code}")
    
    if product_response.status_code == 200:
        product_soup = BeautifulSoup(product_response.text, 'html.parser')
        
        # Extract product details
        # Note: The exact selectors will depend on the page structure
        product_score = product_soup.select_one('.product-score')
        score_text = product_score.text.strip() if product_score else "Score not found"
        
        # Get ingredients if available
        ingredients_section = product_soup.select_one('.product-ingredients')
        ingredients = []
        
        if ingredients_section:
            ingredient_items = ingredients_section.select('.ingredient-item')
            for item in ingredient_items:
                name_elem = item.select_one('.ingredient-name')
                score_elem = item.select_one('.ingredient-score')
                
                ing_name = name_elem.text.strip() if name_elem else "Unknown"
                ing_score = score_elem.text.strip() if score_elem else "Unknown"
                
                ingredients.append(f"{ing_name} (Score: {ing_score})")
        
        # Print detailed information
        print(f"\nProduct Details for {product_name}:")
        print(f"Overall Score: {score_text}")
        
        if ingredients:
            print("\nIngredients:")
            for ing in ingredients:
                print(f"- {ing}")
        else:
            print("\nNo ingredients information found.")
            
        # Get additional information sections
        about_section = product_soup.select_one('.about-section')
        if about_section:
            print("\nAbout this product:")
            print(about_section.text.strip())
        
        # You can add more sections as needed based on the page structure
        
    else:
        print(f"Failed to access the product page: {product_response.status_code}")
else:
    print(f"Failed to access the search page: {response.status_code}")