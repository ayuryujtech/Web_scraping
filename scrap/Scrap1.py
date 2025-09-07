import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
import json
import time
import random
import re
from datetime import datetime

# Configure main logging
logging.basicConfig(filename='scraping_log.log', level=logging.INFO,
                   format='%(asctime)s - %(message)s')

# Create a separate logger for failed URLs
failed_logger = logging.getLogger('failed_urls')
failed_logger.setLevel(logging.ERROR)
failed_handler = logging.FileHandler('failed_urls.log')
failed_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
failed_logger.addHandler(failed_handler)
failed_logger.propagate = False  # Prevent duplicate logging in main log
print('scrpt is logged')

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

# Load the links from an Excel file
kapiva_links_df = pd.read_excel("E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\vitalCare\\vital_care.xlsx")

# Clean function to remove illegal characters from Excel output
def clean_text(text):
    # Remove any HTML tags and control characters
    clean = re.sub(r'<.*?>', '', str(text))  # Remove HTML tags
    return ''.join(c for c in clean if ord(c) >= 32)  # Remove control characters

# Enhanced product images extraction function
def extract_product_images(soup):
    # Try multiple image classes to ensure we find all images
    image_classes = [
        'Thumbnail__thumbnail-image-new___3rsF_',
        'ProductImageCarousel__thumbnail-img___3xfQn',
        'style__image___Ny-Sa',
        'style__product-image___1bkgA',
        'ProductImageCarousel__image-container___cSrff img'
    ]
    
    all_image_urls = []
    
    # Try using standard classes first
    for class_name in image_classes:
        image_tags = soup.select(f'img.{class_name}')
        if not image_tags and ' ' in class_name:
            # Try CSS selector for complex patterns
            image_tags = soup.select(class_name)
            
        for img in image_tags:
            if 'src' in img.attrs:
                img_url = img['src']
                if img_url and img_url not in all_image_urls:
                    all_image_urls.append(img_url)
    
    # If no images found with classes, try main product images
    if not all_image_urls:
        # Look for product carousel or main product image
        carousel = soup.find('div', class_=lambda x: x and 'carousel' in x.lower())
        if carousel:
            for img in carousel.find_all('img'):
                if 'src' in img.attrs:
                    all_image_urls.append(img['src'])
    
    # Final fallback - find images with product in URL
    if not all_image_urls:
        all_imgs = soup.find_all('img')
        for img in all_imgs:
            if 'src' in img.attrs:
                src = img['src'].lower()
                if ('product' in src or '/prod/' in src or 'cdn' in src) and src not in all_image_urls:
                    all_image_urls.append(img['src'])
    
    # Log the results
    logging.info(f"Found {len(all_image_urls)} product images")
    if all_image_urls:
        logging.info(f"First image URL: {all_image_urls[0]}")
    else:
        logging.warning("No product images found")
        
    return ' | '.join(all_image_urls)

# Add this function after extract_product_images function
def extract_pack_details(soup):
    try:
        # Default values
        pack_qty = 1  # This is always 1 as per requirement
        content_qty = ""
        content_unit = ""
        
        # Find pack box with the specific class
        pack_box = soup.find('div', class_='OtcPriceBox__add-box___3rvCP')
        if pack_box:
            # Look for the specific span that contains the content information
            content_span = pack_box.find('span', class_='PackSizeLabel__single-packsize___3KEr_')
            
            if content_span and content_span.text:
                # Get the text like "100 tablets"
                content_text = content_span.get_text(strip=True)
                
                # Extract quantity and unit using regex
                # This pattern matches a number followed by non-numeric text
                match = re.match(r'(\d+(?:\.\d+)?)\s*(.*)', content_text)
                if match:
                    content_qty, content_unit = match.groups()
                    content_qty = content_qty.strip()
                    content_unit = content_unit.strip()
                else:
                    # Fallback if regex doesn't match
                    logging.warning(f"Regex didn't match content text: '{content_text}'")
            else:
                logging.warning("PackSizeLabel__single-packsize span not found")
        else:
            logging.warning("OtcPriceBox__add-box div not found")
        
        # Log the extracted values
        logging.info(f"Extracted pack details: qty={pack_qty}, content_qty={content_qty}, content_unit={content_unit}")
        
        return pack_qty, content_qty, content_unit
    except Exception as e:
        logging.error(f"Error extracting pack details: {e}")
        return 1, "", ""  # Default values in case of error

