import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# List of base URLs to scrape
base_urls = [
   "https://www.1mg.com/marketer/arya-vaidya-sala-kottakkal-75834",
    # Add more URLs as needed
]

# Headers to simulate a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
}

# Function to scrape products from a URL
def scrape_url(base_url):
    url_products = []
    page_number = 1
    
    print(f"\nStarting to scrape: {base_url}")
    
    while True:
        # Construct URL with pagination
        url = f"{base_url}?pageNumber={page_number}"
        print(f"Scraping page: {page_number}")

        # Fetch the page content with headers
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve page {page_number}. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all product links inside the main container
        product_links = soup.select("#srchRslt .col-sm-3.col-xs-6 a")

        # If no products found, stop pagination
        if not product_links:
            print(f"No more products found on page {page_number}. Moving to next URL.")
            break

        # Extract product names and complete links
        for link in product_links:
            product_name = link.get_text(strip=True)
            product_url = "https://www.1mg.com" + link["href"]
            url_products.append({
                "Product Name": product_name, 
                "Link": product_url,
                "Source": base_url
            })
            
        print(f"Found {len(product_links)} products on page {page_number}")

        # Move to the next page
        page_number += 1
        
        # Add a small delay to be respectful to the server
        time.sleep(1)
    
    print(f"Total products from {base_url}: {len(url_products)}")
    return url_products

# Storage for all product data
all_products = []

# Loop through each base URL
for base_url in base_urls:
    # Get products from this URL
    products = scrape_url(base_url)
    # Add to our master list
    all_products.extend(products)

# Save all data to Excel
output_file = "all_new_kottakal.xlsx"
df = pd.DataFrame(all_products)
df.to_excel(output_file, index=False)

print(f"\nTotal products scraped: {len(all_products)}")
print(f"Data saved to '{output_file}'")
