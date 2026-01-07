import pandas as pd
import re
from unidecode import unidecode
from typing import List

# =========================
# CONFIG
# =========================
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_CSV = BASE_DIR / "drug_data_final.csv"
OUTPUT_EXCEL = BASE_DIR / "output.xlsx"



# SỐ DÒNG MUỐN XỬ LÝ
# - test: 20
# - full: None
MAX_ROWS = 20


# =========================
# TEXT NORMALIZATION
# =========================
def normalize_text(text: str) -> str:
    if pd.isna(text) or not text:
        return ""
    text = text.lower()
    text = unidecode(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================
# CẮT PHẦN CHỈ ĐỊNH
# =========================
STOP_PATTERNS = [
    r"\bla thuoc\b",
    r"\bco che\b",
    r"\bhap thu\b",
    r"\bduoc dong hoc\b",
    r"\bchuyen hoa\b",
    r"\bthai tru\b",
    r"\bdu lieu thuc nghiem\b"
]

def extract_indication_section(text: str) -> str:
    text = normalize_text(text)
    for pattern in STOP_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return text[:match.start()].strip()
    return text


# =========================
# LEXICON – CÓ THỂ MỞ RỘNG
# =========================
KEY_TERMS = [
    "sot",
    "sot sau tiem chung",
    "dau dau",
    "dau rang",
    "dau hong",
    "dau co",
    "dau co bap",
    "dau khop",
    "dau bung",
    "dau nhuc",
    "cam lanh",
    "cum",
    "viem",
    "viem hong",
    "viem mui",
    "viem xoang"
]


def extract_terms(text: str, vocab: List[str]) -> List[str]:
    found = []
    for term in vocab:
        if re.search(r"\b" + re.escape(term) + r"\b", text):
            found.append(term)
    return found


# =========================
# CORE: TÓM TẮT CHỈ ĐỊNH
# =========================
def summarize_indication(raw_text: str) -> str:
    section = extract_indication_section(raw_text)
    terms = extract_terms(section, KEY_TERMS)
    return ", ".join(sorted(set(terms)))


# =========================
# MAIN PIPELINE
# =========================
def main():
    print("🔹 Reading CSV...")
    df = pd.read_csv(INPUT_CSV)

    if MAX_ROWS:
        df = df.head(MAX_ROWS)

    output_rows = []

    print(f"🔹 Processing {len(df)} drugs...")

    for _, row in df.iterrows():
        chi_dinh_raw = row.get("chi_dinh", "")

        summarized = summarize_indication(chi_dinh_raw)

        output_rows.append({
            "ten_thuoc": row.get("ten_thuoc"),
            "so_dang_ky": row.get("so_dang_ky"),
            "chi_dinh_tom_tat": summarized,
            "hoat_chat": row.get("hoat_chat"),
            "slug": row.get("slug"),
            "ham_luong_thuoc": row.get("ham_luong_thuoc"),
        })

    output_df = pd.DataFrame(output_rows)

    print("🔹 Writing Excel...")
    output_df.to_excel(OUTPUT_EXCEL, index=False)

    print("✅ DONE")
    print(f"➡ Output file: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()