# Check if data indicates an error
def is_error_data(data_tuple):
    # Check if key fields contain error indicators
    product_description = data_tuple[0]
    product_highlights = data_tuple[1]
    manufacturer_name = data_tuple[2]
    images = data_tuple[6]
    
    # If any of these key fields contain 'Error' or 'not found', consider it an error
    if (product_description == "Error" or 
        product_highlights == "Error" or 
        manufacturer_name == "Error" or
        images == "Images not found" or
        len(data_tuple[5]) == 0):  # Empty pack_size_mrp_list
        return True
    return False

# Scrape product data from a given link with retry mechanism
def scrape_product_data(link, max_retries=3):
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(80, 130)}.0.0.0 Safari/537.36'
            }
            
            # Rotate proxies and add timeout
            proxy = {'http': random.choice(proxies)}
            response = requests.get(link, headers=headers, proxies=proxy, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Get product title (for better logging)
            title_element = soup.find('h1', class_=lambda x: x and 'title' in x.lower())
            product_title = title_element.get_text(strip=True) if title_element else "Unknown Title"

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

            # Get price - Updated to use new class
            price_div = soup.find('div', class_='PriceDetails__discount-div___nb724')
            if price_div:
                # Extract just the numeric part using regex
                price_text = price_div.get_text(strip=True)
                price_match = re.search(r'₹\s*(\d+)', price_text)
                price = price_match.group(1) if price_match else "Price not found"
            else:
                # Fallback to previous method if new tag not found
                price_span = soup.find('span', class_='SaleDetails__discount-price___3xUk9')
                price = ''.join(filter(str.isdigit, price_span.get_text(strip=True))) if price_span else "Price not found"

            # Log the extracted price for debugging
            logging.info(f"Extracted price: {price}")

            # Get pack size and MRP
            pack_size_mrp_list = []

            # Find the OtcVariants container which holds all size variants
            variant_container = soup.find('div', class_='OtcVariants__variant-div___2l321')
            variant_parent = soup.find('div', class_='')  # Empty class parent container

            # First look for all variant divs in the parent container
            if variant_parent:
                # Find all variant divs
                variant_divs = variant_parent.find_all('div', class_='OtcVariants__variant-div___2l321')
                
                # If no direct divs, look for the container itself
                if not variant_divs:
                    variant_divs = [variant_parent]
                
                # Process each variant container
                for div in variant_divs:
                    # Look for both link and div variants (selected vs. not selected)
                    variant_items = div.find_all(['a', 'div'], class_=lambda c: c and 'OtcVariantsItem__container___2ldJL' in c)
                    
                    for item in variant_items:
                        # Extract size text (e.g., "2 bottles")
                        size_text = item.find('div', class_='OtcVariantsItem__variant-text___1Grsz')
                        size_text = size_text.get_text(strip=True) if size_text else "N/A"
                        
                        # Extract price (e.g., "₹510")
                        price_div = item.find('div', class_='OtcVariantsItem__variant-price___3RfP5')
                        price_text = price_div.get_text(strip=True) if price_div else ""
                        
                        # Extract just the numeric part of the price
                        price_value = ''.join(filter(str.isdigit, price_text))
                        
                        # Add to list if both size and price were found
                        if size_text != "N/A" and price_value:
                            pack_size_mrp_list.append({"size": size_text, "mrp": price_value})
                            logging.info(f"Found variant: {size_text} - {price_value}")

            # If no variants found using the specific structure, fall back to previous methods
            if not pack_size_mrp_list:
                # Primary method using OtcPriceBox__add-box
                add_box = soup.find('div', class_='OtcPriceBox__add-box___3rvCP')
                if add_box:
                    # Extract pack size (e.g., "1 Jar")
                    pack_size_div = add_box.find('div', class_='DropdownA11y__display-text___QK-u8')
                    pack_size = pack_size_div.get_text(strip=True) if pack_size_div else "N/A"
                    
                    # Extract content (e.g., "500 gm Paste")
                    content_span = add_box.find('span', class_='PackSizeLabel__single-packsize___3KEr_')
                    content = content_span.get_text(strip=True) if content_span else "N/A"
                    
                    # Add to list as first option
                    mrp_value = price if price and price != "Price not found" else ""
                    pack_size_mrp_list.append({"size": f" {content}", "mrp": mrp_value})
                    
                    # Log successful extraction
                    logging.info(f"Extracted pack size: {pack_size} of {content} - MRP: {mrp_value}")

                # Fallback to other variant formats
                variant_divs = soup.find_all('div', class_='OtcVariantsItem__container___2ldJL')
                variant_links = soup.find_all('a', class_='OtcVariantsItem__container___2ldJL')
                
                for div in variant_divs:
                    size_text = div.find('div', class_='OtcVariantsItem__variant-text___1Grsz')
                    size_text = size_text.get_text(strip=True) if size_text else "N/A"
                    
                    mrp_tag = div.find('div', class_='OtcVariantsItem__variant-price___3RfP5')
                    mrp_text = ''.join(filter(str.isdigit, mrp_tag.get_text(strip=True))) if mrp_tag else ''
                    
                    if size_text != "N/A" and mrp_text:
                        pack_size_mrp_list.append({"size": size_text, "mrp": mrp_text})
                
                for a in variant_links:
                    size_text = a.find('div', class_='OtcVariantsItem__variant-text___1Grsz')
                    size_text = size_text.get_text(strip=True) if size_text else "N/A"
                    
                    mrp_tag = a.find('div', class_='OtcVariantsItem__variant-price___3RfP5')
                    mrp_text = ''.join(filter(str.isdigit, mrp_tag.get_text(strip=True))) if mrp_tag else ''
                    
                    if size_text != "N/A" and mrp_text:
                        pack_size_mrp_list.append({"size": size_text, "mrp": mrp_text})

            # Log the final results
            logging.info(f"Found {len(pack_size_mrp_list)} pack size/MRP options")

            # Get images
            product_images = extract_product_images(soup)
            
            # Extract pack details
            pack_qty, content_qty, content_unit = extract_pack_details(soup)

            # Data validation - check if we have critical data
            if not product_description_html or product_description_html == "Description not found":
                logging.warning(f"Missing product description for {product_title}")
                
            if not pack_size_mrp_list:
                logging.warning(f"No pack size/MRP found for {product_title}")
                
            if not product_images or product_images == "Images not found":
                logging.warning(f"No images found for {product_title}")

            # Log success
            logging.info(f"Successfully scraped: {link}")
            
            # Add variable delay to avoid pattern detection (1-3 seconds)
            time.sleep(random.uniform(1, 3))
            
            return product_description_html, product_highlights, manufacturer_name, address, price, pack_size_mrp_list, product_images, pack_qty, content_qty, content_unit

        except requests.RequestException as e:
            logging.error(f"Attempt {attempt+1}/{max_retries} failed for {link}: {e}")
            
            # Exponential backoff (2^attempt * 1-3 seconds)
            backoff_time = (2 ** attempt) * random.uniform(1, 3)
            logging.info(f"Backing off for {backoff_time:.2f} seconds before retry")
            time.sleep(backoff_time)
            
            # If this was the last attempt, log to failed_urls
            if attempt == max_retries - 1:
                product_name = "Unknown"
                try:
                    product_name = kapiva_links_df.loc[kapiva_links_df['Link'] == link, 'Product Name'].iloc[0]
                except:
                    pass
                failed_logger.error(f"FAILED: {product_name} | {link} | Error: {str(e)}")
        
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt+1}/{max_retries} for {link}: {e}")
            
            # If this was the last attempt, log to failed_urls
            if attempt == max_retries - 1:
                product_name = "Unknown"
                try:
                    product_name = kapiva_links_df.loc[kapiva_links_df['Link'] == link, 'Product Name'].iloc[0]
                except:
                    pass
                failed_logger.error(f"FAILED: {product_name} | {link} | Unexpected error: {str(e)}")
            
            # Back off before retry
            time.sleep((2 ** attempt) * random.uniform(1, 3))
    
    # If all retries failed, return error values
    return "Error", "Error", "Error", "Error", "Price not found", [], "Images not found", 1, "", ""

