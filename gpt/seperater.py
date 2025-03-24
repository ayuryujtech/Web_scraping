import pandas as pd


file_path = '/home/vedant/ScrapData/gpt/DataUnique/DrVaidyaProduct_UniqueTitles.xlsx'
data = pd.read_excel(file_path)


empty_mrp_df = data[data['Pack Size MRP'] == "[]"]  
filled_mrp_df = data[data['Pack Size MRP'] != "[]"]  


empty_mrp_file_path = 'DrVaidya_Empty.xlsx'
filled_mrp_file_path = 'DrVaidya_Filled.xlsx'


empty_mrp_df.to_excel(empty_mrp_file_path, index=False)
filled_mrp_df.to_excel(filled_mrp_file_path, index=False)

print("Files saved successfully!")

