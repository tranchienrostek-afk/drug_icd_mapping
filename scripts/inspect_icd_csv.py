import pandas as pd

CSV_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\to_database\icd_data.csv"

try:
    df = pd.read_csv(CSV_PATH, header=None, nrows=3)
    print("--- Row 0 ---")
    for i, val in enumerate(df.iloc[0]):
        print(f"Col {i}: {val}")
    print("\n--- Row 1 ---")
    for i, val in enumerate(df.iloc[1]):
        print(f"Col {i}: {val}")
except Exception as e:
    print(e)