# Function to store failures in a separate Excel file
def save_failed_urls(urls, reasons):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    failed_df = pd.DataFrame({
        'URL': urls,
        'Reason': reasons,
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    failed_df.to_excel(f"failed_urls_{timestamp}.xlsx", index=False)

# Output file to store scraped data
output_file = "VitalCare_scrapped.xlsx"

# Process each link in the DataFrame
if os.path.exists(output_file):
    existing_data = pd.read_excel(output_file)
    print("This is to check")
    failed_urls = []
    failed_reasons = []

    for index, row in kapiva_links_df.iterrows():
        link = row['Link']
        product_description, product_highlights, manufacturer_name, address, price, pack_size_mrp_list, product_images, pack_qty, content_qty, content_unit = scrape_product_data(link)
        
        # Check if the data indicates an error
        if is_error_data((product_description, product_highlights, manufacturer_name, address, price, pack_size_mrp_list, product_images, pack_qty, content_qty, content_unit)):
            failed_urls.append(link)
            failed_reasons.append("Error in data extraction")
            continue
        
        # Add data to existing DataFrame
        existing_data.at[index, 'Product Description HTML'] = clean_text(product_description)
        existing_data.at[index, 'Product Highlights'] = clean_text(product_highlights)
        existing_data.at[index, 'Manufacturer Name'] = clean_text(manufacturer_name)
        existing_data.at[index, 'Address'] = clean_text(address)
        existing_data.at[index, 'Price'] = clean_text(price)
        existing_data.at[index, 'Pack Size MRP'] = json.dumps(pack_size_mrp_list, indent=4)
        existing_data.at[index, 'Images'] = clean_text(product_images)
        
        # New columns
        existing_data.at[index, 'Pack Quantity'] = pack_qty
        existing_data.at[index, 'Content Quantity'] = content_qty
        existing_data.at[index, 'Content Unit'] = content_unit

    # Save failed URLs to a separate file
    if failed_urls:
        save_failed_urls(failed_urls, failed_reasons)

else:
    print("Starting fresh scraping...")
    # If starting fresh
    kapiva_links_df[['Product Description HTML', 'Product Highlights', 'Manufacturer Name', 
                    'Address', 'Price', 'Pack Size MRP', 'Images', 
                    'Pack Quantity', 'Content Quantity', 'Content Unit']] = kapiva_links_df['Link'].apply(
        lambda link: pd.Series(scrape_product_data(link)))
    existing_data = kapiva_links_df
    print(existing_data)

# Debug output to verify image URLs are being captured
print("Checking data before saving to Excel...")
print(f"'Images' column exists: {'Images' in existing_data.columns}")
print(f"First few image URLs sample:")
for i, img in enumerate(existing_data['Images'].head()):
    if i < 3:  # Show just first 3 samples
        print(f"  Row {i+1}: {img[:100]}...")  # Show first 100 chars

# Save the cleaned and updated data to an Excel file
existing_data.to_excel(output_file, index=False)
print(f"Scraping completed and data saved to '{output_file}'")
