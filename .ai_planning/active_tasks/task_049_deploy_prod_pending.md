# Task 049: Deploy Production - PENDING

> **Trạng thái:** 🟡 PENDING  
> **Ngày tạo:** 2026-01-27  
> **Ưu tiên:** HIGH  
> **Loại:** Deployment

---

## 🎯 Mục tiêu
Deploy code mới lên Production server để fix lỗi `INTERNAL_KB_EMPTY`.

## 🐛 Vấn đề hiện tại
- **Prod** trả về `INTERNAL_KB_EMPTY` cho các thuốc như Ambroxol, Anaferon
- **Dev** hoạt động tốt với `INTERNAL_KB_TDV` response
- **Nguyên nhân:** Code mới đã push Git nhưng chưa deploy lên Prod

## 📋 Checklist Deploy

### Cách 1: Fast Deploy (Khuyến nghị - chỉ Python code)
```bash
# SSH vào server
ssh root@10.14.190.28

# Vào folder prod
cd /root/workspace/drug_icd_mapping/fastapi-medical-app

# Pull code mới
git pull origin main

# Restart container (không rebuild)
docker restart drug_icd_mapping_prod_web_1

# Verify health
curl http://localhost:8000/api/v1/health
```

### Cách 2: Full Deploy (Nếu thay đổi requirements)
```bash
ssh root@10.14.190.28
cd /root/workspace/drug_icd_mapping/fastapi-medical-app
./scripts/promote_to_prod.sh
```

## ✅ Verification sau deploy
```bash
# Test API consult_integrated
curl -X POST http://localhost:8000/api/v1/consult_integrated \
  -H "Content-Type: application/json" \
  -d '{
    "icd_code": "J42",
    "items": [
      {"id": "1", "name": "Ambroxol (Drenoxol)"},
      {"id": "2", "name": "Anaferon"}
    ]
  }'
```

**Expected:** Phải trả về `INTERNAL_KB_TDV` hoặc có role/validity, KHÔNG phải `INTERNAL_KB_EMPTY`.

---

## 📝 Notes
- Commit đã push: `24f5cfb` - "docs: add detailed work log for 2026-01-27"
- Các file đã sửa theo WorkLog: `consultation_service.py`, `ai_consult_service.py`, `kb_fuzzy_match_service.py`

---
*Task created: 2026-01-27 17:10*
