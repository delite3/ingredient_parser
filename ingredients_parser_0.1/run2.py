import requests
from bs4 import BeautifulSoup
import re
import json

from img2txt5 import extract_txt


def search_ingredient(search_term):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.ewg.org/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    search_url = f"http://www.ewg.org/skindeep/search/?search={search_term}&search_type=ingredients"

    response = requests.get(search_url, headers=header)
    search_soup = (
        BeautifulSoup(response.text, "html.parser")
        if response.status_code == 200
        else None
    )
    return search_soup, response.status_code


def find_matches(soup, search_term, exact_match_only=False):
    products = soup.select(".product-tile")
    all_matches = []

    best_match = None
    best_match_link = None

    # Normalize the search term for better matching
    search_term_normalized = search_term.lower()

    # Collect all products for potential display
    for product in products:
        name_elem = product.select_one(".product-name")
        if name_elem:
            product_name = name_elem.text.strip()
            link_elem = product.select_one("a")
            product_link = None
            if link_elem and "href" in link_elem.attrs:
                product_link = link_elem["href"]
                if not product_link.startswith("http"):
                    product_link = f"https://www.ewg.org{product_link}"

            all_matches.append({"name": product_name, "url": product_link})

            # Check for exact or partial match
            product_name_normalized = product_name.lower()

            # First priority: exact match
            if search_term_normalized == product_name_normalized:
                return product_name, product_link, all_matches

            # Second priority: search term is contained in product name
            if search_term_normalized in product_name_normalized and not best_match:
                best_match = product_name
                best_match_link = product_link

    # If we only want exact matches and haven't found one, return None
    if exact_match_only:
        return None, None, all_matches

    # If we have a partial match, return it
    if best_match:
        return best_match, best_match_link, all_matches

    # If no match at all but we have products, return the first one
    if all_matches:
        return all_matches[0]["name"], all_matches[0]["url"], all_matches

    return None, None, all_matches


if __name__ == "__main__":

    ingredient_list = extract_txt("product_images/product_label1.jpg")

    # first_ing = ingredient_list.pop(0)
    for ingredient in ingredient_list:

        search_soup, response = search_ingredient(ingredient)
        best_match, best_match_link, all_matches = find_matches(
            search_soup, ingredient, exact_match_only=False
        )

        # 1 check if first ingredient has a good enough match.
        ## if so exit loop and move onto next ingredient
        ## else try combining with next word
        print()
