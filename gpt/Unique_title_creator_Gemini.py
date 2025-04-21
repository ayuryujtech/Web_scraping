import pandas as pd
import google.generativeai as genai
import time
from random import uniform
import re
import os

# Load the Excel file
file_path = r'E:\AYURYUJ\Web_scraping\scrap\vital_care_scrapped_with_categoriesBenefits.xlsx'
kapiva_data = pd.read_excel(file_path)

# Set up the Gemini API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))")

# Function to generate unique titles with Gemini using benefits and pack information
def generate_unique_title(product_title, benefits=None, pack_qty=None, content_qty=None, content_unit=None):
    # Include packaging information if available
    packaging_info = ""
    if content_qty and content_unit:
        packaging_info = f" {content_qty} {content_unit}"
    
    # Simplified prompt that focuses only on a unique name
    prompt = (
        f"Generate ONLY a unique product name for '{product_title}'{packaging_info}. "
        f"Do not add any descriptions, benefits, or additional comments. "
        f"Keep it concise with just 3-5 extra words to make it unique. "
        f"Return only the exact product name with no quotes, explanations or suggestions."
    )
    
    try:
        # Add delay between API calls (2-4 seconds)
        time.sleep(uniform(2, 4))
        
        # Configure the model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Get the response text and clean it thoroughly
        generated_title = response.text.strip()
        # Remove quotes, explanations and any extra text
        generated_title = generated_title.strip('"\'')
        # If response contains multiple lines, take only the first line
        generated_title = generated_title.split('\n')[0]
        # Remove any phrases like "Here's a unique name:" or "Unique name:"
        generated_title = re.sub(r'^.*?name:?\s*', '', generated_title, flags=re.IGNORECASE)
        
        return generated_title
    except Exception as e:
        if "429" in str(e):  # Rate limit error
            print("Rate limit reached, waiting 60 seconds...")
            time.sleep(60)  # Wait longer on rate limit
            # Try once more
            try:
                response = model.generate_content(prompt)
            except Exception as e2:
                print(f"Second attempt failed: {e2}")
                return product_title
        else:
            print(f"Error generating title: {e}")
            return product_title  # fallback to original title if API fails

# Function to make only duplicate titles unique
def make_titles_unique(df):
    # Check column names first
    print("Available columns:", df.columns.tolist())
    
    # Sort by Product Name only
    df = df.sort_values(by=['Product Name']).reset_index(drop=True)
    
    # Identify duplicate titles
    duplicates = df.duplicated(subset='Product Name', keep=False)
    
    # Process in smaller batches
    batch_size = 10
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}...")
        time.sleep(30)  # Wait between batches
        
        # Process batch with all columns
        df.loc[batch.index, 'Unique Title'] = batch.apply(
            lambda row: generate_unique_title(
                product_title=row['Product Name'],
                benefits=row.get('Product Highlights', ''),
                pack_qty=row.get('Pack Quantity', None),
                content_qty=row.get('Content Quantity', None),
                content_unit=row.get('Content Unit', None)
            ) if duplicates[row.name] else row['Product Name'],
            axis=1
        )
    
    return df

# Apply the function to make titles unique
unique_kapiva_data = make_titles_unique(kapiva_data)

# Save the modified data back to a new Excel file
output_path = 'vitalCare_unique_titles.xlsx'

# Ensure all columns are preserved - FIXED to include Predicted Categories and Showcase Benefits
columns_to_save = [
    'Product Name', 'Link', 'Source', 'Product Description HTML',
    'Product Highlights', 'Manufacturer Name', 'Address', 'Price',
    'Pack Size MRP', 'Images', 'Pack Quantity', 'Content Quantity',
    'Content Unit', 'Predicted Categories', 'Showcase Benefits', 'Unique Title'
]

# Print input column count
print(f"Input file has {len(kapiva_data.columns)} columns: {kapiva_data.columns.tolist()}")

# Verify all expected columns exist
all_cols_exist = all(col in unique_kapiva_data.columns for col in columns_to_save)
if not all_cols_exist:
    missing_cols = [col for col in columns_to_save if col not in unique_kapiva_data.columns]
    print(f"Warning: Missing columns in input file: {missing_cols}")
    # Only use existing columns
    existing_columns = [col for col in columns_to_save if col in unique_kapiva_data.columns]
    print(f"Will save {len(existing_columns)} columns: {existing_columns}")
else:
    existing_columns = columns_to_save
    print(f"All {len(columns_to_save)} expected columns found.")

# Save all existing columns to output
unique_kapiva_data[existing_columns].to_excel(output_path, index=False)

# Verify output file
output_df = pd.read_excel(output_path)
print(f"Output file has {len(output_df.columns)} columns: {output_df.columns.tolist()}")
print(f"Processed data saved to {output_path}")