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

def smart_ingredient_search(ingredient_list):
    """
    Intelligently search for ingredients that might be incorrectly joined or split.
    
    Args:
        ingredient_list (list): List of possible ingredients from OCR
        
    Returns:
        list: Corrected list of ingredients with matches from the database
    """
    corrected_ingredients = []
    unmatched_ingredients = []
    potential_splits = {}
    
    # Step 1: Try direct matches first
    print("PHASE 1: Testing direct matches...")
    for ingredient in ingredient_list:
        result = main(ingredient, exact_match_only=True)
        
        if result["product_found"] and result.get("exact_match", False):
            print(f"✓ Found exact match for: {ingredient}")
            corrected_ingredients.append({
                "original": ingredient,
                "corrected": ingredient,
                "match_type": "exact",
                "data": result
            })
        else:
            print(f"✗ No exact match for: {ingredient}")
            unmatched_ingredients.append(ingredient)
            
            # Store potential alternatives for reference
            if "all_products" in result and result["all_products"]:
                potential_splits[ingredient] = result["all_products"]
    
    # Step 2: Try splitting unmatched ingredients
    print("\nPHASE 2: Testing word splits for unmatched ingredients...")
    still_unmatched = []
    
    for ingredient in unmatched_ingredients:
        # Split by spaces and other common separators
        words = re.split(r'[\s,/\-]+', ingredient)
        
        # Filter out common words that aren't likely to be ingredients
        words = [w for w in words if len(w) > 2 and w.lower() not in ['and', 'with', 'plus', 'the']]
        
        if len(words) <= 1:
            still_unmatched.append(ingredient)
            continue
            
        found_matches = []
        
        for word in words:
            result = main(word, exact_match_only=True)
            
            if result["product_found"] and result.get("exact_match", False):
                print(f"✓ Found exact match for split word: {word} (from {ingredient})")
                found_matches.append({
                    "original": word,
                    "corrected": word,
                    "match_type": "split_exact",
                    "data": result
                })
            
        if found_matches:
            corrected_ingredients.extend(found_matches)
        else:
            still_unmatched.append(ingredient)
    
    # Step 3: Try combining adjacent unmatched ingredients
    print("\nPHASE 3: Testing combinations of adjacent unmatched ingredients...")
    if len(still_unmatched) >= 2:
        i = 0
        while i < len(still_unmatched) - 1:
            # Try combining with the next ingredient
            combined = still_unmatched[i] + " " + still_unmatched[i+1]
            result = main(combined, exact_match_only=True)
            
            if result["product_found"] and result.get("exact_match", False):
                print(f"✓ Found exact match for combined: {combined}")
                corrected_ingredients.append({
                    "original": f"{still_unmatched[i]} + {still_unmatched[i+1]}",
                    "corrected": combined,
                    "match_type": "combined_exact",
                    "data": result
                })
                # Skip both ingredients as they've been combined
                i += 2
            else:
                # Also try with a comma
                combined_comma = still_unmatched[i] + ", " + still_unmatched[i+1]
                result = main(combined_comma, exact_match_only=True)
                
                if result["product_found"] and result.get("exact_match", False):
                    print(f"✓ Found exact match for combined with comma: {combined_comma}")
                    corrected_ingredients.append({
                        "original": f"{still_unmatched[i]} + {still_unmatched[i+1]}",
                        "corrected": combined_comma,
                        "match_type": "combined_comma_exact",
                        "data": result
                    })
                    i += 2
                else:
                    # Only increment by 1 to try next pair
                    i += 1
        
        # Don't forget the last ingredient if we didn't combine it
        if i == len(still_unmatched) - 1:
            still_unmatched_final = [still_unmatched[i]]
        else:
            still_unmatched_final = []
    else:
        still_unmatched_final = still_unmatched
    
    # Final step: Try a fuzzy search for any remaining unmatched ingredients
    print("\nPHASE 4: Performing fuzzy search for remaining items...")
    for ingredient in still_unmatched_final:
        # Get all results for the ingredient
        result = main(ingredient, exact_match_only=False)
        
        if result["product_found"]:
            print(f"~ Found closest match for: {ingredient} -> {result['product_info']['name']}")
            corrected_ingredients.append({
                "original": ingredient,
                "corrected": result["product_info"]["name"],
                "match_type": "fuzzy",
                "data": result
            })
        else:
            print(f"✗ Could not find any match for: {ingredient}")
            # Add as is with no match
            corrected_ingredients.append({
                "original": ingredient,
                "corrected": None,
                "match_type": "no_match",
                "data": None
            })
    
    return corrected_ingredients


