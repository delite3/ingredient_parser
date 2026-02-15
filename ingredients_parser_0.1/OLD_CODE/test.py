from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up Chrome options
chrome_options = Options()
# Uncomment the line below if you want to run headless (no browser window)
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

# Initialize the Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # Navigate to the search URL
    search_term = "glycerin"
    driver.get(f"http://www.ewg.org/skindeep/search/?search={search_term}")
    
    # Wait for the page to load
    time.sleep(5)
    
    # Extract search results
    products = driver.find_elements(By.CSS_SELECTOR, ".product-tile")
    
    for product in products:
        try:
            name = product.find_element(By.CSS_SELECTOR, ".product-name").text
            score = product.find_element(By.CSS_SELECTOR, ".product-score").text
            print(f"Product: {name} | Score: {score}")
        except:
            print("Could not extract complete information for a product")
    
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the browser
    driver.quit()


"""
import requests
from bs4 import BeautifulSoup

# URL with search query parameters
search_term = "glycerin"

url = f"http://www.ewg.org/skindeep/search/?search={search_term}"

# Send GET request
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find search results (the exact code depends on the website structure)
search_results = soup.find_all('div', class_='search-result')

# Print results
for result in search_results:
    title = result.find('h3').text
    link = result.find('a')['href']
    print(f"Title: {title}")
    print(f"Link: {link}")
    print("---")
    
"""