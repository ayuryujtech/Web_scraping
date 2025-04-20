import pandas as pd
import os

def remove_duplicates(input_file, output_file=None):
    # Define output file name if not provided
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_no_duplicates{ext}"
    
    print(f"Reading file: {input_file}")
    
    # Read the Excel file
    try:
        df = pd.read_excel(input_file)
        initial_count = len(df)
        print(f"Initial row count: {initial_count}")
        
        # Add an index column to track original positions
        df['original_index'] = range(len(df))
        
        # MODIFIED: Check only the Link column for duplicates
        duplicate_mask = df.duplicated(subset=['Link'], keep='first')
        
        # Get the duplicate rows for logging/review
        duplicate_rows = df[duplicate_mask].copy()
        
        # Keep only the non-duplicates
        df_no_duplicates = df[~duplicate_mask].copy()
        
        # Report results
        removed_count = initial_count - len(df_no_duplicates)
        print(f"Removed {removed_count} duplicate links")
        print(f"Final row count: {len(df_no_duplicates)}")
        
        # Save duplicates to a separate file
        if len(duplicate_rows) > 0:
            duplicates_file = f"{os.path.splitext(output_file)[0]}_duplicates{os.path.splitext(output_file)[1]}"
            duplicate_rows.to_excel(duplicates_file, index=False)
            print(f"Duplicate rows saved to: {duplicates_file}")
            
            # Print the first few duplicates
            print("\nSample of removed duplicates:")
            pd_options = pd.get_option('display.max_columns')
            pd.set_option('display.max_columns', None)
            print(duplicate_rows.head(3))
            pd.set_option('display.max_columns', pd_options)
        
        # Remove the tracking column before saving
        df_no_duplicates = df_no_duplicates.drop('original_index', axis=1)
        
        # Save to new file
        df_no_duplicates.to_excel(output_file, index=False)
        print(f"Cleaned data saved to: {output_file}")
        
        return True
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

# File path
input_file = r"E:\AYURYUJ\Web_scraping\scrap\all_zandu.xlsx"
output_file = r"E:\AYURYUJ\Web_scraping\scrap\all_zandu_clean.xlsx"

# Run the function
remove_duplicates(input_file, output_file)