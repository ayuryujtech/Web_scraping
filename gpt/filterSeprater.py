import pandas as pd


file_path = '/home/vedant/ScrapData/gpt/PatanjaliDivya_Filter_data.xlsx'
data = pd.read_excel(file_path)


empty_mrp_df = data[data['Normalized Data'] == "[]"]  
filled_mrp_df = data[data['Normalized Data'] != "[]"]  


empty_mrp_file_path = 'PatanjaliDivya_filter_Empty.xlsx'
filled_mrp_file_path = 'PatanjaliDivya_fitlter_Filled.xlsx'


empty_mrp_df.to_excel(empty_mrp_file_path, index=False)
filled_mrp_df.to_excel(filled_mrp_file_path, index=False)

print("Files saved successfully!")

