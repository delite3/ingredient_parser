import requests
from bs4 import BeautifulSoup
import re
import json

def get_headers():
    """Return headers to mimic a browser for requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.ewg.org/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

def search_product(search_term):
    """
    Search for a product on EWG Skindeep.
    
    Args:
        search_term (str): The product to search for
        
    Returns:
        tuple: (status_code, BeautifulSoup object of search results)
    """
    search_url = f"http://www.ewg.org/skindeep/search/?search={search_term}"
    response = requests.get(search_url, headers=get_headers())
    
    if response.status_code == 200:
        return response.status_code, BeautifulSoup(response.text, 'html.parser')
    else:
        return response.status_code, None

def find_best_match(soup, search_term, exact_match_only=False):
    """
    Find the product that best matches the search term.
    
    Args:
        soup (BeautifulSoup): The soup object of the search results
        search_term (str): The search term
        exact_match_only (bool): If True, only return exact matches
        
    Returns:
        tuple: (product_name, product_url, all_products) where all_products is a list of all products found
    """
    products = soup.select('.product-tile')
    all_products = []
    
    best_match = None
    best_match_link = None
    
    # Collect all products for potential display
    for product in products:
        name_elem = product.select_one('.product-name')
        if name_elem:
            product_name = name_elem.text.strip()
            link_elem = product.select_one('a')
            product_link = None
            if link_elem and 'href' in link_elem.attrs:
                product_link = link_elem['href']
                if not product_link.startswith('http'):
                    product_link = f"https://www.ewg.org{product_link}"
            
            all_products.append({
                "name": product_name,
                "url": product_link
            })
            
            # Check for exact match
            if search_term.lower() in product_name.lower():
                best_match = product_name
                best_match_link = product_link
                # If we found an exact match, return it immediately
                if search_term.lower() == product_name.lower():
                    return best_match, best_match_link, all_products
    
    # If we only want exact matches and haven't found one, return None
    if exact_match_only and not best_match:
        return None, None, all_products
    
    # If we have a partial match, return it
    if best_match:
        return best_match, best_match_link, all_products
    
    # If no match at all but we have products, return the first one (unless exact_match_only is True)
    if all_products and not exact_match_only:
        return all_products[0]["name"], all_products[0]["url"], all_products
    
    return None, None, all_products

def get_product_page(url):
    """
    Get the product page soup object.
    
    Args:
        url (str): The URL of the product page
        
    Returns:
        tuple: (status_code, BeautifulSoup object of product page)
    """
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        return response.status_code, BeautifulSoup(response.text, 'html.parser')
    else:
        return response.status_code, None

def extract_score(product_soup):
    """
    Extract the hazard score from the product page.
    
    Args:
        product_soup (BeautifulSoup): The soup object of the product page
        
    Returns:
        tuple: (score_range, data_level) or (None, None) if not found
    """
    score_range = None
    data_level = None
    
    # Extract hazard score
    score_img = product_soup.select_one('.product-score img')
    if score_img and 'src' in score_img.attrs:
        img_src = score_img['src']
        
        score_match = re.search(r'score=(\d+)', img_src)
        score_min_match = re.search(r'score_min=(\d+)', img_src)
        
        score = score_match.group(1) if score_match else "Unknown"
        score_min = score_min_match.group(1) if score_min_match else score
        
        score_range = f"{score_min}-{score}"
    
    # Get data level
    data_level_elem = product_soup.select_one('.data-level')
    if data_level_elem:
        data_level = data_level_elem.text.split()
        if len(data_level) > 1:
            data_level = data_level[1]
        else:
            data_level = data_level_elem.text.strip()
    
    return score_range, data_level

def extract_ingredient_concerns(product_soup):
    """
    Extract all ingredient concerns from collapsible blocks in a product page.
    
    Args:
        product_soup (BeautifulSoup): The BeautifulSoup object of the product page
        
    Returns:
        list: List of dictionaries containing concern information
    """
    all_concerns = []
    
    # Find the main ingredient concerns wrapper
    concerns_wrapper = product_soup.select_one('.ingredient-concerns-inner-wrapper')
    if not concerns_wrapper:
        return []
    
    # Find all collapsible blocks within the concerns sources wrapper
    collapsable_blocks = concerns_wrapper.select('.concerns-sources-wrapper .collapsable-block')
    
    if not collapsable_blocks:
        return []
    
    # Extract information from each block (skip the first block which is usually a header)
    for i, block in enumerate(collapsable_blocks):
        if i == 0:  # Skip the first block if it's a header
            continue

        # Find the table within the concerns block
        concern_table = block.select_one('.chemical-concern-table')
        
        if concern_table:
            # Get all rows in the table body
            rows = concern_table.select('tbody tr')
            
            for row in rows:
                # Get the concern and reference cells
                cells = row.select('td')
                if len(cells) >= 2:
                    concern = cells[0].text.strip()
                    reference = cells[1].text.strip()
                    all_concerns.append({
                        "concern": concern,
                        "reference": reference
                    })
    
    return all_concerns

def main(search_term):
    """
    Main function to search for a product and extract its information.
    
    Args:
        search_term (str): The product to search for
        
    Returns:
        dict: A dictionary containing all the product information
    """
    result = {
        "search_term": search_term,
        "product_found": False,
        "product_info": {}
    }
    
    # Search for the product
    status_code, search_soup = search_product(search_term)
    
    if status_code != 200 or search_soup is None:
        result["error"] = f"Failed to access search results: {status_code}"
        return result
    
    # Find the best match
    product_name, product_url = find_best_match(search_soup, search_term)
    
    if not product_name or not product_url:
        result["error"] = f"No products found for '{search_term}'"
        return result
    
    result["product_found"] = True
    result["product_info"]["name"] = product_name
    result["product_info"]["url"] = product_url
    
    # Get the product page
    status_code, product_soup = get_product_page(product_url)
    
    if status_code != 200 or product_soup is None:
        result["error"] = f"Failed to access product page: {status_code}"
        return result
    
    # Extract score and data level
    score_range, data_level = extract_score(product_soup)
    
    if score_range:
        result["product_info"]["score_range"] = score_range
    
    if data_level:
        result["product_info"]["data_level"] = data_level
    
    # Extract concerns
    concerns = extract_ingredient_concerns(product_soup)
    
    if concerns:
        result["product_info"]["concerns"] = concerns
    
    return result

def pretty_print_results(result):
    """
    Pretty print the results.
    
    Args:
        result (dict): The result dictionary from main()
    """
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"\n=== RESULTS FOR: {result['search_term']} ===\n")
    
    if not result["product_found"]:
        print("No product found.")
        return
    
    info = result["product_info"]
    
    print(f"Product Name: {info['name']}")
    print(f"Product URL: {info['url']}")
    
    if "score_range" in info:
        print(f"Score Range: {info['score_range']}")
    
    if "data_level" in info:
        print(f"Data Level: {info['data_level']}")
    
    if "concerns" in info and info["concerns"]:
        print("\nConcerns:")
        for concern in info["concerns"]:
            print(f"- {concern['concern']} [{concern['reference']}]")
    else:
        print("\nNo concerns found.")

# Example usage
if __name__ == "__main__":
    #search_term = "Glycerin"
    ingredient_list = ['Ingredients', 'Aqua', 'C12-15 Alkyl Benzoate', 'Alcohol Denat. Butyl Methoxydiben', 'zoylmethane']

    for ingredient in ingredient_list:

        _, search_soup = search_product(ingredient)
        best_match, best_match_link, all_products = find_best_match(search_soup, ingredient)
        if product_name != ingredient:
            continue
        results = main(ingredient)
        pretty_print_results(results)
    
    # Optionally save results to a JSON file
    # with open(f"{search_term.replace('/', '_')}_results.json", 'w') as f:
    #     json.dump(results, f, indent=2)