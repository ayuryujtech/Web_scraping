import pandas as pd
import openai

# Load the Excel file
file_path = r'E:\AYURYUJ\Web_scraping\scrap\all_zandu_scrapped_categories_benefits.xlsx'
kapiva_data = pd.read_excel(file_path)

# Set up the OpenAI API key
openai.api_key = ''

# Function to generate unique titles with GPT using benefits
def generate_unique_title(product_title, benefits):
    prompt = (
        f"Generate a unique and appealing e-commerce title for a product named '{product_title}' that includes "
        f"the benefits '{benefits}'. Ensure the title is not too lengthy and only adds 3-5 extra words related to the benefits. aslo insure that new word are add in back of title not in fornt and make it sutable with old title "
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant generating distinct product titles for e-commerce."},
                {"role": "user", "content": prompt}
            ],
        
            temperature=0.7
        )
        # Strip any leading/trailing quotation marks added by GPT
        generated_title = response.choices[0].message['content'].strip()
        return generated_title.strip('"')  # Remove quotes around the title
    except Exception as e:
        print(f"Error generating title: {e}")
        return product_title  # fallback to original title if API fails

# Function to make only duplicate titles unique
def make_titles_unique(df):
    # Check column names first
    print("Available columns:", df.columns.tolist())
    
    # Use the correct column name (probably 'Product Name' instead of 'Title')
    df = df.sort_values(by=['Product Name', 'Showcase Benefits']).reset_index(drop=True)
    
    # Identify duplicate titles
    duplicates = df.duplicated(subset='Product Name', keep=False)
    
    # Apply transformation to make only duplicate titles unique
    df['Unique Title'] = df.apply(
        lambda row: generate_unique_title(row['Product Name'], row['Showcase Benefits']) 
        if duplicates[row.name] else row['Product Name'], axis=1)
    
    return df

# Apply the function to make titles unique
unique_kapiva_data = make_titles_unique(kapiva_data)

# Save the modified data back to a new Excel file
output_path = 'all_zandu2_unique.xlsx'
unique_kapiva_data.to_excel(output_path, index=False)

print(f"Processed data saved to {output_path}")
