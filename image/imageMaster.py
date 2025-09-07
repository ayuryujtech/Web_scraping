import os
import requests
from pathlib import Path
import pandas as pd
import re
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
output_path=r"E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\vitalCare\\vital_Care_Images" #folderPath for Images
input_path=r"E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\vitalCare\\vitalCare_Normalised.xlsx"#filled file path
# Set up logging
log_dir = "download_logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"download_log_{timestamp}.txt")

# Initialize tracking data
download_stats = {
    "total_products": 0,
    "products_with_images": 0,
    "products_without_images": 0,
    "total_images_to_download": 0,
    "successfully_downloaded": 0,
    "failed_downloads": 0,
    "failed_images": []  # Will store tuples of (product_name, url, error_message)
}

def log_message(message):
    """Write message to both console and log file"""
    print(message)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def download_image_from_url(url, filename, product_name, timeout=30):
    """Download image with error tracking"""
    try:
        if os.path.exists(filename):
            log_message(f"File already exists: {filename}")
            download_stats["successfully_downloaded"] += 1
            return True
        
        response = requests.get(url, stream=True, timeout=timeout)
        if response.status_code in (200, 206):  
            ensure_directory_existence(filename)
            
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(1024 * 8):  
                    file.write(chunk)
            log_message(f"Downloaded: {filename}")
            download_stats["successfully_downloaded"] += 1
            return True
        else:
            error_msg = f"Failed to download image from {url}. Status code: {response.status_code}"
            log_message(error_msg)
            download_stats["failed_downloads"] += 1
            download_stats["failed_images"].append((product_name, url, error_msg))
            return False
    except Exception as e:
        error_msg = f"An error occurred while downloading {url}: {e}"
        log_message(error_msg)
        download_stats["failed_downloads"] += 1
        download_stats["failed_images"].append((product_name, url, str(e)))
        return False

def download_image_with_retry(url, filename, product_name, max_retries=3, timeout=45):
    """Download image with multiple retries and longer timeout"""
    if os.path.exists(filename):
        log_message(f"File already exists: {filename}")
        return True
    
    for attempt in range(max_retries):
        try:
            log_message(f"Recovery attempt {attempt+1} to download {url}")
            
            # Add random delay between attempts
            if attempt > 0:
                delay = random.uniform(3, 8)
                log_message(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
            
            # Use a different user agent for each attempt
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
            ]
            
            headers = {
                'User-Agent': user_agents[attempt % len(user_agents)],
                'Referer': 'https://www.1mg.com/'
            }
            
            response = requests.get(
                url, 
                stream=True, 
                timeout=timeout,
                headers=headers
            )
            
            if response.status_code in (200, 206):  
                ensure_directory_existence(filename)
                
                with open(filename, 'wb') as file:
                    for chunk in response.iter_content(1024 * 8):  
                        file.write(chunk)
                log_message(f"Successfully recovered: {filename}")
                return True
            else:
                log_message(f"Failed recovery attempt {attempt+1}: Status code {response.status_code}")
                
        except Exception as e:
            log_message(f"Error on recovery attempt {attempt+1}: {e}")
    
    # If we reach here, all attempts failed
    error_msg = f"All {max_retries} recovery attempts failed to download {url}"
    log_message(error_msg)
    return False

