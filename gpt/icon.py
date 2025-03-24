import openai
import openpyxl
import time
import re
import json
from openpyxl import load_workbook

# Set your OpenAI API key
openai.api_key = ' '

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

# Function to get predictions from OpenAI
# Function to get predictions from OpenAI
def get_predictions(title, description):
    prompt = f"""
    Based on the product's title, description, and key ingredients, categorize the product into relevant categories from this list: {', '.join(categories)}.
    Provide exactly 5 key benefits with short and concise descriptions. All 5 benefits must be included and complete.

    Generate a list of icon ideas for Ayurveda products that emphasize the themes of nature, immunity, and personal well-being. For each benefit, provide:

    A brief description of the icon design.
    The meaning or significance of the icon in relation to Ayurveda.

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
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that classifies products and generates benefits."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        if not response['choices']:
            print("No choices returned. Empty response.")
            return None

        content = response['choices'][0]['message']['content'].strip()
        if not content:
            print("Received empty content. Skipping.")
            return None
        
        return content
    
    except Exception as e:  # Catch any general exception
        print(f"An error occurred: {e}")
        time.sleep(60)  # Wait before retrying in case of rate limit or server error
        return get_predictions(title, description)

# Function to extract categories and benefits from the GPT response
def extract_categories_and_benefits(text):
    try:
        # Extract categories from the response using regex or JSON parsing
        match = re.search(r'\"Categories\": \[([^\]]+)\]', text)
        if match:
            categories_string = match.group(1)  # Capture the contents inside the brackets
            # Convert the string to a list of categories
            categories = [cat.strip().strip('"') for cat in categories_string.split(',')]
        else:
            categories = []

        # Extract key benefits in JSON format using regex
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
    wb = load_workbook(file_path)
    sheet = wb.active
    
    # Setting headers for new columns
    sheet['Q1'] = 'Predicted Categories'
    sheet['R1'] = 'Showcase Benefits'

    for row in range(2, sheet.max_row + 1):
        title = sheet[f'B{row}'].value  
        description = sheet[f'M{row}'].value  
        key_benefits = sheet[f'I{row}'].value  

        # Log the data being processed
        print(f"Processing row {row}: ")

        if not title or not description or not key_benefits:
            print(f"Missing data in row {row}. Skipping.")
            continue

        predictions = get_predictions(title, description, key_benefits)
        
        if predictions:
            try:
                # Extract categories and benefits from the response text
                categories, benefits = extract_categories_and_benefits(predictions)

                # Write categories directly as a list
                if categories:
                    sheet[f'Q{row}'] = ', '.join(categories)  # Joining the categories as a comma-separated list

                # Convert benefits to JSON formatted string for saving
                benefits_json = json.dumps(benefits, indent=4)
                sheet[f'R{row}'] = benefits_json
                
            except Exception as e:
                print(f"Error processing row {row}: {e}")
                continue  # Skip this row and move to the next

    # Save the processed data back into the Excel file
    wb.save(file_path)
    print("All rows processed successfully and workbook saved.")

# Example usage
process_excel("/home/vedant/Pandas/HumdardProductData.xlsx")
