import requests
from bs4 import BeautifulSoup
import re
import json
import time
import sys

print("Python path:", sys.executable)
print("Python version:", sys.version)

# Then try to import
try:
    import Levenshtein

    print("Levenshtein import successful")
except ImportError as e:
    print(f"Import error: {e}")
from Levenshtein import distance


class EWGSkindeepAPI:
    """Class for interacting with the EWG Skindeep database"""

    def __init__(self, rate_limit=1):
        """
        Initialize the API client

        Args:
            rate_limit (float): Seconds to wait between requests to avoid rate limiting
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0

    def get_headers(self):
        """Return headers to mimic a browser for requests."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.ewg.org/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    def _make_request(self, url):
        """
        Make a request with rate limiting

        Args:
            url (str): URL to request

        Returns:
            requests.Response: The response object
        """
        # Apply rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        # Make the request
        response = requests.get(url, headers=self.get_headers())
        self.last_request_time = time.time()

        return response

    def search_ingredient(self, search_term):
        """
        Search for an ingredient on EWG Skindeep.

        Args:
            search_term (str): The ingredient to search for

        Returns:
            tuple: (status_code, BeautifulSoup object of search results)
        """
        # Specifically search for ingredients by adding the search_type parameter
        search_url = f"http://www.ewg.org/skindeep/search/?search={search_term}&search_type=ingredients"
        response = self._make_request(search_url)

        if response.status_code == 200:
            return response.status_code, BeautifulSoup(response.text, "html.parser")
        else:
            return response.status_code, None

    def find_matches(self, soup, search_term, exact_match_only=False):
        """
        Find the ingredient(s) that match the search term.

        Args:
            soup (BeautifulSoup): The soup object of the search results
            search_term (str): The search term
            exact_match_only (bool): If True, only return exact matches

        Returns:
            tuple: (best_match_name, best_match_url, all_matches)
        """
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

    def get_ingredient_page(self, url):
        """
        Get the ingredient page content.

        Args:
            url (str): The URL of the ingredient page

        Returns:
            tuple: (status_code, BeautifulSoup object of ingredient page)
        """
        response = self._make_request(url)

        if response.status_code == 200:
            return response.status_code, BeautifulSoup(response.text, "html.parser")
        else:
            return response.status_code, None

    def extract_score(self, product_soup):
        """
        Extract the hazard score from the ingredient page.

        Args:
            product_soup (BeautifulSoup): The soup object of the ingredient page

        Returns:
            tuple: (score_range, data_level) or (None, None) if not found
        """
        score_range = None
        data_level = None

        # Extract hazard score
        score_img = product_soup.select_one(".product-score img")
        if score_img and "src" in score_img.attrs:
            img_src = score_img["src"]

            score_match = re.search(r"score=(\d+)", img_src)
            score_min_match = re.search(r"score_min=(\d+)", img_src)

            score = score_match.group(1) if score_match else "Unknown"
            score_min = score_min_match.group(1) if score_min_match else score

            score_range = f"{score_min}-{score}"

        # Get data level
        data_level_elem = product_soup.select_one(".data-level")
        if data_level_elem:
            data_level = data_level_elem.text.split()
            if len(data_level) > 1:
                data_level = data_level[1]
            else:
                data_level = data_level_elem.text.strip()

        return score_range, data_level

    def extract_concerns(self, product_soup):
        """
        Extract all ingredient concerns from collapsible blocks.

        Args:
            product_soup (BeautifulSoup): The BeautifulSoup object of the page

        Returns:
            list: List of dictionaries containing concern information
        """
        all_concerns = []

        # Find the main ingredient concerns wrapper
        concerns_wrapper = product_soup.select_one(".ingredient-concerns-inner-wrapper")
        if not concerns_wrapper:
            return []

        # Find all collapsible blocks within the concerns sources wrapper
        collapsable_blocks = concerns_wrapper.select(
            ".concerns-sources-wrapper .collapsable-block"
        )

        if not collapsable_blocks:
            return []

        # Extract information from each block (skip the first block which is usually a header)
        for i, block in enumerate(collapsable_blocks):
            if i == 0:  # Skip the first block if it's a header
                continue

            # Find the table within the concerns block
            concern_table = block.select_one(".chemical-concern-table")

            if concern_table:
                # Get all rows in the table body
                rows = concern_table.select("tbody tr")

                for row in rows:
                    # Get the concern and reference cells
                    cells = row.select("td")
                    if len(cells) >= 2:
                        concern = cells[0].text.strip()
                        reference = cells[1].text.strip()
                        all_concerns.append(
                            {"concern": concern, "reference": reference}
                        )

        return all_concerns

    def get_ingredient_data(self, search_term, exact_match_only=False):
        """
        Get complete data for an ingredient.

        Args:
            search_term (str): The ingredient to search for
            exact_match_only (bool): If True, only consider exact matches

        Returns:
            dict: A dictionary containing all the ingredient information
        """
        result = {
            "search_term": search_term,
            "ingredient_found": False,
            "ingredient_info": {},
            "all_matches": [],
        }

        # Search for the ingredient
        status_code, search_soup = self.search_ingredient(search_term)

        if status_code != 200 or search_soup is None:
            result["error"] = f"Failed to access search results: {status_code}"
            return result

        # Find the best match
        ingredient_name, ingredient_url, all_matches = self.find_matches(
            search_soup, search_term, exact_match_only
        )

        # Store all matches in the result for reference
        result["all_matches"] = all_matches

        if not ingredient_name or not ingredient_url:
            result["error"] = f"No suitable matches found for '{search_term}'"
            return result

        result["ingredient_found"] = True
        result["ingredient_info"]["name"] = ingredient_name
        result["ingredient_info"]["url"] = ingredient_url

        # Check if we got an exact match
        ratio = Levenshtein.ratio(search_term, ingredient_name)
        if ratio > 0.9:
            result["exact_match"] = True
        else:
            result["exact_match"] = False

        # Get the ingredient page
        status_code, ingredient_soup = self.get_ingredient_page(ingredient_url)

        if status_code != 200 or ingredient_soup is None:
            result["error"] = f"Failed to access ingredient page: {status_code}"
            return result

        # Extract score and data level
        score_range, data_level = self.extract_score(ingredient_soup)

        if score_range:
            result["ingredient_info"]["score_range"] = score_range

        if data_level:
            result["ingredient_info"]["data_level"] = data_level

        # Extract concerns
        concerns = self.extract_concerns(ingredient_soup)

        if concerns:
            result["ingredient_info"]["concerns"] = concerns

        return result

    def analyze_ingredient(self, ingredient):
        """
        Analyze a single ingredient

        Args:
            ingredient (str): The ingredient to analyze

        Returns:
            dict: Analysis result
        """
        # First try exact match
        result = self.get_ingredient_data(ingredient, exact_match_only=True)

        if result["ingredient_found"] and result.get("exact_match", False):
            result["match_type"] = "exact"
            return result

        # If no exact match, return the result with available matches
        result["match_type"] = "no_exact_match"
        return result


