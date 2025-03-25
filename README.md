# Web Scraping Workflow

This README explains how to scrape product data using the provided Python scripts in a multi-step workflow.

---

## 🎯 Prerequisites

1. Install Python (>=3.8).
2. Install required libraries:

    
bash
    pip install requests beautifulsoup4 pandas openpyxl


---

## 🛠️ Step 1: Extract Product Links

Run Productdatalink.py to extract product names and links from the website.

bash
python Productdatalink.py


## Step 2: Scrape Product Details

Next, use the output CSV from step 1 as input to scrap1.py to scrape detailed product data.

python scrap1.py

What it does:

Reads product links from product_links.csv.

Visits each product page.

Extracts details like price, description, and ingredients.

Saves data to an Excel file (e.g., product_details.xlsx).

## Step 3: Categorize Products & Beefits generation

For the final step, you can generate category-based data using category_new.py.
```
python Category_Benefit_generator1.py
```
What it does:

Takes product_details.xlsx as input.

Categorizes products based on keywords (e.g., capsule, syrup, oil).

Saves a new categorized output file (e.g., categorized_products.xlsx).

Its Also generate the key benefits of product

## step 4: generate uniquie title 
```
    python Unique_title_creator.py
```
ITs generate to unique title for each prodoct it help to diffretiatie diffrent size of same product

## step 5: seperator empty filled package size
```
    seperater_empty_filled3.py
```
Its use to figure out empty package size product 

## step 6: 


### Notes

If any script fails or website structure changes, check the User-Agent in the headers and update it if needed.

For large datasets, consider adding delays between requests (time.sleep()) or handling pagination.