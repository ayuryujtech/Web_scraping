import pandas as pd
import openai

# Load the Excel file
file_path = '/home/vedant/DataScraper/Web_scraping/scrap/vitalCareProduct.xlsx'
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
            max_tokens=50,
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
    # Sort data to keep the first instance of each duplicate
    df = df.sort_values(by=['Title', 'Showcase Benefits']).reset_index(drop=True)
    
    # Identify duplicate titles
    duplicates = df.duplicated(subset='Title', keep=False)
    
    # Apply transformation to make only duplicate titles unique
    df['Unique Title'] = df.apply(
        lambda row: generate_unique_title(row['Title'], row['Showcase Benefits']) 
        if duplicates[row.name] else row['Title'], axis=1)
    
    return df

# Apply the function to make titles unique
unique_kapiva_data = make_titles_unique(kapiva_data)

# Save the modified data back to a new Excel file
output_path = 'vitalcareProduct_UniqueTitles.xlsx'
unique_kapiva_data.to_excel(output_path, index=False)

print(f"Processed data saved to {output_path}")