class IngredientAnalyzer:
    """Class for analyzing and correcting ingredient lists from OCR"""

    def __init__(self, ewg_api=None):
        """
        Initialize the analyzer

        Args:
            ewg_api (EWGSkindeepAPI): API client instance
        """
        self.ewg_api = ewg_api or EWGSkindeepAPI()

    def analyze_ingredient(self, ingredient):
        """
        Analyze a single ingredient

        Args:
            ingredient (str): The ingredient to analyze

        Returns:
            dict: Analysis result
        """
        # First try exact match
        result = self.ewg_api.get_ingredient_data(ingredient, exact_match_only=True)

        if result["ingredient_found"] and result.get("exact_match", False):
            result["match_type"] = "exact"
            return result

        # If no exact match, return the result with available matches
        result["match_type"] = "no_exact_match"
        return result

    def smart_analyze(self, ingredient):
        """
        Smartly analyze an ingredient by trying various combinations

        Args:
            ingredient (str): The ingredient to analyze

        Returns:
            dict: Best analysis result
        """
        # First try the original ingredient
        result = self.analyze_ingredient(ingredient)

        if result["ingredient_found"] and result.get("exact_match", False):
            return {
                "original": ingredient,
                "corrected": ingredient,
                "match_type": "exact",
                "data": result,
            }

        # Try to split the ingredient and check each part
        words = re.split(r"[\s,/\-]+", ingredient)
        words = [
            w
            for w in words
            if len(w) > 2 and w.lower() not in ["and", "with", "plus", "the"]
        ]

        # If we only have one word, skip to partial match
        if len(words) > 1:
            found_matches = []

            for word in words:
                result = self.analyze_ingredient(word)

                if result["ingredient_found"] and result.get("exact_match", False):
                    found_matches.append(
                        {
                            "original": word,
                            "corrected": word,
                            "match_type": "split_exact",
                            "data": result,
                        }
                    )

            if found_matches:
                return found_matches[0]  # Return the first match for now

        # If we didn't find any exact matches from splits, try a fuzzy match on the original
        result = self.ewg_api.get_ingredient_data(ingredient, exact_match_only=False)

        if result["ingredient_found"]:
            return {
                "original": ingredient,
                "corrected": result["ingredient_info"]["name"],
                "match_type": "fuzzy",
                "data": result,
            }

        # No match found
        return {
            "original": ingredient,
            "corrected": None,
            "match_type": "no_match",
            "data": None,
        }

    def smart_analyze_list(self, ingredient_list):
        """
        Intelligently analyze a list of ingredients

        Args:
            ingredient_list (list): List of ingredients

        Returns:
            list: List of analysis results
        """

        results = []
        unmatched = []

        # Phase 1: Try direct matches first
        print("PHASE 1: Testing direct matches...")
        for ingredient in ingredient_list:
            result = self.smart_analyze(ingredient)

            if result["match_type"] in ["exact", "fuzzy"]:
                print(f"✓ Found match for: {ingredient}")
                results.append(result)
            else:
                print(f"✗ No match for: {ingredient}")
                unmatched.append(ingredient)

        # Phase 2: Try combinations of adjacent unmatched ingredients
        print("\nPHASE 2: Testing combinations of adjacent unmatched ingredients...")
        if len(unmatched) >= 2:
            i = 0
            while i < len(unmatched) - 1:
                # Try combining with the next ingredient
                combined = unmatched[i] + " " + unmatched[i + 1]
                combined_result = self.analyze_ingredient(combined)

                if combined_result["ingredient_found"] and combined_result.get(
                    "exact_match", False
                ):
                    print(f"✓ Found exact match for combined: {combined}")
                    results.append(
                        {
                            "original": f"{unmatched[i]} + {unmatched[i+1]}",
                            "corrected": combined,
                            "match_type": "combined_exact",
                            "data": combined_result,
                        }
                    )
                    # Skip both ingredients as they've been combined
                    i += 2
                else:
                    # Also try with a comma
                    combined_comma = unmatched[i] + ", " + unmatched[i + 1]
                    comma_result = self.analyze_ingredient(combined_comma)

                    if comma_result["ingredient_found"] and comma_result.get(
                        "exact_match", False
                    ):
                        print(
                            f"✓ Found exact match for combined with comma: {combined_comma}"
                        )
                        results.append(
                            {
                                "original": f"{unmatched[i]} + {unmatched[i+1]}",
                                "corrected": combined_comma,
                                "match_type": "combined_comma_exact",
                                "data": comma_result,
                            }
                        )
                        i += 2
                    else:
                        # Only increment by 1 to try next pair
                        i += 1

            # Add any remaining unmatched ingredients with their best fuzzy matches
            while i < len(unmatched):
                fuzzy_result = self.ewg_api.get_ingredient_data(
                    unmatched[i], exact_match_only=False
                )

                if fuzzy_result["ingredient_found"]:
                    print(
                        f"~ Found closest match for: {unmatched[i]} -> {fuzzy_result['ingredient_info']['name']}"
                    )
                    results.append(
                        {
                            "original": unmatched[i],
                            "corrected": fuzzy_result["ingredient_info"]["name"],
                            "match_type": "final_fuzzy",
                            "data": fuzzy_result,
                        }
                    )
                else:
                    print(f"✗ Could not find any match for: {unmatched[i]}")
                    results.append(
                        {
                            "original": unmatched[i],
                            "corrected": None,
                            "match_type": "no_match",
                            "data": None,
                        }
                    )
                i += 1

        return results


