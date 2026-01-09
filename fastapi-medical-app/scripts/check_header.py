import pandas as pd
import sys

FILE_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\datacore_thuocbietduoc\ketqua_thuoc_part_20260108_104310.csv"

try:
    df = pd.read_csv(FILE_PATH, nrows=1)
    print(df.columns.tolist())
except Exception as e:
    print(e)
