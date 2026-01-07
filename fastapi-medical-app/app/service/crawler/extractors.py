import re
from .utils import parse_drug_info

async def extract_drug_details(target, site_config, site_name, logger):
    """
    Trích xuất dữ liệu chi tiết thuốc sử dụng Playwright Page/Locator.
    
    Cập nhật v2 (Fix BUG-011): 
    - Tích hợp logic 'Sibling Finding' từ Bulk Scraper thành công.
    - Tìm Label (text) -> Lấy thẻ div kế bên (thay vì cố đoán selector bảng/tr/td).
    """
    fields_config = site_config.get('fields', {})
    extracted_fields = {}
    full_content = ""

    # --- 1. LẤY FULL CONTENT (Dùng cho RAG/Search) ---
    try:
        # Ưu tiên lấy trong vùng nội dung chính để loại bỏ header/footer
        main_content = target.locator("main, #content, .content, article, body")
        if await main_content.count() > 0:
            full_content = await main_content.first.inner_text()
        else:
            full_content = await target.inner_text("body")
    except Exception as e:
        full_content = ""
        # logger.warning(f"Could not extract full content: {e}")

    # --- 2. CHIẾN THUẬT: THUOCBIETDUOC SPECIFIC (Logic chiến thắng) ---
    # Logic này copy từ script chạy tay: Tìm text label -> lấy div anh em ngay sau nó
    if "thuocbietduoc" in site_name.lower():
        logger.info(f"[{site_name}] Applying 'Sibling Finding' strategy...")
        
        # Mapping: Tên trường -> Các Label có thể xuất hiện trên UI
        sibling_map = {
            "so_dang_ky": ["Số đăng ký", "SĐK", "Reg.No"],
            "dang_bao_che": ["Dạng bào chế", "Bào chế"],
            "quy_cach_dong_goi": ["Quy cách đóng gói", "Đóng gói"],
            "cong_ty_sx": ["Công ty sản xuất", "Nhà sản xuất"],
            "nuoc_sx": ["Nước sản xuất"],
            "cong_ty_dk": ["Công ty đăng ký", "Đơn vị đăng ký"],
            "nhom_thuoc": ["Nhóm thuốc"],
            "ham_luong": ["Hàm lượng", "Nồng độ"]
        }

        # A. Xử lý các trường đặc biệt (Class/Tag cụ thể)
        try:
            # Tên thuốc (thường là H1)
            if await target.locator("h1").count() > 0:
                extracted_fields["ten_thuoc"] = (await target.locator("h1").first.inner_text()).strip()
            
            # Hoạt chất (Class .ingredient-content rất chuẩn trên site này)
            if await target.locator(".ingredient-content").count() > 0:
                extracted_fields["hoat_chat"] = (await target.locator(".ingredient-content").first.inner_text()).strip()
            elif await target.locator("#chi-dinh").count() > 0: # Fallback đôi khi nó nằm lung tung
                 pass
        except Exception:
            pass

        # B. Xử lý các trường Sibling (Label -> Value)
        for field, labels in sibling_map.items():
            if field in extracted_fields: continue # Đã có rồi thì thôi

            for label in labels:
                # XPath thần thánh: Tìm div chứa text label, lấy div ngay sau nó
                # Cấu trúc: <div>Label:</div> <div>Value</div>
                xpath = f"//div[contains(text(), '{label}')]/following-sibling::div"
                try:
                    loc = target.locator(f"xpath={xpath}")
                    if await loc.count() > 0:
                        val = (await loc.first.inner_text()).strip()
                        # Clean bớt rác nếu có (VD: ": ")
                        val = val.lstrip(":").strip()
                        if val:
                            extracted_fields[field] = val
                            logger.info(f"   + Found {field} via label '{label}': {val[:30]}...")
                            break # Found match for this field
                except Exception:
                    continue

    # --- 3. CHIẾN THUẬT: CONFIG-BASED (Fallback cho site khác hoặc trường thiếu) ---
    if fields_config:
        # logger.info(f"[{site_name}] Checking config selectors for missing fields...")
        for field, selectors in fields_config.items():
            if field in extracted_fields and extracted_fields[field]: 
                continue # Skip nếu logic trên đã tìm thấy
            
            for sel in selectors:
                try:
                    if not sel: continue
                    
                    # Chuẩn hóa selector
                    final_sel = sel
                    if not final_sel.startswith("xpath=") and (final_sel.startswith("//") or final_sel.startswith("./")):
                        final_sel = f"xpath={final_sel}"
                    
                    if await target.locator(final_sel).count() > 0:
                        val = await target.locator(final_sel).first.inner_text()
                        if val:
                            extracted_fields[field] = val.strip()
                            break
                except Exception:
                    continue
    
    return full_content, extracted_fields
