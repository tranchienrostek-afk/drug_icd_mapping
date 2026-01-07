# EDIT-TEST LOOP WORKFLOW (X MINS)

**Rule:** Không viết code implementation nếu chưa có failing test.

## STEP 1: RED (X mins)
- Tạo file test mới trong `tests/` dựa trên `test_template_tdd.py`.
- Định nghĩa Input/Output mong muốn.
- Chạy test -> BẮT BUỘC PHẢI FAIL.

## STEP 2: GREEN (X mins)
- Viết code tối thiểu (Minimal code) trong `app/` để pass test.
- Không tối ưu, không over-engineer.
- Chạy lại test -> PHẢI PASS.

## STEP 3: REFACTOR (X mins)
- Clean code, thêm type hints, tách hàm nếu cần.
- Chạy lại test lần cuối để đảm bảo không break logic.
- Commit code.