import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
import json
import time
import random
import re

# Define a list of proxy addresses
proxies = [
    'http://51.79.50.31:9300',
    'http://143.198.197.126:1080',
    'http://167.172.221.249:8080',
    'http://157.245.42.93:8080',
    'http://104.248.153.94:8080',
    'http://206.189.191.15:8080',
    'http://138.68.240.218:8080',
    'http://45.77.247.249:8080',
    'http://161.35.56.238:80',
    'http://51.158.68.68:8811',
    'http://198.211.96.109:8080',
    'http://165.22.254.100:8080',
    'http://192.241.223.120:8080',
    'http://185.220.101.101:8080',
    'http://185.220.101.102:8080',
    'http://185.107.232.253:8080',
    'http://193.37.100.184:8080',
    'http://185.244.171.22:8080',
    'http://51.79.50.31:9300',
    'http://45.32.56.157:8080',
    'http://5.189.133.231:80',
    'http://137.184.46.150:3128',
    'http://164.52.201.18:8080',
    'http://198.211.113.186:8080',
    'http://157.245.56.94:8080',
    'http://45.77.78.129:8080',
    'http://37.187.95.171:8080',
    'http://46.101.34.200:8080',
    'http://104.248.56.74:8080',
    'http://165.227.73.80:8080',
    'http://161.35.49.121:80',
    
]

# Configure logging
logging.basicConfig(filename='scraping_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load the links from an Excel file
kapiva_links_df = pd.read_excel()

# Clean function to remove illegal characters from Excel output
def clean_text(text):
    # Remove any HTML tags and control characters
    clean = re.sub(r'<.*?>', '', str(text))  # Remove HTML tags
    return ''.join(c for c in clean if ord(c) >= 32)  # Remove control characters

# Extract product images from soup
def extract_product_images(soup):
    image_tags = soup.find_all('img', class_='Thumbnail__thumbnail-image-new___3rsF_')
    image_urls = [img['src'] for img in image_tags]
    return ' | '.join(image_urls)

# Scrape product data from a given link
def scrape_product_data(link):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        }
        proxy = {'http': random.choice(proxies)}
        response = requests.get(link, headers=headers, proxies=proxy)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Get product description
        product_description_div = soup.find('div', class_='ProductDescription__description-content___A_qCZ')
        product_description_html = product_description_div.decode_contents() if product_description_div else "Description not found"

        # Get product highlights
        product_highlight_div = soup.find('div', class_='ProductHighlights__highlights-text___dc-WQ')
        product_highlights = product_highlight_div.decode_contents() if product_highlight_div else "No highlights found"

        # Get manufacturer information
        compliance_info_div = soup.find('div', class_='OtcPage__compliance-info-wrapper___1edqX')
        if compliance_info_div:
            manufacturer_name = compliance_info_div.find('div').get_text(strip=True).replace('Name:', '').strip()
            address = compliance_info_div.find_all('div')[1].get_text(strip=True).replace('Address:', '').strip()
        else:
            manufacturer_name, address = "Manufacturer info not found", "Address info not found"

        # Get price
        price_span = soup.find('span', class_='DiscountDetails__discount-price___Mdcwo')
        price = ''.join(filter(str.isdigit, price_span.get_text(strip=True))) if price_span else "Price not found"

        # Get pack size and MRP
        pack_size_mrp_list = []
        variant_divs = soup.find_all('div', class_='OtcVariantsItem__container___2ldJL')
        variant_links = soup.find_all('a', class_='OtcVariantsItem__container___2ldJL')

        def extract_size_and_mrp(tag):
            size_text = tag.find('div', class_='OtcVariantsItem__variant-text___1Grsz').get_text(strip=True)
            mrp_tag = tag.find('div', class_='OtcVariantsItem__variant-price___3RfP5')
            mrp_text = mrp_tag.get_text(strip=True).replace('₹', '').strip() if mrp_tag else ''
            return {"size": size_text, "mrp": mrp_text}

        for div in variant_divs:
            pack_size_mrp_list.append(extract_size_and_mrp(div))
        for a in variant_links:
            pack_size_mrp_list.append(extract_size_and_mrp(a))

        # Get images
        product_images = extract_product_images(soup)

        # Log success
        logging.info(f"Successfully scraped: {link}")
        time.sleep(1)  # Random sleep to avoid being blocked
        return product_description_html, product_highlights, manufacturer_name, address, price, pack_size_mrp_list, product_images

    except requests.RequestException as e:
        logging.error(f"Failed to scrape {link}: {e}")
        return "Error", "Error", "Error", "Price not found", [], "Images not found"

# Output file to store scraped data
output_file = "ForestEssentail2.xlsx"

# Process each link in the DataFrame
if os.path.exists(output_file):
    existing_data = pd.read_excel(output_file)
    print("This is to check")
    for index, row in kapiva_links_df.iterrows():
        link = row['Link']
        product_description, product_highlight, manufacturer_name, address, price, pack_size_mrp_list, product_images = scrape_product_data(link)
        
        # Add data to existing DataFrame, cleaning each field
        existing_data.at[index, 'Product Description HTML'] = clean_text(product_description)
        existing_data.at[index, 'Product Highlights'] = clean_text(product_highlight)
        existing_data.at[index, 'Manufacturer Name'] = clean_text(manufacturer_name)
        existing_data.at[index, 'Address'] = clean_text(address)
        existing_data.at[index, 'Price'] = clean_text(price)
        existing_data.at[index, 'Images'] = clean_text(product_images)
        existing_data.at[index, 'Pack Size MRP'] = json.dumps(pack_size_mrp_list, indent=4)

else:
    kapiva_links_df[['Product Description HTML', 'Product Highlights', 'Manufacturer Name', 'Address', 'Price', 'Pack Size MRP', 'Images']] = kapiva_links_df['Link'].apply(
        lambda link: pd.Series(scrape_product_data(link)))
    existing_data = kapiva_links_df.drop(columns=['Link'])

# Save the cleaned and updated data to an Excel file
existing_data.to_excel(output_file, index=False)
print(f"Scraping completed and data saved to '{output_file}'")