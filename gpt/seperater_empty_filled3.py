import pandas as pd


file_path = r"E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\zandu2\\zandu_scrapped_with_categoriesBenefits.xlsx"
data = pd.read_excel(file_path)


empty_mrp_df = data[data['Pack Size MRP'] == "[]"]  
filled_mrp_df = data[data['Pack Size MRP'] != "[]"]  


empty_mrp_file_path ="E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\zandu2\\zandu_empty.xlsx"
filled_mrp_file_path ="E:\\AYURYUJ\\Web_scraping\\all_excelFiles\\zandu2\\zandu_filled.xlsx"


empty_mrp_df.to_excel(empty_mrp_file_path, index=False)
filled_mrp_df.to_excel(filled_mrp_file_path, index=False)

print("Files saved successfully!")

