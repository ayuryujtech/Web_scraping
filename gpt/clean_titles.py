import pandas as pd
import re
import os
import json
from datetime import datetime

def clean_unique_title(title):
    """Clean special characters from unique titles while preserving parentheses"""
    if pd.isna(title):
        return title
    cleaned = str(title)
    cleaned = re.sub(r'[,:;"\'\[\]{}]', '', cleaned)  # Remove punctuation but keep ()
    cleaned = re.sub(r'[®™©]', '', cleaned)  # Remove trademark symbols
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Replace multiple spaces with single space
    cleaned = re.sub(r'-+', '-', cleaned)  # Replace multiple hyphens with single hyphen
    cleaned = re.sub(r'\s*\(\s*', ' (', cleaned)  # Clean space before (
    cleaned = re.sub(r'\s*\)\s*', ') ', cleaned)  # Clean space after )
    cleaned = cleaned.strip()
    cleaned = re.sub(r'\s*-\s*', '-', cleaned)
    return cleaned

def clean_pack_size_mrp(pack_size_mrp):
    """Remove first item from Pack Size MRP if multiple items exist"""
    if pd.isna(pack_size_mrp):
        return pack_size_mrp
    try:
        if isinstance(pack_size_mrp, str):
            try:
                data = json.loads(pack_size_mrp)
            except Exception:
                data = json.loads(pack_size_mrp.replace("'", '"'))
        else:
            data = pack_size_mrp
        if isinstance(data, list) and len(data) > 1:
            return json.dumps(data[1:], ensure_ascii=False)
        return pack_size_mrp
    except Exception as e:
        print(f"Error processing Pack Size MRP: {e}")
        return pack_size_mrp

def clean_pack_size_mrp_text(pack_size_mrp):
    """Remove text before and including 'of' in Pack Size MRP - only when it contains exactly 1 item"""
    if pd.isna(pack_size_mrp):
        return pack_size_mrp
    try:
        # Function to clean text pattern like "1 Bottle of 200 ml Oil" to "200 ml Oil"
        def clean_text(text):
            if " of " in text:
                parts = text.split(" of ", 1)
                if len(parts) > 1:
                    return parts[1].strip()
            # Also try to match pattern like "1 Bottle" or "2 Packets" etc.
            match = re.match(r'^\d+\s+\w+\s+(.*?)$', text)
            if match:
                return match.group(1).strip()
            return text
        
        # Check if it's a string or already parsed data
        if isinstance(pack_size_mrp, str):
            try:
                # First try to parse as JSON
                data = json.loads(pack_size_mrp)
                is_json = True
            except Exception:
                try:
                    # Try with single quotes replaced
                    data = json.loads(pack_size_mrp.replace("'", '"'))
                    is_json = True
                except Exception:
                    # Not a JSON string, handle as regular text
                    is_json = False
                    # Process text directly - only for single items
                    # No need to check item count for plain text
                    return clean_text(pack_size_mrp)
        else:
            data = pack_size_mrp
            is_json = True
            
        if is_json:
            # ONLY process if the data contains exactly 1 item in the list
            if isinstance(data, list) and len(data) == 1:
                item = data[0]
                # Check if the item has a 'size' key (don't process multi-item structures)
                if isinstance(item, dict) and "size" in item:
                    # Get the size text
                    size_text = item["size"]
                    # Only clean if it contains "of" pattern
                    if " of " in size_text:
                        item["size"] = clean_text(size_text)
                elif isinstance(item, dict) and "text" in item:
                    # Handle text field format
                    item["text"] = clean_text(item["text"])
                
                # Return processed JSON data
                return json.dumps(data, ensure_ascii=False) if isinstance(pack_size_mrp, str) else data
            elif isinstance(data, dict) and "text" in data:
                # Single dictionary object is considered one item
                data["text"] = clean_text(data["text"])
                
                # Return processed JSON data
                return json.dumps(data, ensure_ascii=False) if isinstance(pack_size_mrp, str) else data
            else:
                # More than 1 item or not the right structure - don't process
                return pack_size_mrp
        
        # If no processing was done, return original
        return pack_size_mrp
        
    except Exception as e:
        print(f"Error processing Pack Size MRP text: {e}")
        return pack_size_mrp

