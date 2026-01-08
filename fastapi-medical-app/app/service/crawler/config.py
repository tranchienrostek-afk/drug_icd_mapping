
# Validated Scraper Configuration v3
# Schema Strictness: High
# Changes: Robust CSS selectors, fallback lists, disabled DNS-failing site

def get_drug_web_config():
    """
    Returns a list of validated site configurations for multi-site drug search.
    Updated: 2026-01-08 - Synchronized with verified knowledge scripts.
    """
    return [
        {
            "site_name": "ThuocBietDuoc",
            "url": "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx",
            "enabled": True,
            "priority": 1,
            "search": {
                "input_selectors": [
                    "input[name='key']",
                    "#search-input",
                    "input[type='text']"
                ],
                "action_type": "ENTER"
            },
            "list_logic": {
                "item_container": ".drug-card-title",
                "max_items": 3
            },
            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": ".",
                "content_container": "#content"
            },
            "fields": {
                "so_dang_ky": ["//div[contains(text(), 'Số đăng ký')]/following-sibling::div"],
                "hoat_chat": [".ingredient-content"],
                "chi_dinh": ["#chi-dinh"]
            },
            "popup_selectors": [".close-button", "button[aria-label='Close']"]
        },
        {
            "site_name": "TrungTamThuoc",
            "url": "https://trungtamthuoc.com/",
            "enabled": True, 
            "priority": 2,
            "search": {
                "input_selectors": [
                    "#txtKeywords",
                    "input[name='txtKeywords']",
                    "input[type='text']"
                ],
                "action_type": "CLICK",
                "button_selectors": ["#btnsearchheader"]
            },
            "list_logic": {
                "item_container": ".cs-item-product",
                "max_items": 2
            },
            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": "a[href]",
                "content_container": "main"
            },
            "fields": {
                "so_dang_ky": ["//tr[td[contains(text(), 'Số đăng ký')]]/td[2]"],
                "hoat_chat": ["//tr[td[contains(text(), 'Hoạt chất')]]/td[2]"]
            },
            "popup_selectors": ["#close-ads", ".modal-close"]
        },
        {
            "site_name": "NhaThuocLongChau",
            "url": "https://nhathuoclongchau.com.vn/",
            "enabled": True,
            "priority": 3,
            "search": {
                "input_selectors": ['input[name="search"]'],
                "action_type": "ENTER"
            },
            "list_logic": {
                "item_container": "a[href^='/thuoc/']",
                "max_items": 2
            },
            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": ".",
                "content_container": "main"
            },
            "fields": {
                "so_dang_ky": ["xpath=//div[p[text()='Số đăng ký']]//span", "xpath=//div[p[contains(.,'Số đăng ký')]]//span"],
                "hoat_chat": ["xpath=//div[p[text()='Thành phần']]//span"],
                "ten_thuoc": ['h1[data-test="product_name"]']
            },
            "popup_selectors": ["button:text('Đóng')", "span:text('X')"]
        },
        {
            "site_name": "DAV",
            "url": "https://dichvucong.dav.gov.vn/congbothuoc/index",
            "enabled": True,
            "priority": 4,
            "search": {
                "input_selectors": ["input[ng-model='vm.filterAll']"],
                "action_type": "ENTER"
            },
            "list_logic": {
                "item_container": "div.k-grid-content tbody tr",
                "max_items": 5
            },
            "detail_logic": {
                "has_detail_page": False,
                "link_xpath": "",
                "content_container": "."
            },
            "fields": {
                "so_dang_ky": ["td:nth-child(4)"], 
                "ten_thuoc": ["td:nth-child(6)"],
                "hoat_chat": ["td:nth-child(10)"],
                "ham_luong": ["td:nth-child(11)"],
                "cong_ty_san_xuat": ["td:nth-child(22)"]
            }
        }
    ]

def get_icd_web_config():
    """ICD configuration synchronized with verified format."""
    return [
        {
            "site_name": "KCB_ICD",
            "url": "https://icd.kcb.vn",
            "enabled": True,
            "priority": 1,
            "search": {
                "input_selectors": ["#keyword"],
                "action_type": "ENTER"
            },
            "list_logic": {
                "item_container": "#recommend-box li",
                "max_items": 5
            },
            "detail_logic": {
                "has_detail_page": True,
                "link_xpath": "a",
                "expand_button_xpath": "#btn-expand",
                "content_container": "#detail"
            },
            "fields": {
                "disease_name": ["h2", ".title"],
                "icd_code": [".code", ".icd-code"]
            }
        }
    ]