def ensure_directory_existence(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        Path(directory).mkdir(parents=True, exist_ok=True)

def filter_image_url(url):
    # Adjust the regex if needed
    filtered_url = re.sub(r'/(l_watermark_[^/]*/|a_ignore[^/]*/)', '/', url)
    filtered_url = re.sub(r'/[^/]*,[^/]*/', '/', filtered_url)
    return filtered_url

def process_excel(file_path):
    log_message(f"Starting image download process for: {file_path}")
    
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        download_stats["total_products"] = len(df)
        
        # Update column names to use Unique Title
        col_title = 'Package Unique Name'  # Changed from 'Product Name' to 'Unique Title'
        col_image_src = 'Images'    # This remains the same
        
        # Check if Unique Title column exists
        if col_title not in df.columns:
            log_message(f"Warning: '{col_title}' column not found. Available columns: {df.columns.tolist()}")
            log_message("Falling back to 'Product Name' column")
            col_title = 'Product Name'
        
        download_tasks = []
        
        with ThreadPoolExecutor(max_workers=50) as executor:  
            for index, row in df.iterrows():
                title = row[col_title]
                img_srcs = row[col_image_src]

                if pd.isna(img_srcs) or img_srcs.strip() == '':
                    log_message(f"No images for '{title}'")
                    download_stats["products_without_images"] += 1
                    continue
                
                download_stats["products_with_images"] += 1
                
                # Sanitize folder name to remove invalid characters
                safe_title = re.sub(r'[<>:"/\\|?*]', '', str(title))
                
                target_folder = f"{output_path}/{safe_title}"
                ensure_directory_existence(target_folder)
                
                img_urls = img_srcs.split('|')
                
                for i, img_url in enumerate(img_urls):
                    if img_url.strip():
                        download_stats["total_images_to_download"] += 1
                        filtered_url = filter_image_url(img_url.strip())
                        img_filename = f"{target_folder}/image_{i+1}.jpg"
                        download_tasks.append((filtered_url, img_filename, title))
            
            # Process the download tasks in parallel
            futures = [executor.submit(download_image_from_url, url, filename, product_name) 
                      for url, filename, product_name in download_tasks]
            
            for future in as_completed(futures):
                try:
                    future.result()  # To handle exceptions raised in threads
                except Exception as e:
                    log_message(f"An error occurred in thread: {e}")
    
    except Exception as e:
        log_message(f"An error occurred while processing {file_path}: {e}")
    
    # Generate summary report
    generate_summary_report()
    
    # If there are any failed downloads, try to recover them
    if download_stats["failed_downloads"] > 0:
        # Save failed downloads to Excel
        failed_report_file = os.path.join(log_dir, f"failed_downloads_{timestamp}.xlsx")
        failed_df = pd.DataFrame(download_stats["failed_images"], 
                                columns=["Product Name", "Image URL", "Error Message"])
        failed_df.to_excel(failed_report_file, index=False)
        
        log_message(f"\nAttempting to recover {download_stats['failed_downloads']} failed images...")
        recover_failed_images(failed_report_file)
    
    return

def generate_summary_report():
    """Create a detailed summary report of the download process"""
    log_message("\n" + "="*50)
    log_message("DOWNLOAD SUMMARY REPORT")
    log_message("="*50)
    log_message(f"Total products processed: {download_stats['total_products']}")
    log_message(f"Products with images: {download_stats['products_with_images']}")
    log_message(f"Products without images: {download_stats['products_without_images']}")
    log_message(f"Total images to download: {download_stats['total_images_to_download']}")
    log_message(f"Successfully downloaded: {download_stats['successfully_downloaded']}")
    log_message(f"Failed downloads: {download_stats['failed_downloads']}")
    
    # Calculate success rate
    if download_stats['total_images_to_download'] > 0:
        success_rate = (download_stats['successfully_downloaded'] / download_stats['total_images_to_download']) * 100
        log_message(f"Download success rate: {success_rate:.2f}%")
    
    # Generate failed downloads report
    if download_stats['failed_downloads'] > 0:
        log_message("\nFAILED DOWNLOADS:")
        log_message("-"*50)
        
        # Log first 10 failed downloads in the text log
        for i, (product, url, error) in enumerate(download_stats["failed_images"][:10]):
            log_message(f"{i+1}. Product: {product}")
            log_message(f"   URL: {url}")
            log_message(f"   Error: {error}")
        
        if len(download_stats["failed_images"]) > 10:
            log_message(f"... and {len(download_stats['failed_images']) - 10} more.")
    
    log_message("="*50)

def recover_failed_images(failed_images_path):
    """Process the failed downloads file and try to recover the images"""
    recovery_stats = {
        "total_failed_images": 0,
        "successfully_recovered": 0,
        "still_failed": 0,
        "failed_images": []
    }
    
    if not os.path.exists(failed_images_path):
        log_message(f"Error: Failed images file not found: {failed_images_path}")
        return
    
    try:
        # Read the failed downloads Excel file
        failed_df = pd.read_excel(failed_images_path)
        
        if 'Product Name' not in failed_df.columns or 'Image URL' not in failed_df.columns:
            log_message("Error: Required columns not found in the failed images file")
            return
        
        recovery_stats["total_failed_images"] = len(failed_df)
        log_message(f"Found {recovery_stats['total_failed_images']} failed images to recover")
        
        # Process each failed image
        for index, row in failed_df.iterrows():
            product_name = row['Product Name']
            url = row['Image URL']
            
            # Sanitize product name for folder creation
            safe_title = re.sub(r'[<>:"/\\|?*]', '', str(product_name))
            
            # Extract image number
            img_number = 1
            for i in range(1, 20):  # Attempt to find next available number
                target_path = f"{output_path}/{safe_title}/image_{i}.jpg"
                if not os.path.exists(target_path):
                    img_number = i
                    break
            
            target_filename = f"{output_path}/{safe_title}/image_{img_number}.jpg"
            
            log_message(f"Attempting to recover image for {product_name}")
            success = download_image_with_retry(url, target_filename, product_name)
            
            if success:
                recovery_stats["successfully_recovered"] += 1
            else:
                recovery_stats["still_failed"] += 1
                recovery_stats["failed_images"].append((product_name, url, "Failed after multiple recovery attempts"))
            
            # Add a small delay between downloads
            time.sleep(random.uniform(1, 3))
        
        # Generate recovery report
        log_message("\n" + "="*50)
        log_message("RECOVERY SUMMARY REPORT")
        log_message("="*50)
        log_message(f"Total failed images attempted: {recovery_stats['total_failed_images']}")
        log_message(f"Successfully recovered: {recovery_stats['successfully_recovered']}")
        log_message(f"Still failed: {recovery_stats['still_failed']}")
        
        # Calculate success rate
        if recovery_stats['total_failed_images'] > 0:
            success_rate = (recovery_stats['successfully_recovered'] / recovery_stats['total_failed_images']) * 100
            log_message(f"Recovery success rate: {success_rate:.2f}%")
        
        # Generate report for images that still failed
        if recovery_stats['still_failed'] > 0:
            log_message("\nIMAGES STILL FAILING:")
            log_message("-"*50)
            
            # Create Excel report of still failing downloads
            still_failed_report_file = os.path.join(log_dir, f"still_failed_downloads_{timestamp}.xlsx")
            failed_df = pd.DataFrame(recovery_stats["failed_images"], 
                                   columns=["Product Name", "Image URL", "Error Message"])
            failed_df.to_excel(still_failed_report_file, index=False)
            
            log_message(f"Detailed report of still failing downloads saved to: {still_failed_report_file}")
            
            # Log the first few still failing downloads
            for i, (product, url, error) in enumerate(recovery_stats["failed_images"][:5]):
                log_message(f"{i+1}. Product: {product}")
                log_message(f"   URL: {url}")
        
        log_message("="*50)
        
    except Exception as e:
        log_message(f"Error processing failed images file: {e}")

def verify_product_folders(excel_file_path):
    """Check which products don't have folders created"""
    log_message("\n" + "="*50)
    log_message("FOLDER VERIFICATION")
    log_message("="*50)
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file_path)
        
        # Determine which column to use for titles
        col_title = 'Unique Title' if 'Unique Title' in df.columns else 'Product Name'
        
        log_message(f"Total products in Excel: {len(df)}")
        
        # Check each product
        missing_folders = []
        for index, row in df.iterrows():
            title = row[col_title]
            if pd.isna(title) or title.strip() == '':
                log_message(f"Row {index+2}: Missing title")
                missing_folders.append((index+2, "Missing title", ""))
                continue
                
            # Sanitize folder name
            safe_title = re.sub(r'[<>:"/\\|?*]', '', str(title))
            folder_path = f"{output_path}/{safe_title}"
            
            if not os.path.exists(folder_path):
                # Check if this product has images
                has_images = not (pd.isna(row.get('Images', '')) or row.get('Images', '').strip() == '')
                reason = "No images" if not has_images else "Unknown issue"
                
                missing_folders.append((index+2, title, reason))
                log_message(f"Row {index+2}: No folder for '{title}' - {reason}")
        
        log_message(f"\nTotal missing folders: {len(missing_folders)}")
        
        # Save missing folders report
        if missing_folders:
            missing_report_file = os.path.join(log_dir, f"missing_folders_{timestamp}.xlsx")
            missing_df = pd.DataFrame(missing_folders, columns=["Row", "Product Title", "Reason"])
            missing_df.to_excel(missing_report_file, index=False)
            log_message(f"Missing folders report saved to: {missing_report_file}")
        
    except Exception as e:
        log_message(f"Error verifying product folders: {e}")

if __name__ == "__main__":
    # Update this path to point to your filled file
    excel_file_path = input_path
    
    # Process the specified Excel file
    process_excel(excel_file_path)
    
    # Verify all products have folders
    verify_product_folders(excel_file_path)
    
    log_message("\nImage download process completed with automatic recovery!")
