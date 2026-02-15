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

search_term = "Caprylic/Capric Triglyceride"
search_url = f"http://www.ewg.org/skindeep/search/?search={search_term}"

# Get search results page
response = requests.get(search_url, headers=headers)
print(f"Search results status code: {response.status_code}")


def extract_ingredient_concerns(product_soup):
    """
    Extract all ingredient concerns from collapsible blocks in a product page.
    
    Args:
        product_soup (BeautifulSoup): The BeautifulSoup object of the product page
        
    Returns:
        dict: Dictionary with section titles as keys and lists of concern information as values
    """
    results = {}
    
    # Find the main ingredient concerns wrapper
    concerns_wrapper = product_soup.select_one('.ingredient-concerns-inner-wrapper')
    if not concerns_wrapper:
        return {"error": "No ingredient concerns wrapper found"}
    
    # Find all collapsible blocks within the concerns sources wrapper
    collapsable_blocks = concerns_wrapper.select('.concerns-sources-wrapper .collapsable-block')
    
    if not collapsable_blocks:
        return {"error": "No collapsible blocks found"}
    
    # Extract information from each block
    for i_, block in enumerate(collapsable_blocks):
        if i_ == 0:
            continue

        #concerns_block = product_soup.select_one('.concerns-block')
        if block:
            # Find the table within the concerns block
            concern_table = block.select_one('.chemical-concern-table')
            
            if concern_table:
                # Get all rows in the table body
                rows = concern_table.select('tbody tr')
                
                if rows:
                    print("Concerns:")
                    for row in rows:
                        # Get the concern and reference cells
                        cells = row.select('td')
                        if len(cells) >= 2:
                            concern = cells[0].text.strip()
                            reference = cells[1].text.strip()
                            print(f"- {concern} [{reference}]")
    
    return results


if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.select('.product-tile')
    
    best_match = None
    best_match_link = None
    
    # Find the product that best matches our search term
    for product in products:
        name_elem = product.select_one('.product-name')
        if name_elem and search_term.lower() in name_elem.text.lower():
            best_match = name_elem.text.strip()
            # Find the link to the product page
            link_elem = product.select_one('a')
            if link_elem and 'href' in link_elem.attrs:
                best_match_link = link_elem['href']
                if not best_match_link.startswith('http'):
                    # Handle relative URLs
                    best_match_link = f"https://www.ewg.org{best_match_link}"
                break
    
    if best_match and best_match_link:
        print(f"Best match found: {best_match}")
        print(f"Link: {best_match_link}")
        
        # Navigate to the product page
        product_response = requests.get(best_match_link, headers=headers)
        print(f"Product page status code: {product_response.status_code}")
        
        if product_response.status_code == 200:
            product_soup = BeautifulSoup(product_response.text, 'html.parser')
        
        # Extract hazard score
        score_img = product_soup.select_one('.product-score img')
        if score_img and 'src' in score_img.attrs:
            # Extract score from the URL parameters
            img_src = score_img['src']
            
            # Parse the score and score_min from the URL
            import re
            score_match = re.search(r'score=(\d+)', img_src)
            score_min_match = re.search(r'score_min=(\d+)', img_src)
            
            score = score_match.group(1) if score_match else "Unknown"
            score_min = score_min_match.group(1) if score_min_match else score
            
            score_range = f"{score_min}-{score}"
            print(f"Product score range: {score_range}")
        else:
            print("Could not find score image")

        concerns_data = extract_ingredient_concerns(product_soup)

        # Also get the data level if available
        data_level = product_soup.select_one('.data-level').text.split()[1]
        print(f"Data availability level: {data_level}") if data_level else print("Data avaialability information not found")
            
            
    else:
        print(f"No exact match found for '{search_term}'. Displaying first result instead:")
        if products:
            first_product = products[0]
            name_elem = first_product.select_one('.product-name')
            link_elem = first_product.select_one('a')
            
            name = name_elem.text.strip() if name_elem else "Name not found"
            link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
            
            if not link.startswith('http'):
                link = f"https://www.ewg.org{link}"
                
            print(f"Product: {name}")
            print(f"Link: {link}")
            
            # You could add code here to navigate to this first result if desired
        else:
            print("No products found in the search results.")
else:
    print(f"Failed to access the search results: {response.status_code}")



# Example usage:
#concerns_data = extract_ingredient_concerns(product_soup)

"""# Pretty print the results
import json
print(json.dumps(concerns_data, indent=2))

# Or print in a more readable format
for section, rows in concerns_data.items():
    print(f"\n=== {section} ===")
    
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        # Print the first row's keys as column headers
        headers = list(rows[0].keys())
        for header in headers:
            print(f"{header:<40}", end="")
        print("\n" + "-" * (40 * len(headers)))
        
        # Print each row
        for row in rows:
            for header in headers:
                value = row.get(header, "")
                print(f"{value:<40}", end="")
            print()
    else:
        print(rows)
"""