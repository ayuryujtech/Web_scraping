import openpyxl
import json
import re
from openpyxl import load_workbook, Workbook

# Function to normalize "Pack Size MRP" data
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

# Function to process the Excel file and include all data with the new normalized column
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

    # Copy original headers and add new headers for normalized data
    headers = [cell.value for cell in sheet[1]]
    headers.extend(["Normalized Data", "Variant Name"])
    new_sheet.append(headers)

    # Process each row in the original Excel sheet
    for row in range(2, sheet.max_row + 1):
        row_data = [sheet.cell(row=row, column=col).value for col in range(1, sheet.max_column + 1)]
        pack_size_mrp_raw = sheet.cell(row=row, column=pack_size_mrp_col).value

        if not pack_size_mrp_raw:
            row_data.extend(["", ""])  # Add empty normalized data and variant name if no data
        else:
            try:
                # Parse the JSON-like string in "Pack Size MRP" column
                pack_data = json.loads(pack_size_mrp_raw.replace("'", '"'))  # JSON parsing
                normalized_data = normalize_pack_data(pack_data)

                # Extract distinct flavors for the "Variant Name" column
                unique_flavors = {item.get('flavor', '') for item in pack_data}
                variant_name = ', '.join(filter(None, unique_flavors))  # Join unique flavors as a single string

                # Add normalized data and variant name to the row
                row_data.extend([json.dumps(normalized_data, indent=4), variant_name])

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in row {row}: {e}")
                row_data.extend(["", ""])  # Add empty normalized data and variant name in case of error

        # Add the row to the new sheet
        new_sheet.append(row_data)

    # Save the new workbook
    new_file_path = file_path.replace(".xlsx", "file.xlsx")
    new_wb.save(new_file_path)
    print(f"All rows processed successfully and new workbook saved at {new_file_path}")


# Call the function with the input file path
process_excel("/home/vedant/DataScraper/Web_scraping/gpt/vitalcare_Filled.xlsx")
