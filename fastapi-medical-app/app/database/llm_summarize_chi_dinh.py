import argparse
import time
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# =========================
# CONFIG
# =========================
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
INPUT_CSV = "drug_data_final.csv"
OUTPUT_CSV = "drug_data_with_chi_dinh_tom_tat.csv"
CHI_DINH_COLUMN = "chi_dinh"

SYSTEM_PROMPT = """Hãy tóm tắt chỉ định điều trị của thuốc sau thành danh sách ngắn các bệnh hoặc triệu chứng.
Yêu cầu:
- Tiếng Việt
- Mỗi mục 1–7 từ
- Ngăn cách bằng dấu phẩy
- Không giải thích
- Không thêm thông tin
"""

# =========================
# LOAD MODEL
# =========================
def load_model():
    print("🔹 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

    print("🔹 Loading model (CPU)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        device_map="cpu",
        trust_remote_code=True
    )
    model.eval()
    return tokenizer, model


# =========================
# LLM SUMMARIZE
# =========================
def summarize_chi_dinh(tokenizer, model, chi_dinh_text: str) -> str:
    if not isinstance(chi_dinh_text, str) or chi_dinh_text.strip() == "":
        return ""

    prompt = f"""
{SYSTEM_PROMPT}

Chỉ định:
{chi_dinh_text}
"""

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    )

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=False,
            temperature=0.2
        )

    result = tokenizer.decode(output[0], skip_special_tokens=True)

    # chỉ lấy phần model sinh ra
    result = result.split("Chỉ định:")[-1].strip()
    return result


# =========================
# MAIN PIPELINE
# =========================
def main(limit: int):
    print("🔹 Reading CSV...")
    df = pd.read_csv(INPUT_CSV)

    if CHI_DINH_COLUMN not in df.columns:
        raise ValueError(f"Không tìm thấy cột `{CHI_DINH_COLUMN}` trong CSV")

    if limit > 0:
        df = df.head(limit)

    tokenizer, model = load_model()

    summarized_results = []

    start_time = time.time()

    for idx, row in df.iterrows():
        chi_dinh = row.get(CHI_DINH_COLUMN, "")
        summary = summarize_chi_dinh(tokenizer, model, chi_dinh)
        summarized_results.append(summary)

        if (idx + 1) % 10 == 0:
            elapsed = time.time() - start_time
            print(f"⏳ Đã xử lý {idx + 1} dòng | {elapsed/60:.2f} phút")

    df["chi_dinh_tom_tat"] = summarized_results

    print("💾 Writing output CSV...")
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    total_time = time.time() - start_time
    print(f"✅ Hoàn thành | Tổng thời gian: {total_time/3600:.2f} giờ")


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Số dòng cần xử lý (test). Dùng 0 để quét toàn bộ."
    )
    args = parser.parse_args()

    main(args.limit)
