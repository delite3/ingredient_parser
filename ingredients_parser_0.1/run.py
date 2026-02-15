from utils import search_product, find_best_match, main, pretty_print_results, smart_ingredient_search
from img2txt5 import clean_ingredient_list, extract_txt

if __name__ == "__main__":
    #search_term = "Glycerin"
    ingredient_list = extract_txt("product_label.jpg")
    n = 1
    for ingredient in ingredient_list:

        reuslts = smart_ingredient_search(ingredient_list)
        #results = main(ingredient)
        print(f"#######{n}#######")
        pretty_print_results(results)
        print(f"#######{n}#######")
        n += 1


























# Optionally save results to a JSON file
# with open(f"{search_term.replace('/', '_')}_results.json", 'w') as f:
#     json.dump(results, f, indent=2)


# 1. find-search-term-ingredients: search the term and parse through the best matches to see if each one is an ingedient or not.
# 2. find-perfect-matches

        """
        _, search_soup = search_product(ingredient)
        best_match, best_match_link, all_products = find_best_match(search_soup, ingredient)
        
        if best_match == None:
            temp_ingredient_list = ingredient.split()
            possible_ingredient_list = [] 

            for temp_ingredient in temp_ingredient_list:
                _, search_soup = search_product(ingredient)
                best_match, best_match_link, all_products = find_best_match(search_soup, ingredient)

                if best_match is not None and (best_match.lower() == temp_ingredient.lower()):
                    possible_ingredient_list.append(temp_ingredient)
            
            if possible_ingredient_list == []:
                temp_ingredient1 = temp_ingredient_list.pop(0)
                for temp_ingredient2 in temp_ingredient_list:
                    temp_ingredient1 + temp_ingredient2


        if best_match.lower() != ingredient.lower():
            continue
        """