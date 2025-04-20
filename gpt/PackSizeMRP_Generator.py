import pandas as pd
import json
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Function to clean the Unique Title column
def clean_unique_title(title):
    if isinstance(title, str) and '|' in title:
        return title.split('|')[0].strip()  # Return only text before the pipe
    return title

def generate_pack_size_mrp_content(input_file, output_file):
    logging.info(f"Reading file: {input_file}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(input_file)
        
        # Verify required columns exist
        required_columns = ['Content Quantity', 'Content Unit', 'Price']
        if not all(col in df.columns for col in required_columns):
            logging.error(f"Missing one or more required columns: {required_columns}")
            return
        
        # Clean Unique Title column if it exists
        if 'Unique Title' in df.columns:
            logging.info("Cleaning Unique Title column - removing text after | symbol")
            df['Unique Title'] = df['Unique Title'].apply(clean_unique_title)
            
            # Log some examples of cleaned titles
            if not df.empty:
                sample_titles = df['Unique Title'].head(3).tolist()
                logging.info(f"Sample cleaned titles: {sample_titles}")
        
        def create_pack_size_mrp(row):
            try:
                # Create the structured data
                pack_data = [{
                    'size': f"{row['Content Quantity']} {row['Content Unit']}",
                    'mrp': str(row['Price']),
                    
                }]
                return json.dumps(pack_data)
            except Exception as e:
                logging.error(f"Error creating pack size MRP: {e}")
                return None
        
        # Create Pack Size MRP column
        df['Pack Size MRP'] = df.apply(create_pack_size_mrp, axis=1)
        
        # Remove rows where Pack Size MRP creation failed
        df = df.dropna(subset=['Pack Size MRP'])
        
        # Save to new file
        df.to_excel(output_file, index=False)
        logging.info(f"Data saved successfully to: {output_file}")
        
        # Display sample of processed data
        sample_columns = ['Content Quantity', 'Content Unit', 'Price', 'Pack Size MRP']
        if 'Unique Title' in df.columns:
            sample_columns.insert(0, 'Unique Title')
            
        logging.info("\nSample of processed data:")
        sample_data = df[sample_columns].head()
        print(sample_data)
        
    except Exception as e:
        logging.error(f"Error processing file: {e}")

if __name__ == "__main__":
    # File paths
    input_file = r"E:\AYURYUJ\Web_scraping\gpt\all_kottakal_Empty.xlsx"
    output_file = r"E:\AYURYUJ\Web_scraping\gpt\all_kottakal_with_packsizeMRP.xlsx"
    
    # Run the generator
    generate_pack_size_mrp_content(input_file, output_file)