# QA AUDIT REPORT

## 1. Current Audit Status: ⚠️ CONDITIONAL PASS

### Summary
Hệ thống **Drug Identification** hoạt động bước đầu nhưng chưa ổn định ở khâu Web Scraping. Code quality tốt, tuân thủ PEP8 và cấu trúc dự án rõ ràng. Tuy nhiên, phụ thuộc vào Google Search library miễn phí là rủi ro lớn.

## 2. Findings

### 🔴 Critical Issues (Must Fix)
1. **Dependency Risk:** `googlesearch-python` không đáng tin cậy cho production. Dễ bị Google ban IP server.
   - *Recommendation:* Chuyển sang SerpAPI hoặc quay lại tối ưu Internal Search + Caching.
2. **Review Process:** Cần thêm unit test cho `GoogleSearchService` mock response để tránh gọi thật khi chạy CI/CD.

### 🟡 Medium Issues
1. **Error Handling:** Khi `GoogleSearchService` lỗi, fallback sang internal search chưa được kiểm chứng kỹ (cần integration test).
2. **Performance:** Latency trung bình còn cao (~10s nếu phải fallback).

### 🟢 Good Points
1. **Security:** Không thấy hardcoded secrets. Crawler chạy trong container cô lập.
2. **Architecture:** Tách biệt rõ ràng Service, Crawler, và API layer.

## 3. Action Items
- [ ] @SeniorDev: Refactor `GoogleSearchService` để support SerpAPI (nếu được approve).
- [ ] @TestEngineer: Viết test case mô phỏng rate limit để verify fallback logic.