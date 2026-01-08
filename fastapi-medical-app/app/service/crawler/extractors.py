import re
from .utils import parse_drug_info

async def extract_drug_details(target, site_config, site_name, logger):
    """
    Trích xuất dữ liệu chi tiết thuốc sử dụng Playwright Page/Locator.
    
    Cập nhật v3:
    - Tích hợp logic 'Section Parsing' (H2 range) để trích xuất nội dung dài.
    - Cải thiện 'Sibling Finding' với mapping rộng hơn.
    """
    fields_config = site_config.get('fields', {})
    extracted_fields = {}
    full_content = ""

    async def extract_section_range(page, start_label, stop_label=None):
        """
        Trích xuất nội dung giữa hai tiêu đề (H2/H3).
        """
        try:
            # Tìm node bắt đầu chứa label
            start_xpath = f"//h2[contains(., '{start_label}')] | //h3[contains(., '{start_label}')]"
            start_loc = page.locator(f"xpath={start_xpath}").first
            if await start_loc.count() == 0: return None

            # Lấy tất cả anh em phía sau
            nodes = start_loc.locator("xpath=following-sibling::*")
            texts = []
            for i in range(await nodes.count()):
                node = nodes.nth(i)
                tag = await node.evaluate("e => e.tagName")
                
                # Nếu gặp tiêu đề kế tiếp (H2/H3) thì dừng
                if tag in ["H2", "H3"]:
                    if stop_label:
                        node_text = await node.inner_text()
                        if stop_label.lower() in node_text.lower():
                            break
                    else:
                        break # Dừng ở bất kỳ H2/H3 nào nếu không có stop_label cụ thể
                
                texts.append(await node.inner_text())
            return "\n".join(t.strip() for t in texts if t.strip())
        except Exception:
            return None

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

    # --- 2. CHIẾN THUẬT: SIBLING FINDING & SECTION RANGE (Logic chính) ---
    # Tìm kiếm label -> lấy nội dung anh em hoặc nội dung trong range H2/H3
    
    # Mapping: Tên trường -> Các Label có thể xuất hiện trên UI
    sibling_map = {
        "so_dang_ky": ["Số đăng ký", "SĐK", "Reg.No", "Sđk"],
        "dang_bao_che": ["Dạng bào chế", "Bào chế", "Dạng chế phẩm"],
        "quy_cach_dong_goi": ["Quy cách đóng gói", "Đóng gói", "Quy cách"],
        "cong_ty_sx": ["Công ty sản xuất", "Nhà sản xuất", "Cơ sở sản xuất", "Sản xuất bởi"],
        "nuoc_sx": ["Nước sản xuất", "Xuất xứ"],
        "cong_ty_dk": ["Công ty đăng ký", "Đơn vị đăng ký", "Cơ sở đăng ký"],
        "nhom_thuoc": ["Nhóm thuốc", "Danh mục", "Loại thuốc"],
        "ham_luong": ["Hàm lượng", "Nồng độ", "Thành phần hàm lượng"]
    }

    section_map = {
        "chi_dinh": ["Chỉ định", "Chỉ định điều trị", "Công dụng", "Chỉ định và công dụng"],
        "chong_chi_dinh": ["Chống chỉ định", "Chống chỉ định và thận trọng"],
        "lieu_dung": ["Liều dùng", "Cách dùng", "Hướng dẫn sử dụng", "Liều dùng và cách dùng"],
        "tac_dung_phu": ["Tác dụng phụ", "Tác dụng không mong muốn", "Phản ứng có hại"],
        "than_trong": ["Thận trọng", "Lưu ý", "Cảnh báo và thận trọng"]
    }

    # A. Xử lý các trường đặc biệt (Class/Tag cụ thể)
    try:
        # Tên thuốc (thường là H1 hoặc class cụ thể)
        if await target.locator("h1").count() > 0:
            extracted_fields["ten_thuoc"] = (await target.locator("h1").first.inner_text()).strip()
        
        # Hoạt chất đặc biệt cho ThuocBietDuoc
        if await target.locator(".ingredient-content").count() > 0:
            extracted_fields["hoat_chat"] = (await target.locator(".ingredient-content").first.inner_text()).strip()
    except Exception:
        pass

    # B. Xử lý các trường Sibling (Label -> Value)
    for field, labels in sibling_map.items():
        if field in extracted_fields: continue

        for label in labels:
            # Ưu tiên các div/p/span chứa chính xác label
            xpath = f"//*[self::div or self::p or self::span or self::td][contains(text(), '{label}')]/following-sibling::*[self::div or self::p or self::span or self::td]"
            try:
                loc = target.locator(f"xpath={xpath}")
                if await loc.count() > 0:
                    val = (await loc.first.inner_text()).strip()
                    val = val.lstrip(":").strip()
                    if val:
                        extracted_fields[field] = val
                        break
            except Exception:
                continue

    # C. Xử lý các trường Section Range (H2/H3 blocks)
    for field, labels in section_map.items():
        if field in extracted_fields and extracted_fields[field]: continue
        for label in labels:
            content = await extract_section_range(target, label)
            if content:
                extracted_fields[field] = content
                break

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
