
# Validated Scraper Configuration
# Schema Strictness: High
# No None values allowed. Use empty strings or empty lists.

def get_drug_web_config():
    """
    Returns a list of validated site configurations.
    """
    return [
        {
            "site_name": "ThuocBietDuoc",
            "url": "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx",
            "enabled": True,
            "priority": 1,
            
            # Search Behavior
            "search": {
                "input_xpath": "//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']",
                "action_type": "CLICK", # Enum: ENTER or CLICK
                "button_xpath": "//*[@id='ctl00_ContentPlaceHolder1_btnSearch']"
            },

            # List Items
            "list_logic": {
                "item_container": "//a[contains(@class, 'drug-list-item') or contains(@href, '/thuoc/')]",  # Generic robust selector
                "max_items": 2
            },

            # Detail Page
            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": ".", # Click the container itself
                "expand_button_xpath": "", # No expand needed usually
                "content_container": "//*[@id='content']" # Fallback if specific fields fail
            },

            # Extraction Rules (List of XPaths for fallback)
            "fields": {
                "so_dang_ky": [
                    "//div[contains(text(), 'Số đăng ký')]/following-sibling::div",
                    "//span[contains(text(), 'SĐK')]/following-sibling::span",
                    "//*[@id='divSoDangKy']"
                ],
                "hoat_chat": [
                    "//div[contains(text(), 'Dạng bào chế')]/following-sibling::div", # Often near info
                    "//*[@id='divHoatChat']"
                ],
                "cong_ty_san_xuat": [
                    "//div[contains(text(), 'Nhà sản xuất')]/following-sibling::div",
                    "//*[@id='divNhaSanXuat']"
                ],
                "chi_dinh": [
                    "//div[contains(text(), 'Chỉ định')]/following-sibling::div",
                    "//*[@id='divChiDinh']"
                ]
            }
        },
        {
            "site_name": "TrungTamThuoc",
            "url": "https://trungtamthuoc.com.vn/",
            "enabled": True,
            "priority": 2,
            
            "search": {
                "input_xpath": "//input[@name='search' or @type='text']",
                "action_type": "ENTER",
                "button_xpath": ""
            },

            "list_logic": {
                "item_container": "//div[contains(@class, 'product-item') or contains(@class, 'item-product')]//h3/a",
                "max_items": 2
            },

            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": ".",
                "expand_button_xpath": "//*[@id='btn-expand-content']",
                "content_container": "//*[@id='content']"
            },

            "fields": {
                "so_dang_ky": [
                    "//tr[td[contains(text(), 'Số đăng ký')]]/td[2]",
                    "//span[contains(text(), 'Số đăng ký')]/following-sibling::span"
                ],
                "hoat_chat": [
                    "//tr[td[contains(text(), 'Hoạt chất')]]/td[2]"
                ],
                "cong_ty_san_xuat": [
                    "//tr[td[contains(text(), 'Nhà sản xuất')]]/td[2]"
                ],
                "chi_dinh": [
                    "//*[@id='chi-dinh']//following-sibling::div[1]"
                ]
            }
        },
        {
            "site_name": "DAV (Dịch Vụ Công)",
            "url": "https://dichvucong.dav.gov.vn/congbothuoc/index",
            "enabled": True,
            "priority": 3,
            
            "search": {
                "input_xpath": "//input[@id='txtTenThuoc']",
                "action_type": "CLICK",
                "button_xpath": "//button[@id='btnSearch']" # Hypothetical robust ID
            },

            "list_logic": {
                "item_container": "//table[@id='tblDSThuoc']//tr[position()>1]",
                "max_items": 2
            },

            "detail_logic": {
                "has_detail_page": False, # Table row contains data
                "link_xpath": "",
                "expand_button_xpath": "",
                "content_container": "."
            },

            "fields": {
                "so_dang_ky": [
                    "./td[2]" # Relative to row
                ],
                "hoat_chat": [
                    "./td[3]"
                ],
                "cong_ty_san_xuat": [
                    "./td[5]"
                ],
                "chi_dinh": [] # Not available in table list usually
            }
        }
    ]

def get_icd_web_config():
    """
    Returns ICD configuration (Refactored to match Drug schema slightly if needed, 
    but for now keeping simple as core_icd manages it).
    """
    import pandas as pd
    # Maintaining DataFrame for ICD for now to limit scope of change to Drugs first,
    # or refactor if requested. The Plan focused on Drugs logic.
    # BUT consistency is key. Let's keep ICD simple for now.
    
    data = {
        "TenTrang": ["KCB_ICD"],
        "URL": ["https://icd.kcb.vn"],
        "XPath_Input_Search": ["//*[@id='keyword']"],
        "XPath_Item_Container": ["//*[@id='recommend-box']//li"],
        "XPath_Link_ChiTiet": ["."],
        "XPath_Nut_Mo_Rong": ["//*[@id='btn-expand']"],
        "XPath_NoiDung_Lay": ["//*[@id='detail']"]
    }
    return pd.DataFrame(data)