def search_product(search_term):
    """
    Search for a product on EWG Skindeep.
    
    Args:
        search_term (str): The product to search for
        
    Returns:
        tuple: (status_code, BeautifulSoup object of search results)
    """
    search_url = f"http://www.ewg.org/skindeep/search/?search={search_term}&search_type=ingredients"
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

def main(search_term, exact_match_only=False):
    """
    Main function to search for a product and extract its information.
    
    Args:
        search_term (str): The product to search for
        exact_match_only (bool): If True, only consider exact matches
        
    Returns:
        dict: A dictionary containing all the product information
    """
    result = {
        "search_term": search_term,
        "product_found": False,
        "product_info": {},
        "all_products": []
    }
    
    # Search for the product
    status_code, search_soup = search_product(search_term)
    
    if status_code != 200 or search_soup is None:
        result["error"] = f"Failed to access search results: {status_code}"
        return result
    
    # Find the best match
    product_name, product_url, all_products = find_best_match(search_soup, search_term, exact_match_only)
    
    # Store all products in the result for reference
    result["all_products"] = all_products
    
    if not product_name or not product_url:
        result["error"] = f"No suitable products found for '{search_term}'"
        return result
    
    result["product_found"] = True
    result["product_info"]["name"] = product_name
    result["product_info"]["url"] = product_url
    
    # Check if we got an exact match
    result["exact_match"] = search_term.lower() == product_name.lower()
    
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
        
        # If we have products but no exact match, show them
        if "all_products" in result and result["all_products"]:
            print(f"\nAvailable products for '{result['search_term']}':")
            for i, product in enumerate(result["all_products"], 1):
                print(f"{i}. {product['name']}")
            print("\nConsider searching for one of these specific products instead.")
        
        return
    
    print(f"\n=== RESULTS FOR: {result['search_term']} ===\n")
    
    if not result["product_found"]:
        print("No product found.")
        return
    
    info = result["product_info"]
    
    if "exact_match" in result:
        match_type = "EXACT MATCH" if result["exact_match"] else "CLOSEST MATCH (not exact)"
        print(f"Match Type: {match_type}")
    
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

def batch_process_ingredients(ingredient_list, exact_match_only=False):
    """
    Process a list of ingredients and collect results.
    
    Args:
        ingredient_list (list): List of ingredients to search for
        exact_match_only (bool): If True, only consider exact matches
        
    Returns:
        dict: Dictionary with ingredients as keys and result dictionaries as values
    """
    results = {}
    
    for ingredient in ingredient_list:
        print(f"\nProcessing: {ingredient}")
        result = main(ingredient, exact_match_only)
        results[ingredient] = result
        pretty_print_results(result)
    
    return results


from img2txt5 import clean_ingredient_list, extract_txt

if __name__ == "__main__":
    #search_term = "Glycerin"
    ingredient_list = extract_txt("product_label.jpg")
    n = 1
    for ingredient in ingredient_list:

        results = smart_ingredient_search(ingredient_list)
        #results = main(ingredient)
        print(f"#######{n}#######")
        pretty_print_results(results)
        print(f"#######{n}#######")
        n += 1


# Optionally save results to a JSON file
# with open(f"{search_term.replace('/', '_')}_results.json", 'w') as f:
#     json.dump(results, f, indent=2)
