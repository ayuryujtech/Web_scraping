import os
import requests
from pathlib import Path
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_image_from_url(url, filename):
    try:
        if os.path.exists(filename):
            print(f"File already exists: {filename}")
            return
        
        response = requests.get(url, stream=True)
        if response.status_code in (200, 206):  
            ensure_directory_existence(filename)
            
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(1024 * 8):  
                    file.write(chunk)
            print(f"Downloaded: {filename}")
        else:
            print(f"Failed to download image from {url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while downloading {url}: {e}")

def ensure_directory_existence(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        Path(directory).mkdir(parents=True, exist_ok=True)

def filter_image_url(url):
   
    filtered_url = re.sub(r'/(l_watermark_[^/]*/|a_ignore[^/]*/)', '/', url)
    
    
    filtered_url = re.sub(r'/[^/]*,[^/]*/', '/', filtered_url)
    
    return filtered_url

def process_excel(file_path):
    try:
        df = pd.read_excel(file_path, engine='openpyxl')  
        
        col_title = 'Package Unique Name'
        col_image_src = 'Images'
        # col_price = 'Price'
        
        folder_name = Path(file_path).parent.name  
        download_tasks = []
        with ThreadPoolExecutor(max_workers=50) as executor:  
            for index, row in df.iterrows():
                title = row[col_title]
                img_srcs = row[col_image_src]
                # price = row[col_price]

                if pd.isna(img_srcs) or img_srcs.strip() == '':
                    print(f"No images for '{title}'")
                    continue
                
                target_folder = f"downloads/PatanjaliAyurveda_Filter_filled/{title}"
                ensure_directory_existence(target_folder)  # Ensure the folder exists  
                
                img_urls = img_srcs.split('|')
                
                for i, img_url in enumerate(img_urls):
                    if img_url.strip():  
                        filtered_url = filter_image_url(img_url.strip())
                        
                        img_filename = f"{target_folder}/image_{i+1}.jpg"
                        
                        
                        download_tasks.append((filtered_url, img_filename))
            
            # Process the download tasks in parallel
            futures = [executor.submit(download_image_from_url, url, filename) for url, filename in download_tasks]
            
            for future in as_completed(futures):
                try:
                    future.result()  # To handle exceptions raised in threads
                except Exception as e:
                    print(f"An error occurred while processing a download task: {e}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

if __name__ == "__main__":
    excel_file_path = '/home/vedant/ScrapData/gpt/UploadReady/PatanjaliDivya_fitlter_Filled.xlsx' 
    
    # Process the specified Excel file
    process_excel(excel_file_path)

    print("All images have been downloaded.")
