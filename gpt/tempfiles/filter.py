import pandas as pd
import openai

# Load the Excel file
file_path = '/home/vedant/ScrapData/scrap/Data/KapivaProduct.xlsx'
kapiva_data = pd.read_excel(file_path)

# Set up the OpenAI API key
openai.api_key = ' '

# Function to generate unique titles with GPT
def generate_unique_title(product_title, price, pack_size):
    prompt = f"Generate a unique, appealing e-commerce title for a product named '{product_title}' that includes price '{price}' INR and pack size '{pack_size}' without making it too lengthy."
    
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
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error generating title: {e}")
        return product_title  # fallback to original title if API fails


def make_titles_unique(df):
    # Sort data to keep first instance of each duplicate
    df = df.sort_values(by=['Title', 'Price', 'Pack Size MRP']).reset_index(drop=True)
    
    # Identify duplicate titles
    duplicates = df.duplicated(subset='Title', keep=False)
    
 
    df['Unique Title'] = df.apply(
        lambda row: generate_unique_title(row['Title'], row['Price'], row['Pack Size MRP']) 
        if duplicates[row.name] else row['Title'], axis=1)
    
    return df


unique_kapiva_data = make_titles_unique(kapiva_data)


output_path = 'KapivaProduct_UniqueTitles.xlsx'
unique_kapiva_data.to_excel(output_path, index=False)

print(f"Processed data saved to {output_path}")
