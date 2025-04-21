import google.generativeai as genai
import openpyxl
import time
import re
import json
from openpyxl import load_workbook

# Set your Gemini API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# List of predefined categories 
categories = [
    "ayurveda products", "vitamins & supplements", "pain relief", "multivitamins", "health & wellness", 
    "juices & vinegars", "women's health", "covid essentials", "ayurveda", "orthotics", "women care", 
    "women multivitamins", "hypertension products", "daily essentials", "personal care", "stomach care", 
    "calcium products", "omega", "adult diapers", "herbal supplements", "adult hygiene", "juices", 
    "health essentials", "ayurvedic medicine", "bone & joint health", "weight management", "elderly care", 
    "personal hygiene", "holistic wellness", "winter essentials", "masks", "herbal juices", 
    "bone & joint supplements", "hair & skin supplements", "heart supplements", "heart & bone health", 
    "immunity & wellness", "nutrition", "nutritional supplements", "food & nutrition", "cosmetics", 
    "skin care", "nutritional drinks", "fitness supplements", "feminine care", "healthy snacks", 
    "diabetes", "immunity boosters", "hair care", "sexual wellness", "eye care", "liver care", 
    "bone, joint & muscle care", "kidney care", "respiratory care", "homeopathy", "health care", 
    "malaria", "baby care", "oral care", "mindcare", "heart care", "derma care", "men grooming", 
    "pet care", "cardiac care", "cough & cold", "winter popular products", "headache & fever"
]

# Function to get predictions from Gemini
def get_predictions(title, description):
    prompt = f"""
     Based on the product's title, description, and key ingredients, categorize the product into relevant categories from this list: {', '.join(categories)}.
    Provide exactly 5 key benefits with short and concise descriptions. All 5 benefits must be included and complete.

    Generate a list of icon ideas for Ayurveda products that emphasize the themes of nature, immunity, and personal well-being. For each benefit, provide:

    A brief description of the icon design.
    The meaning or significance of the icon in relation to Ayurveda.
    
    For each key benefit generated, also provide an icon name related to it based on these categories:
    
    Nature-Related Icons: Herbal Extracts, Forest-Sourced, Earth-Friendly, Pure Water, Sun-Powered.
    Immunity-Boosting Icons: Strength & Vitality, Immunity Shield, Energizing, Anti-Oxidant Rich, Detoxifying.
    Personal Well-being Icons: Holistic Health, Self-Care, Relaxation, Personalized Care, Natural Healing.
    "Nature-Related Icons: Earth-Friendly dont give like this give only Earth-Friendly "

    Title: {title}
    Description: {description}

    Respond in strict format as:
    {{
        "Categories": ["Category1", "Category2"],
        "Key Benefits": [
            {{
                "heading": "Benefit Heading 1",
                "description": "A short benefit description (10-20 words).",
                "cardType": "medium",
                "icon": "Generated icon name based on the benefit"
            }},
            {{
                "heading": "Benefit Heading 2",
                "description": "A short benefit description (10-20 words).",
                "cardType": "medium",
                "icon": "Generated icon name based on the benefit"
            }},
            {{
                "heading": "Benefit Heading 3",
                "description": "A short benefit description (10-20 words).",
                "cardType": "medium",
                "icon": "Generated icon name based on the benefit"
            }},
            {{
                "heading": "Benefit Heading 4",
                "description": "A short benefit description (10-20 words).",
                "cardType": "medium",
                "icon": "Generated icon name based on the benefit"
            }},
            {{
                "heading": "Benefit Heading 5",
                "description": "A longer benefit description (20-30 words).",
                "cardType": "large",
                "icon": "Generated icon name based on the benefit"
            }}
        ]
    }}
    """

    try:
        # Configure the model
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Generate content
        response = model.generate_content(prompt)
        
        content = response.text.strip()
        if not content:
            print("Received empty content. Skipping.")
            return None
        
        return content
    
    except Exception as e:
        print(f"Gemini API error occurred: {e}")
        time.sleep(60)  # Wait before retrying
        return get_predictions(title, description)

