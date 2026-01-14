# Báo cáo Trạng thái Gỡ lỗi BUG-010 (Ngày 12/01/2026)

## Tổng quan
Mục tiêu phiên làm việc là khắc phục lỗi endpoint `/api/v1/drugs/agent-search` trả về kết quả rỗng. Quá trình gỡ lỗi đã đi sâu vào các vấn đề về cấu hình môi trường, tích hợp Azure OpenAI và sự tương thích của thư viện `mcp-agent`.

## Trạng thái Hiện tại
**TÌNH TRẠNG: BLOCKED (Tạm dừng)**
*   **Lỗi**: `Connection aborted` (Remote end closed connection without response).
*   **Mô tả**: Worker process của Uvicorn bị crash (thoát đột ngột) mỗi khi gọi endpoint, ngay cả khi đã cố gắng mock (giả lập) phản hồi từ LLM.

## Các Vấn đề Đã Được Giải quyết
1.  **Biến Môi trường Azure**:
    *   Đã đồng bộ hóa `.env` với thư mục tham chiếu (`Final_Exhaustive_Round_Search`).
    *   Đã thêm xử lý cho cả hai tên biến `AZURE_OPENAI_DEPLOYMENT_NAME` và `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`.
    *   Đã khắc phục lỗi thiếu `AZURE_OPENAI_API_KEY` và `OPENAI_API_KEY` trong Docker container do vấn đề encoding của file `.env`.
2.  **Lỗi 400 Bad Request**:
    *   Đã xác định nguyên nhân do tham số `parallel_tool_calls` không được hỗ trợ hoặc bị từ chối bởi API version `2024-06-01` của Azure.
    *   Đã triển khai code (trong `AzureAugmentedLLM`) để loại bỏ tham số này khỏi payload trước khi gửi.
3.  **Cấu trúc Code**:
    *   Đã chuyển từ Monkey Patch (không ổn định) sang Subclassing (`AzureAugmentedLLM` kế thừa `OpenAIAugmentedLLM`) để quản lý logic Azure OpenAI sạch sẽ hơn.

## Các Giả thuyết về Lỗi Crash (Connection Aborted)
Mặc dù đã giải quyết các vấn đề cấu hình, server vẫn crash. Điều này rất bất thường vì crash xảy ra ngay cả khi function `request_completion_task` được mock trả về kết quả ngay lập tức. Các nguyên nhân tiềm năng cần điều tra vào ngày mai:

1.  **Playwright trong Docker**:
    *   Khởi tạo `async_playwright().start()` hoặc `browser.launch()` có thể gây crash do thiếu thư viện hệ thống (dù đã dùng image base của Microsoft) hoặc vấn đề về bộ nhớ/shm-size trong Docker.
    *   *Hành động tiếp theo*: Thử tắt Playwright và chỉ chạy LLM text-only để cô lập lỗi.
2.  **Xung đột Thư viện `mcp-agent`**:
    *   Quy trình `attach_llm` của `mcp-agent` có thể thực hiện các bước khởi tạo ngầm định gây lỗi trước khi gọi hàm generate của chúng ta.
3.  **Tài nguyên Docker**:
    *   Container có thể bị OOM (Out Of Memory) kill.

## Kế hoạch Tiếp theo (Ngày mai)
1.  **Cô lập Playwright**: Tạm thời disable phần khởi tạo Browser trong `BrowserAgentRunner` để xem server có còn crash khi chỉ gọi LLM không.
2.  **Kiểm tra Resource**: Kiểm tra `dmesg` hoặc `docker stats` để xem có phải lỗi OOM không.
3.  **Debug từng dòng**: Thêm log chi tiết vào constructor của `BrowserAgentRunner` và trước/sau lệnh `async_playwright().start()`.

## Kết luận
Hệ thống đã sạch về mặt cấu hình và logic gọi API. Vấn đề hiện tại nằm ở tầng Infrastructure (Docker/Playwright) hoặc tương thích sâu của thư viện.
