# BUSINESS ANALYST KNOWLEDGE BASE

## 1. Drug Identification Rules
[RULE_01] - [Normalization] -> Remove usage form (e.g. "viên nén", "chai") but KEEP dosage (e.g. "500mg").
[RULE_02] - [Validation] -> A drug is considered VERIFIED if and only if it has a valid SDK (Format: VN-xxxxx-xx or VD-xxxxx-xx).
[RULE_03] - [Conflict] -> If internal DB and Web Scrape conflict, trust Internal DB (if verified).
[RULE_04] - [Mapping] -> 1 Drug can map to multiple ingredients (e.g. Panadol Extra -> Paracetamol + Caffeine).

## 2. Data Schema Requirements
**Mandatory Fields:**
- `ten_thuoc` (Standardized Name)
- `so_dang_ky` (Registration Number)
- `hoat_chat` (Active Ingredients)

**Optional Fields:**
- `nha_san_xuat` (Manufacturer)
- `quy_cach_dong_goi` (Packaging)
- `chi_dinh` (Indications)

## 3. Validated Sample Pairs
| Input | Normalized | Output (SDK) | Status |
|---|---|---|---|
| "Pana 500" | "panadol 500mg" | VN-12345-67 | APPROVED |
| "Symbicort" | "symbicort" | VN-17730-14 | APPROVED |
| "Kháng sinh A" | "khang sinh a" | None | REJECTED (Ambiguous) |