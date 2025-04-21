import openai
import openpyxl
import json
import re
import time
from openpyxl import load_workbook, Workbook

# Function to set up OpenAI API key (replace with your actual key)
openai.api_key = ''

# Function to format data into the target structure with retry handling for API calls
def normalize_pack_data(pack_data):
    normalized_data = []
    seen_variants = set()  # Track unique (size, flavor) tuples

    for idx, item in enumerate(pack_data):
        # Extract quantity and unit from size field using regex
        match = re.match(r"(\d+)\s*(\w+)", item.get('size', ''))
        if match:
            quantity, unit = match.groups()
            mrp = item.get('mrp', '')
            flavor = item.get('flavor', '')

            # Unique identifier for this variant (size and flavor)
            variant_key = (quantity, unit, flavor)
            if variant_key not in seen_variants:  # Check if variant is unique
                seen_variants.add(variant_key)  # Add to set of seen variants
                normalized_item = {
                    'type': 'primary' if idx == 0 else 'secondary',
                    'size': {
                        'quantity': quantity,
                        'unit': unit
                    },
                    'mrp': mrp,
                    'sellingPrice': mrp,
                    'variant': flavor
                }
                normalized_data.append(normalized_item)
    return normalized_data

# Retry logic for API calls
def call_openai_with_retry(prompt, retries=3, delay=60):
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.5
            )
            return response['choices'][0]['message']['content'].strip()
        except openai.error.OpenAIError as e:
            print(f"OpenAI API error: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Skipping this entry.")
                return None

# Function to process the Excel file and update with normalized data and variants
def process_excel(file_path):
    wb = load_workbook(file_path)
    sheet = wb.active
    
    # Identify "Pack Size MRP" column
    pack_size_mrp_col = None
    for col in sheet.iter_cols(1, sheet.max_column):
        header = col[0].value
        if header == "Pack Size MRP":
            pack_size_mrp_col = col[0].column
            break

    if not pack_size_mrp_col:
        print("Error: Could not find 'Pack Size MRP' column in the sheet.")
        return

    # Create a new workbook to save the processed data
    new_wb = Workbook()
    new_sheet = new_wb.active 
    new_sheet.append(["SKU", "Pack Size MRP", "Normalized Data", "Variant Name"])  # Set headers

    # Process each row in the original Excel sheet
    for row in range(2, sheet.max_row + 1):
        sku = sheet.cell(row=row, column=1).value
        pack_size_mrp_raw = sheet.cell(row=row, column=pack_size_mrp_col).value

        if not pack_size_mrp_raw:
            continue  # Skip rows with missing data

        try:
            # Parse the JSON-like string in "Pack Size MRP" column
            pack_data = json.loads(pack_size_mrp_raw.replace("'", '"'))  # JSON parsing
            normalized_data = normalize_pack_data(pack_data)

            # Extract distinct flavors for the "Variant Name" column
            unique_flavors = {item.get('flavor', '') for item in pack_data}
            variant_name = ', '.join(filter(None, unique_flavors))  # Join unique flavors as a single string

            # Add the normalized data to the new sheet
            new_sheet.append([sku, pack_size_mrp_raw, json.dumps(normalized_data, indent=4), variant_name])

        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            print(f"Error decoding JSON in row {row}: {e}")
            continue

    # Save the new workbook
    new_file_path = file_path.replace(".xlsx", "_normalized_with_variants.xlsx")
    new_wb.save(new_file_path)
    print(f"All rows processed successfully and new workbook saved at {new_file_path}")

# Example usage (replace with actual file path)
process_excel("/home/vedant/DataScraper/Web_scraping/gpt/vitalcare_Filled.xlsx")
