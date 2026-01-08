# WORKFLOW RULES (QUY TẮC QUY TRÌNH LÀM VIỆC)

## 1. Definition of Done (Định nghĩa Hoàn thành)
Một task chỉ được coi là hoàn thành khi:
- Code đã chạy đúng logic.
- Test case đã pass (Green).
- Đã tạo file báo cáo trong `.ai_reports/`.

## 2. Reporting Protocol (Giao thức Báo cáo) - MANDATORY
Sau khi hoàn thành bất kỳ Task hoặc Fix Bug nào, bạn BẮT BUỘC phải:
1.  Tạo file báo cáo mới trong `.ai_reports/YYYY-MM/` theo tên `YYYYMMDD_[TYPE]_[NAME].md`.
    - TYPE: `TASK` hoặc `FIX`.
    - NAME: Tên ngắn gọn (VD: `Init_DB`, `Staging_Logic`).
2.  Sử dụng template tại `.ai_reports/templates/report_template.md`.
3.  Điền chi tiết các thay đổi file và các lệnh đã chạy.

**Lưu ý:** Không cần hỏi xin phép để tạo báo cáo. Hãy tự động làm việc đó.