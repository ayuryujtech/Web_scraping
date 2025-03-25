import requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL
base_url = "https://www.1mg.com/marketer/vital-care-pvt.-ltd-74847"

# Storage for product data
products = []

# Pagination loopimport requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL
base_url = "https://www.1mg.com/marketer/vital-care-pvt.-ltd-74847"

# Headers to simulate a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
}

# Storage for product data
products = []

# Pagination loop
page_number = 1
while True:
    # Construct URL with pagination
    url = f"{base_url}?pageNumber={page_number}"
    print(f"Scraping page: {page_number}")

    # Fetch the page content with headers
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve page.")
        break

    soup = BeautifulSoup(response.content, "html.parser")

    # Find all product links inside the main container
    product_links = soup.select("#srchRslt .col-sm-3.col-xs-6 a")

    # If no products found, stop pagination
    if not product_links:
        print("No more products found. Stopping.")
        break

    # Extract product names and complete links
    for link in product_links:
        product_name = link.get_text(strip=True)
        product_url = "https://www.1mg.com" + link["href"]
        products.append({"Product Name": product_name, "Link": product_url})

    # Move to the next page
    page_number += 1

# Save data to Excel
df = pd.DataFrame(products)
df.to_excel("vital_care_products.xlsx", index=False)

print("✅ Data saved to 'vital_care_products.xlsx'")

page_number = 1
while True:
    # Construct URL with pagination
    url = f"{base_url}?pageNumber={page_number}"
    print(f"Scraping page: {page_number}")

    # Fetch the page content
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve page.")
        break

    soup = BeautifulSoup(response.content, "html.parser")

    # Find all product links inside the main container
    product_links = soup.select("#srchRslt .col-sm-3.col-xs-6 a")

    # If no products found, stop pagination
    if not product_links:
        break

    # Extract product names and complete links
    for link in product_links:
        product_name = link.get_text(strip=True)
        product_url = "https://www.1mg.com" + link["href"]
        products.append({"Product Name": product_name, "Link": product_url})

    # Move to the next page
    page_number += 1

# Save data to Excel
df = pd.DataFrame(products)
df.to_excel("vital_care_products.xlsx", index=False)

print("✅ Data saved to 'vital_care_products.xlsx'")
