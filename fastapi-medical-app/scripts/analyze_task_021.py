import pandas as pd
import sys
import os

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 1000)

DATA_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\ketqua_thuoc_part_20260107_154800.csv"

def analyze_data():
    print("="*60)
    print("TASK 021 - DATA ANALYSIS & DEDUPLICATION PREVIEW")
    print("="*60)
    
    if not os.path.exists(DATA_PATH):
        print(f"❌ File not found: {DATA_PATH}")
        return

    try:
        # 1. Load Data
        print(f"Loading data from: {os.path.basename(DATA_PATH)}")
        df = pd.read_csv(DATA_PATH, on_bad_lines='skip') # Skip bad lines if any
        
        print(f"\n📊 Initial Statistics:")
        print(f"  - Total Rows: {len(df)}")
        print(f"  - Columns: {list(df.columns)}")
        
        # 2. Check Duplicates by SDK
        if 'so_dang_ky' in df.columns:
            # Normalize SDK (strip whitespace)
            df['so_dang_ky'] = df['so_dang_ky'].astype(str).str.strip()
            
            # Count unique SDKs
            unique_sdk = df['so_dang_ky'].nunique()
            duplicates = len(df) - unique_sdk
            
            print(f"\n🔍 Duplication Analysis (by SDK):")
            print(f"  - Unique SDKs: {unique_sdk}")
            print(f"  - Duplicate Rows to Remove: {duplicates}")
            
            # Show example duplicates
            dup_sdk = df[df.duplicated('so_dang_ky', keep=False)]
            if not dup_sdk.empty:
                print(f"\n📝 Example of Duplicated SDKs:")
                example_sdk = dup_sdk['so_dang_ky'].iloc[0]
                example_dups = dup_sdk[dup_sdk['so_dang_ky'] == example_sdk]
                print(example_dups[['so_dang_ky', 'ten_thuoc', 'url_nguon']].to_string(index=False))
            else:
                print("  - No duplicates found based on SDK.")
                
        # 3. Content Analysis
        print(f"\nContent Preview (First 3 rows):")
        # Select key columns to display
        display_cols = ['so_dang_ky', 'ten_thuoc', 'hoat_chat', 'noi_dung_dieu_tri']
        # Truncate long text
        preview_df = df[display_cols].copy()
        if 'noi_dung_dieu_tri' in preview_df.columns:
            preview_df['noi_dung_dieu_tri'] = preview_df['noi_dung_dieu_tri'].astype(str).str.slice(0, 50) + "..."
            
        print(preview_df.head(3).to_string())
        
        # 4. Recommendation
        print("\n" + "="*60)
        print("💡 RECOMMENDATION FOR TASK 021:")
        print(f"  - Clean & Deduplicate: Will remove ~{duplicates} rows.")
        print("  - Mapping Strategy:")
        print("    so_dang_ky -> drugs.so_dang_ky")
        print("    ten_thuoc -> drugs.ten_thuoc")
        print("    hoat_chat -> drugs.hoat_chat")
        print("    noi_dung_dieu_tri -> Extract to 'chi_dinh' & 'mo_ta'")
        print("    url_nguon -> drugs.source_urls")
        print("="*60)

    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

if __name__ == "__main__":
    analyze_data()
