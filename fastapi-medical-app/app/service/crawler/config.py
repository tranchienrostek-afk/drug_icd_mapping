
# Validated Scraper Configuration v3
# Schema Strictness: High
# Changes: Robust CSS selectors, fallback lists, disabled DNS-failing site

def get_drug_web_config():
    """
    Returns a list of validated site configurations.
    Updated 2026-01-07 15:15 - BUG-009 Fix
    """
    return [
        {
            "site_name": "ThuocBietDuoc",
            "url": "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx",
            "enabled": True,
            "priority": 1,
            
            # Search Behavior - Robust Fallback Selectors
            "search": {
                "input_selectors": [
                    "input[name*='TenThuoc']",  # CSS attribute contains (most robust)
                    "input[id*='txtTenThuoc']",  # CSS ID contains
                    "#ContentPlaceHolder1_txtTenThuoc",  # Simpler ID
                    "//input[contains(@id, 'TenThuoc')]"  # XPath fallback
                ],
                "action_type": "CLICK",
                "button_selectors": [
                    "input[name*='btnSearch']",
                    "#ContentPlaceHolder1_btnSearch",
                    "//input[contains(@id, 'btnSearch')]"
                ]
            },

            # List Items
            "list_logic": {
                "item_container": "//a[contains(@href, '/thuoc/')]",
                "max_items": 2
            },

            # Detail Page
            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": ".",
                "expand_button_xpath": "",
                "content_container": "//*[@id='content']"
            },

            # Extraction Rules
            "fields": {
                "so_dang_ky": [
                    "//td[contains(text(), 'Số đăng ký')]/following-sibling::td",
                    "//span[contains(text(), 'SĐK')]/following-sibling::span"
                ],
                "hoat_chat": [
                    "//td[contains(text(), 'Hoạt chất')]/following-sibling::td"
                ],
                "cong_ty_san_xuat": [
                    "//td[contains(text(), 'Nhà sản xuất')]/following-sibling::td"
                ],
                "chi_dinh": [
                    "//td[contains(text(), 'Chỉ định')]/following-sibling::td"
                ]
            }
        },
        {
            "site_name": "TrungTamThuoc",
            "url": "https://trungtamthuoc.com.vn/",
            "enabled": False,  # DISABLED: DNS not resolving in Docker (BUG-009)
            "priority": 2,
            
            "search": {
                "input_selectors": [
                    "input[name='search']",
                    "input[type='text'][placeholder*='tìm']"
                ],
                "action_type": "ENTER",
                "button_selectors": []
            },

            "list_logic": {
                "item_container": ".product-item a",
                "max_items": 2
            },

            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": ".",
                "expand_button_xpath": "",
                "content_container": "#content"
            },

            "fields": {
                "so_dang_ky": ["//tr[td[contains(text(), 'Số đăng ký')]]/td[2]"],
                "hoat_chat": ["//tr[td[contains(text(), 'Hoạt chất')]]/td[2]"],
                "cong_ty_san_xuat": ["//tr[td[contains(text(), 'Nhà sản xuất')]]/td[2]"],
                "chi_dinh": []
            }
        },
        {
            "site_name": "DAV",
            "url": "https://dichvucong.dav.gov.vn/congbothuoc/index",
            "enabled": True,
            "priority": 3,
            
            "search": {
                "input_selectors": [
                    "#txtTenThuoc",
                    "input[placeholder*='tên thuốc']",
                    "input[type='text']"
                ],
                "action_type": "CLICK",
                "button_selectors": [
                    "#btnSearch",
                    "button[type='submit']",
                    ".btn-search"
                ]
            },

            "list_logic": {
                "item_container": "#tblDSThuoc tbody tr",
                "max_items": 2
            },

            "detail_logic": {
                "has_detail_page": False,
                "link_xpath": "",
                "expand_button_xpath": "",
                "content_container": "."
            },

            "fields": {
                "so_dang_ky": ["td:nth-child(2)"],
                "hoat_chat": ["td:nth-child(3)"],
                "cong_ty_san_xuat": ["td:nth-child(5)"],
                "chi_dinh": []
            }
        }
    ]

def get_icd_web_config():
    """ICD configuration."""
    import pandas as pd
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
