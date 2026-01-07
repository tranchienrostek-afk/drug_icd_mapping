<!-- Định nghĩa công nghệ (để AI không dùng sai thư viện) -->

# TECH STACK & VERSIONS
**Project:** AZINSU (Drug Data Management)
**Language:** Python 3.10+
**Framework:** FastAPI (Back-end)

## 1. Core Dependencies
- **FastAPI**: Web framework chính.
- **Pydantic v2**: Khai báo schema và validate dữ liệu (Strict typing).
- **SQLAlchemy 2.0+**: ORM cho PostgreSQL/SQLite.
- **Alembic**: Quản lý migrations cho database.
- **Neo4j**: Graph Database cho Knowledge Graph.

## 2. External Services & APIs
- **Azure OpenAI**: Model xử lý ngôn ngữ tự nhiên (GPT-4o/GPT-3.5) cho phân tích dược lý.
- **Playwright**: Web scraping cho crawler tìm kiếm thuốc/bệnh.
- **Playwright-stealth**: Hỗ trợ vượt mặt các hệ thống bot-detection cơ bản.

## 3. Libraries & Utilities
- **BeautifulSoup4**: Parsing HTML thô nếu cần thiết.
- **Scikit-learn**: Các thuật toán ML cơ bản cho so khớp chuỗi/dữ liệu.
- **OpenPyXL**: Đọc/ghi tệp Excel (Dữ liệu y tế thường ở dạng này).
- **Python-dotenv**: Quản lý biến môi trường.

## 4. Constraints (Ràng buộc)
- **Cấm sử dụng `pandas`** cho các xử lý API logic (tránh overhead và tiêu tốn bộ nhớ). Chỉ dùng trong các script phân tích dữ liệu rời (Data Analytics).
- **Luôn ưu tiên `Async/Await`** cho mọi tác vụ I/O (DB, Web Scraping, External API).
- **Phải sử dụng virtual environment (`venv`)** cho dự án.