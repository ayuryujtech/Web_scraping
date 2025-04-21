import os
import requests
import pandas as pd
import logging
import json
from datetime import datetime
from pathlib import Path
import time
import random

# Set up logging
log_dir = "download_logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"recovery_log_{timestamp}.txt")

# Initialize tracking data
recovery_stats = {
    "total_failed_images": 0,
    "successfully_recovered": 0,
    "still_failed": 0,
    "failed_images": []  # Will store info about images that still fail
}

def log_message(message):
    """Write message to both console and log file"""
    print(message)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def ensure_directory_existence(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        Path(directory).mkdir(parents=True, exist_ok=True)

def download_image_with_retry(url, filename, product_name, max_retries=3, timeout=45):
    """Download image with multiple retries and longer timeout"""
    if os.path.exists(filename):
        log_message(f"File already exists: {filename}")
        recovery_stats["successfully_recovered"] += 1
        return True
    
    for attempt in range(max_retries):
        try:
            log_message(f"Attempt {attempt+1} to download {url}")
            
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
                log_message(f"Successfully downloaded: {filename}")
                recovery_stats["successfully_recovered"] += 1
                return True
            else:
                log_message(f"Failed attempt {attempt+1}: Status code {response.status_code}")
                
        except Exception as e:
            log_message(f"Error on attempt {attempt+1}: {e}")
    
    # If we reach here, all attempts failed
    error_msg = f"All {max_retries} attempts failed to download {url}"
    log_message(error_msg)
    recovery_stats["still_failed"] += 1
    recovery_stats["failed_images"].append((product_name, url, error_msg))
    return False

def recover_failed_images(failed_images_path):
    """Process the failed downloads file and try to recover the images"""
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
                target_path = f"downloads/all_zandu_unique/{safe_title}/image_{i}.jpg"
                if not os.path.exists(target_path):
                    img_number = i
                    break
            
            target_filename = f"downloads/all_zandu_unique/{safe_title}/image_{img_number}.jpg"
            
            log_message(f"Attempting to recover image for {product_name}")
            download_image_with_retry(url, target_filename, product_name)
            
            # Add a small delay between downloads
            time.sleep(random.uniform(1, 3))
        
        # Generate recovery report
        generate_recovery_report()
        
    except Exception as e:
        log_message(f"Error processing failed images file: {e}")

def generate_recovery_report():
    """Create a summary report of the recovery process"""
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
            log_message(f"   Error: {error}")
        
        if len(recovery_stats["failed_images"]) > 5:
            log_message(f"... and {len(recovery_stats['failed_images']) - 5} more. See Excel report for details.")
    
    log_message("="*50)
    log_message(f"Recovery log file: {log_file}")

if __name__ == "__main__":
    import re  # Import re for sanitizing folder names
    
    # Path to the failed downloads report
    failed_images_file = r"E:\AYURYUJ\Web_scraping\image\download_logs\failed_downloads_20250411_000148.xlsx"
    
    log_message(f"Starting recovery of failed image downloads from: {failed_images_file}")
    recover_failed_images(failed_images_file)
    
    log_message("\nImage recovery process completed!")