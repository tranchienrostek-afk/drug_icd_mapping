import openpyxl
import os

# Đường dẫn đến file chứa các ký tự ĐƯỢC PHÉP (đã làm sạch)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(CURRENT_DIR, "allowed_charset.xlsx")

def load_allowed_chars(excel_path: str) -> set[str]:
    """
    Đọc danh sách các ký tự cho phép từ file Excel.
    Giả định file Excel có cột đầu tiên chứa các ký tự (bỏ qua dòng tiêu đề).
    """
    if not os.path.exists(excel_path):
        print(f"Cảnh báo: Không tìm thấy file nguồn {excel_path}")
        return set()

    try:
        wb = openpyxl.load_workbook(excel_path, read_only=True)
        ws = wb.active
        
        allowed = set()
        # Duyệt qua cột A, bỏ qua dòng 1 (header)
        for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
            val = row[0]
            if val is not None:
                allowed.add(str(val))
        
        return allowed
    except Exception as e:
        print(f"Lỗi khi đọc file {excel_path}: {e}")
        return set()

# Khởi tạo set ký tự cho phép khi import module
_ALLOWED_CHARS = load_allowed_chars(STATS_FILE)

def normalize_drug_name(text: str) -> str:
    """
    Chuẩn hóa tên thuốc theo quy tắc truncate (cắt cụt).
    Duyệt từng ký tự từ trái sang phải.
    Nếu gặp ký tự cho phép -> giữ lại.
    Nếu gặp ký tự KHÔNG cho phép -> dừng ngay lập tức, bỏ qua ký tự đó và toàn bộ phần còn lại.
    """
    if not text:
        return ""
    
    # Nếu danh sách allowed trống, logic an toàn là trả về nguyên gốc để tránh mất dữ liệu oan do lỗi config?
    # Tuy nhiên đề bài yêu cầu "xoá", nên ta cứ tuân thủ logic strict.
    if not _ALLOWED_CHARS:
         print("Warning: Danh sách ký tự cho phép rỗng!")
         # Tùy chọn: return "" hoặc return text. 
         # Với logic truncate, nếu không có allowed char nào thì kết quả là "" ngay từ đầu.
         return ""

    result = []
    for char in text:
        if char in _ALLOWED_CHARS:
            result.append(char)
        else:
            # Gặp ký tự lạ -> Dừng luôn.
            break
            
    return "".join(result).strip()

if __name__ == "__main__":
    print(f"Đã load {len(_ALLOWED_CHARS)} ký tự cho phép từ {STATS_FILE}")
    
    test_cases = [
        "Thuốc Panadol 500mg",
        "Thuốc (Panadol)",
        "Viên nén - 500mg",
        "Tên thuốc bình thường",
        "Thuốc A + Thuốc B"
    ]
    
    print("-" * 40)
    for t in test_cases:
        cleaned = normalize_drug_name(t)
        print(f"Gốc   : '{t}'")
        print(f"Clean : '{cleaned}'")
        print("-" * 40)
