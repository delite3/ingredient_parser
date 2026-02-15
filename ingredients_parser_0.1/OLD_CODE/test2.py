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
url = f"http://www.ewg.org/skindeep/search/?search={search_term}"

response = requests.get(url, headers=headers)
print(f"Status code: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.select('.product-tile')
    
    for product in products:
        name_elem = product.select_one('.product-name')
        score_elem = product.select_one('.product-score')
        
        name = name_elem.text.strip() if name_elem else "Name not found"
        score = score_elem.text.strip() if score_elem else "Score not found"
        
        if name.lower() == search_term.lower():
            print(f"Product: {name} | Score: {score}")
else:
    print(f"Failed to access the website: {response.status_code}")

    