# Function to extract categories and benefits from the Gemini response
def extract_categories_and_benefits(text):
    try:
        # Try parsing as JSON first (cleaner approach)
        try:
            json_data = json.loads(text)
            categories = json_data.get('Categories', [])
            benefits = json_data.get('Key Benefits', [])
            return categories, benefits
        except json.JSONDecodeError:
            # Fall back to regex if JSON parsing fails
            categories_match = re.search(r'\"Categories\": \[([^\]]+)\]', text)
            categories = [cat.strip().strip('"') for cat in categories_match.group(1).split(',')] if categories_match else []

            benefits_match = re.findall(r'\{\s*"heading":\s*"([^"]+)",\s*"description":\s*"([^"]+)",\s*"cardType":\s*"([^"]+)",\s*"icon":\s*"([^"]+)"\s*\}', text)
            benefits = [
                {
                    "heading": heading,
                    "description": description,
                    "cardType": cardType,
                    "icon": icon
                }
                for heading, description, cardType, icon in benefits_match
            ]

            return categories, benefits

    except Exception as e:
        print(f"Error extracting categories and benefits: {e}")
        return [], []

# Function to process the Excel file and update with predictions
def process_excel(file_path):
    # Determine output path (new file instead of overwriting)
    output_path = file_path.replace('.xlsx', '_with_categoriesBenefits.xlsx')
    
    print(f"Loading workbook from: {file_path}")
    print(f"Will save results to: {output_path}")
    
    # Load workbook using pandas for better column handling
    import pandas as pd
    df = pd.read_excel(file_path)
    
    # Print existing columns to verify
    print("Found columns in input file:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1}. {col}")
    
    # Check for important columns
    important_columns = ['Images', 'Pack Quantity', 'Content Quantity', 'Content Unit']
    for col in important_columns:
        if col in df.columns:
            print(f"✓ Found {col} column")
        else:
            print(f"⚠️ Warning: {col} column not found!")
    
    # Add new columns for categories and benefits
    df['Predicted Categories'] = ""
    df['Showcase Benefits'] = ""
    
    # Track progress
    total_rows = len(df)
    processed = 0
    successful = 0
    skipped = 0
    errors = 0

    # Process each row
    for index, row in df.iterrows():
        row_num = index + 2  # +2 because Excel rows start at 1 and we're skipping header
        try:
            title = row.get('Product Name', '')
            description = row.get('Product Description HTML', '')

            print(f"Processing row {row_num}/{total_rows+1}: {title[:30]}...")
            processed += 1

            # Skip rows with missing data
            if not title or not description:
                print(f"  Missing data in row {row_num}. Skipping.")
                skipped += 1
                continue

            # Generate predictions
            predictions = get_predictions(title, description)
            
            if predictions:
                try:
                    # Extract categories and benefits
                    categories, benefits = extract_categories_and_benefits(predictions)

                    # Save categories
                    if categories:
                        df.at[index, 'Predicted Categories'] = ', '.join(categories)
                        print(f"  Categories: {', '.join(categories[:3])}...")

                    # Save benefits
                    benefits_json = json.dumps(benefits, indent=4)
                    df.at[index, 'Showcase Benefits'] = benefits_json
                    print(f"  Added {len(benefits)} benefits")
                    successful += 1
                    
                except Exception as e:
                    print(f"  Error processing row {row_num}: {e}")
                    errors += 1
                    continue
            
            # Save checkpoint after every 10 rows
            if processed % 10 == 0:
                df.to_excel(output_path, index=False)
                print(f"Saved progress after {processed}/{total_rows} rows...")
            
            # Add a small delay to avoid API rate limits
            time.sleep(2)

        except Exception as e:
            print(f"Unexpected error on row {row_num}: {e}")
            errors += 1
    
    # Save final results
    df.to_excel(output_path, index=False)
    
    # Verify all columns were preserved
    verification_df = pd.read_excel(output_path)
    print("\nColumns in output file:")
    for i, col in enumerate(verification_df.columns):
        print(f"  {i+1}. {col}")
        
    # Check if important columns were preserved
    for col in important_columns:
        if col in verification_df.columns:
            print(f"✓ {col} column preserved successfully")
        else:
            print(f"✗ ERROR: {col} column was lost!")
    
    # Print summary
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Total rows: {total_rows}")
    print(f"Successfully processed: {successful}")
    print(f"Skipped (missing data): {skipped}")
    print(f"Errors: {errors}")
    if total_rows > 0:
        print(f"Success rate: {successful/total_rows*100:.2f}%")
    print("="*50)
    print(f"Results saved to: {output_path}")
    
    return output_path

# Run the processor
if __name__ == "__main__":
    input_file = "E:\\AYURYUJ\\Web_scraping\\scrap\\vital_care_scrapped.xlsx"
    output_path = "E:\\AYURYUJ\\Web_scraping\\output\\vital_care_categoryBenefits.xlsx"
    output_file = process_excel(input_file)
    print(f"Processing complete. Output file: {output_file}")