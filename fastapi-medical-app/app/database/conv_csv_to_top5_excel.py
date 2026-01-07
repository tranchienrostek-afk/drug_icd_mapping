import pandas as pd
df = pd.read_csv("drug_data_final.csv", encoding = "utf-8-sig", low_memory=False)
df_10 = df.head(10)
df_10.to_excel("10_drugs.xlsx", index=False)