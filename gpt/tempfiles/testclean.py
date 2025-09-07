import re
import pandas as pd
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
clean_unique_title('Dhootapapeshwar Amlapitta Mishran Suspension | For Hyperacidity, Nausea & Vomiting')
print(clean_unique_title('Dhootapapeshwar Amlapitta Mishran Suspension | For Hyperacidity, Nausea & Vomiting'))    
    