def pretty_print_ingredient(result):
    """
    Pretty print the results for a single ingredient.

    Args:
        result (dict): The result dictionary from analyze_ingredient
    """
    if not result or result.get("match_type") == "no_match":
        print("✗ No match found")
        return

    data = result.get("data", {})

    # For split matches, we might have multiple results
    if isinstance(result, list):
        print("Multiple matches found from splitting:")
        for r in result:
            print(f"- {r['corrected']} (split from original)")
        return

    original = result.get("original", "Unknown")
    corrected = result.get("corrected", "Unknown")
    match_type = result.get("match_type", "Unknown")

    print(f"Original: {original}")

    if original != corrected and corrected:
        print(f"Corrected: {corrected}")

    print(f"Match type: {match_type}")

    if data and "ingredient_info" in data:
        info = data["ingredient_info"]

        if "score_range" in info:
            print(f"Score Range: {info['score_range']}")

        if "data_level" in info:
            print(f"Data Level: {info['data_level']}")

        if "concerns" in info and info["concerns"]:
            print("\nConcerns:")
            for concern in info["concerns"]:
                print(f"- {concern['concern']} [{concern['reference']}]")


def print_correction_summary(analysis_results):
    """
    Print a summary of ingredient corrections.

    Args:
        analysis_results (list): List of analysis results from smart_analyze_list
    """
    print("\n=== CORRECTION SUMMARY ===")

    for item in analysis_results:
        if not item:
            continue

        if item["match_type"] == "exact":
            print(f"✓ {item['original']} (confirmed)")
        elif item["corrected"]:
            print(f"✓ {item['original']} → {item['corrected']} ({item['match_type']})")
        else:
            print(f"✗ {item['original']} (no match found)")


