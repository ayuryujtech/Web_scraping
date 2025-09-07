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
    cleaned = re.sub(r'[,:;"\'\[\]{}]', '', |, cleaned)  # Remove punctuation but keep ()
    cleaned = re.sub(r'[®™©]', '', cleaned)  # Remove trademark symbols
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Replace multiple spaces with single space
    cleaned = re.sub(r'-+', '-', cleaned)  # Replace multiple hyphens with single hyphen
    cleaned = re.sub(r'\s*\(\s*', ' (', cleaned)  # Clean space before (
    cleaned = re.sub(r'\s*\)\s*', ') ', cleaned)  # Clean space after )
    cleaned = cleaned.strip()
    cleaned = re.sub(r'\s*-\s*', '-', cleaned)
    return cleaned

def process_normalized_file(input_path):
    try:
        print(f"Reading file: {input_path}")
        df = pd.read_excel(input_path)

        # Clean Unique Title
        if 'Unique Title' in df.columns:
            df['Unique Title'] = df['Unique Title'].apply(clean_unique_title)

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