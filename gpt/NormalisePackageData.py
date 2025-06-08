import json
import re
from openpyxl import load_workbook, Workbook
import os 
need_cleaning = True
import pandas as pd
# Note:
# This File Adds the Normalized Data, Variant Name, Package Unique Name columns to the original sheet 
# Make sure to remove the old columns before running this file
# Use need_cleaning = False if you don't want to clean the data ( for anirban Data use True )
#cleaning the names
def clean_unique_title(title):
    """Clean special characters from unique titles while preserving parentheses"""
    if pd.isna(title):
        return title
    cleaned = str(title)
    cleaned = re.sub(r'[,:;"\'\[\]{}\|]', '', cleaned)  # Remove punctuation including |
    cleaned = re.sub(r'[®™©]', '', cleaned)  # Remove trademark symbols
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Replace multiple spaces with single space
    cleaned = re.sub(r'-+', '-', cleaned)  # Replace multiple hyphens with single hyphen
    cleaned = re.sub(r'\s*\(\s*', ' (', cleaned)  # Clean space before (
    cleaned = re.sub(r'\s*\)\s*', ') ', cleaned)  # Clean space after )
    cleaned = cleaned.strip()
    cleaned = re.sub(r'\s*-\s*', '-', cleaned)
    return cleaned

# Function to normalize pack data with product-specific names

def normalize_pack_data(pack_data, product_name, size, unit, mrp):
    normalized_data = []
    seen_variants = set()  # Track unique (size, flavor) tuples
    print("Pack Data: ", pack_data, size, unit , mrp)
    if need_cleaning:
        if len(pack_data) <= 1:
            print("No need to clean")
            mrp = pack_data[0].get('mrp', mrp)
            pack_data = [{ "size" : str(size) + " " + str(unit), "mrp" : mrp}]
        else:
            pack_data = pack_data[1:]
            print("Need to clean")
            print(pack_data)
    for idx, item in enumerate(pack_data):
        # Extract quantity and unit from size field using regex
        match = re.match(r"(\d+(?:\.\d+)?)\s*(\w+)", item.get('size', ''))
        if match:
            quantity, unit = match.groups()
            mrp = item.get('mrp', '')
            flavor = item.get('flavor', '')

            # Ensure the product name corresponds to this variant
            variant_product_name = f"{product_name} {flavor} {quantity}{unit}" if flavor else f"{product_name} {quantity}{unit}"
            variant_product_name= clean_unique_title(variant_product_name)  # Clean the product name
            # Unique identifier for this variant (size and flavor)
            variant_key = (quantity, unit, flavor)
            print(size, unit , mrp)
            if variant_key not in seen_variants:  # Check if variant is unique
                seen_variants.add(variant_key)  # Add to set of seen variants
                normalized_item = {
                    'type': 'primary' if idx == 0 else 'secondary',
                    'productName': variant_product_name,  # Use variant-specific name
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

# Function to process the Excel file and normalize data
def process_excel(file_path):
    wb = load_workbook(file_path)
    sheet = wb.active
    
    # Identify columns for "Pack Size MRP" and "Product Name"
    pack_size_mrp_col = None
    product_name_col = None
    mrp_col = None
    size_col = None
    unit_col = None
    for col in sheet.iter_cols(1, sheet.max_column):
        header = col[0].value
        if header == "Pack Size MRP":
            pack_size_mrp_col = col[0].column
        elif header == "Product Name":
            product_name_col = col[0].column
        elif header == "Content Quantity":
            size_col = col[0].column
        elif header == "Content Unit":
            unit_col = col[0].column
        elif header == "Price":
            mrp_col = col[0].column

    if not pack_size_mrp_col or not product_name_col or not size_col or not unit_col or not mrp_col:
        return "Error: Necessary columns not found in the sheet."

    # Create a new workbook to save the processed data
    new_wb = Workbook()
    new_sheet = new_wb.active
    
    # Copy all headers from the original sheet and add the new columns
    headers = [cell.value for cell in sheet[1]]
    # remove old headers and columns from sheet like Normalized Data, Variant Name, Package Unique Name if present
    if "Normalized Data" in headers or "Variant Name" in headers or "Package Unique Name" in headers:
        return "Error: Necessary columns already present in the sheet. Please remove them and try again."
    headers.extend([ "Normalized Data","Variant Name","Package Unique Name"])  # Add new headers
    new_sheet.append(headers)

    # Process each row in the original Excel sheet
    for row in range(2, sheet.max_row + 1):
        row_data = [sheet.cell(row=row, column=col).value for col in range(1, sheet.max_column + 1)]
        product_name = sheet.cell(row=row, column=product_name_col).value
        pack_size_mrp_raw = sheet.cell(row=row, column=pack_size_mrp_col).value
        size = sheet.cell(row=row, column=size_col).value
        unit = sheet.cell(row=row, column=unit_col).value
        mrp = sheet.cell(row=row, column=mrp_col).value
        if not pack_size_mrp_raw or not product_name:
            row_data.extend(["", "", ""])  # Add empty normalized data and variant name if no data
        else:
            try:
                # Parse the JSON-like string in "Pack Size MRP" column
                pack_data = json.loads(pack_size_mrp_raw.replace("'", '"'))  # JSON parsing
                normalized_data = normalize_pack_data(pack_data, product_name, size, unit, mrp)

                # Extract distinct flavors for the "Variant Name" column
                unique_flavors = {item.get('flavor', '') for item in pack_data}
                variant_name = ', '.join(filter(None, unique_flavors))  # Join unique flavors as a single string

                # Determine the "Package Unique Name" based on the primary element
                primary_package_name = normalized_data[0]['productName'] if normalized_data else ''

                # Add the normalized data, variant name, and primary package name to the row
                row_data.extend([json.dumps(normalized_data, indent=4), variant_name, primary_package_name])

            except json.JSONDecodeError as e:
                # Handle JSON parsing errors
                print(f"Error decoding JSON in row {row}: {e}")
                row_data.extend(["", "", ""])  # Add empty normalized data, variant name, and package name

        # Add the row to the new sheet
        new_sheet.append(row_data)

    # Save the new workbook
    new_file_path = "E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\vitalCare\\vitalCare_Normalised.xlsx"
    new_wb.save(new_file_path)
    return new_file_path

# Process the uploaded Excel file
processed_file_path = process_excel("E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\vitalCare\\vitalCare_Filled.xlsx")
print(f"Processed file saved at: {processed_file_path}")