def create_log_file():
    """Create a log file for discrepancies"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"discrepancies_log_{timestamp}.txt"
    return log_path

def clean_normalize_data(normalize_data, pack_size_mrp=None, product_id=None, log_file=None):
    """
    Remove first item if quantity=1 and set next item as primary.
    Also check if normalized data matches Pack Size MRP and log discrepancies.
    """
    if pd.isna(normalize_data) or normalize_data == '':
        return normalize_data
    
    try:
        # Debug: Show original input
        print(f"\nOriginal input type: {type(normalize_data)}")
        print(f"Original input: {normalize_data}")
        
        # Handle different input types
        if isinstance(normalize_data, str):
            try:
                # First try direct JSON parse
                data = json.loads(normalize_data)
            except json.JSONDecodeError:
                try:
                    # Try fixing common JSON issues
                    fixed = normalize_data.replace("'", '"').replace("None", "null")
                    data = json.loads(fixed)
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")
                    return normalize_data
        elif isinstance(normalize_data, (list, dict)):
            data = normalize_data
        else:
            print(f"Unexpected data type: {type(normalize_data)}")
            return normalize_data

        # Check if we have Pack Size MRP data to compare
        if pack_size_mrp is not None and log_file is not None and product_id is not None:
            try:
                # Parse Pack Size MRP data if it's a string
                if isinstance(pack_size_mrp, str) and pack_size_mrp and pack_size_mrp.strip():
                    try:
                        mrp_data = json.loads(pack_size_mrp)
                    except:
                        try:
                            mrp_data = json.loads(pack_size_mrp.replace("'", '"'))
                        except:
                            mrp_data = pack_size_mrp
                else:
                    mrp_data = pack_size_mrp
                
                # Extract sizes from both datasets for comparison
                norm_sizes = []
                mrp_sizes = []
                
                # Extract sizes from Normalized Data
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "size" in item:
                            # Extract size value
                            size_info = item.get("size", {})
                            if isinstance(size_info, dict) and "value" in size_info:
                                value = size_info.get("value", "")
                                unit = size_info.get("unit", "")
                                norm_sizes.append(f"{value} {unit}".strip())
                
                # Extract sizes from Pack Size MRP
                if isinstance(mrp_data, list):
                    for item in mrp_data:
                        if isinstance(item, dict) and "size" in item:
                            mrp_sizes.append(item["size"])
                
                # Compare the sizes and log discrepancies
                if norm_sizes and mrp_sizes:
                    # Check if any size in normalized data doesn't match pack size mrp
                    mismatch = False
                    
                    # Simple check: number of sizes don't match
                    if len(norm_sizes) != len(mrp_sizes):
                        mismatch = True
                    
                    # Check for content differences
                    norm_set = set(norm_sizes)
                    mrp_set = set(mrp_sizes)
                    if norm_set != mrp_set:
                        mismatch = True
                    
                    if mismatch:
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"Product ID: {product_id}\n")
                            f.write(f"Normalized Data Sizes: {norm_sizes}\n")
                            f.write(f"Pack Size MRP Sizes: {mrp_sizes}\n")
                            f.write("-" * 50 + "\n")
            except Exception as e:
                # If comparison fails, log the error
                if log_file:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"Error comparing data for Product ID {product_id}: {str(e)}\n")
                        f.write("-" * 50 + "\n")

        # Ensure we have a list
        if not isinstance(data, list):
            print("Data is not a list - no processing needed")
            return normalize_data

        # Check if we have enough items
        if len(data) < 2:
            print("List has less than 2 items - no processing needed")
            return normalize_data

        # Get first item's quantity
        first_item = data[0]
        quantity = str(first_item.get("size", {}).get("quantity", "")).strip()
        print(f"First item quantity: {quantity} (type: {type(quantity)})")

        # Process if quantity is "1"
        if quantity == "1":
            print("Processing: Found quantity=1")
            # Remove first item
            new_data = data[1:]
            # Set first remaining item as primary
            if new_data:
                new_data[0]["type"] = "primary"
                # Set others as secondary
                for item in new_data[1:]:
                    item["type"] = "secondary"
            
            # Convert back to string if input was string
            if isinstance(normalize_data, str):
                return json.dumps(new_data, indent=4, ensure_ascii=False)
            return new_data
        
        print("No processing needed - quantity not '1'")
        return normalize_data

    except Exception as e:
        print(f"Error in clean_normalize_data: {str(e)}")
        return normalize_data

def process_normalized_with_pack_size(row):
    """Process Normalized Data using information from Pack Size MRP"""
    normalized_data = row.get('Normalized Data')
    pack_size_mrp = row.get('Pack Size MRP')
    
    if pd.isna(normalized_data) or pd.isna(pack_size_mrp):
        return normalized_data
        
    try:
        # Parse both columns
        if isinstance(normalized_data, str):
            try:
                norm_data = json.loads(normalized_data)
            except:
                norm_data = json.loads(normalized_data.replace("'", '"').replace("None", "null"))
        else:
            norm_data = normalized_data
            
        if isinstance(pack_size_mrp, str):
            try:
                mrp_data = json.loads(pack_size_mrp)
            except:
                mrp_data = json.loads(pack_size_mrp.replace("'", '"'))
        else:
            mrp_data = pack_size_mrp
            
        # Check if both are valid lists
        if not isinstance(norm_data, list) or not isinstance(mrp_data, list):
            return normalized_data
            
        # First apply the normal cleaning
        cleaned_norm_data = clean_normalize_data(normalized_data)
        
        # Now parse again if it was returned as string
        if isinstance(cleaned_norm_data, str):
            try:
                norm_data = json.loads(cleaned_norm_data)
            except:
                norm_data = json.loads(cleaned_norm_data.replace("'", '"').replace("None", "null"))
        else:
            norm_data = cleaned_norm_data
            
        # Find the primary item in normalized data
        primary_item = None
        for item in norm_data:
            if isinstance(item, dict) and item.get("type") == "primary":
                primary_item = item
                break
                
        if primary_item and isinstance(mrp_data, list) and len(mrp_data) > 0:
            # Get the size from Pack Size MRP first item
            if isinstance(mrp_data[0], dict):
                mrp_size = mrp_data[0].get("size", "")
                
                # Update the primary item's size in normalized data
                if mrp_size and "size" in primary_item and isinstance(primary_item["size"], dict):
                    # Parse the mrp_size to extract quantity and unit
                    # Example: "10 strips" -> quantity="10", unit="strips"
                    size_parts = mrp_size.split(" ", 1)
                    if len(size_parts) == 2:
                        quantity, unit = size_parts
                        # Update the normalized data
                        primary_item["size"]["quantity"] = quantity
                        primary_item["size"]["unit"] = unit
                        
                        # Format the product name according to the requested pattern
                       
        # Return the updated data in the same format as input
        if isinstance(normalized_data, str):
            return json.dumps(norm_data, indent=4, ensure_ascii=False)
        return norm_data
            
    except Exception as e:
        print(f"Error processing normalized data with pack size: {e}")
        return normalized_data

def process_normalized_file(input_path):
    try:
        print(f"Reading file: {input_path}")
        df = pd.read_excel(input_path)

        # Clean Unique Title
        if 'Unique Title' in df.columns:
            df['Unique Title'] = df['Unique Title'].apply(clean_unique_title)

        # Clean Pack Size MRP - First remove items
        if 'Pack Size MRP' in df.columns:
            df['Pack Size MRP'] = df['Pack Size MRP'].apply(clean_pack_size_mrp)
            # Then clean text by removing content before "of" - only for entries with 1 item
            df['Pack Size MRP'] = df['Pack Size MRP'].apply(clean_pack_size_mrp_text)

        # Process Normalized Data based on Pack Size MRP if both columns exist
        if 'Normalized Data' in df.columns and 'Pack Size MRP' in df.columns:
            df['Normalized Data'] = df.apply(process_normalized_with_pack_size, axis=1)
        # Otherwise just clean the normalized data
        elif 'Normalized Data' in df.columns:
            df['Normalized Data'] = df['Normalized Data'].apply(clean_normalize_data)

        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.splitext(input_path)[0]
        output_path = f"{filename}cleaned{timestamp}.xlsx"
        df.to_excel(output_path, index=False)
        print(f"\nProcessing complete! File saved as: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

if __name__ == "__main__":
    input_file = "E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\test1.xlsx"
    if os.path.exists(input_file):
        process_normalized_file(input_file)
    else:
        print(f"Error: Input file not found at {input_file}")