def save_to_json(analysis_results, filename="ingredient_analysis.json"):
    """
    Save analysis results to a JSON file.

    Args:
        analysis_results (list): List of analysis results
        filename (str): Output filename
    """
    # Clean up results to remove circular references
    clean_results = []

    for result in analysis_results:
        if not result:
            continue

        # Create a clean copy without circular references
        clean_result = {
            "original": result.get("original"),
            "corrected": result.get("corrected"),
            "match_type": result.get("match_type"),
        }

        # Add ingredient data if available
        if "data" in result and result["data"]:
            data = result["data"]
            if "ingredient_info" in data:
                clean_result["info"] = data["ingredient_info"]

        clean_results.append(clean_result)

    # Save to file
    with open(filename, "w") as f:
        json.dump(clean_results, f, indent=2)

    print(f"Results saved to {filename}")


# Example usage
if __name__ == "__main__":
    # Create API and analyzer instances
    ewg_api = EWGSkindeepAPI(rate_limit=1)  # 1 second between requests
    analyzer = IngredientAnalyzer(ewg_api)

    # Example ingredient list (from OCR)
    from image2text import test_image
    import glob

    # search_term = "Glycerin"
    folder = glob.glob("product_images/*")
    for image in folder:
        ingredient_list, best_method, _ = test_image(image)
        print(best_method)
        # Analyze ingredients
        analysis_results = analyzer.smart_analyze_list(
            ingredient_list[best_method]["ingredients"]
        )

    # Print summary
    print_correction_summary(analysis_results)

    # Save results to JSON

    # pretty_print_ingredient(analysis_results)
    save_to_json(analysis_results)
