
# Validated Scraper Configuration v3
# Schema Strictness: High
# Changes: Robust CSS selectors, fallback lists, disabled DNS-failing site

def get_drug_web_config():
    """
    Returns a list of site configurations synchronized with 'knowledge for agents'.
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
                # From thuocbietduoc_extract.py: 
                # //div[div[text()='Số đăng ký']]/div[contains(@class,'font-semibold')]
                # //div[contains(text(),'Số đăng ký')]/following-sibling::div
                "so_dang_ky": [
                    "xpath=//div[div[text()='Số đăng ký']]/div[contains(@class,'font-semibold')]", 
                    "xpath=//div[contains(text(),'Số đăng ký')]/following-sibling::div"
                ],
                # From ingredient-content
                "hoat_chat": [".ingredient-content"],
                "dang_bao_che": ["xpath=//div[div[text()='Dạng bào chế']]/div[contains(@class,'font-semibold')]"],
                "nhom_thuoc": ["xpath=//div[div[text()='Danh mục']]//a"],
                "chi_dinh": ["#section-1"],
                "chong_chi_dinh": ["#section-2"]
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
                # From trungtamthuoc_extract.py: 
                # //tr[td[contains(normalize-space(), '{label}')]]/td[last()]
                "so_dang_ky": ["xpath=//tr[td[contains(normalize-space(), 'Số đăng ký')]]/td[last()]"],
                "hoat_chat": ["xpath=//tr[td[contains(normalize-space(), 'Hoạt chất')]]/td[last()]"],
                "dang_bao_che": ["xpath=//tr[td[contains(normalize-space(), 'Dạng bào chế')]]/td[last()]"],
                "quy_cach": ["xpath=//tr[td[contains(normalize-space(), 'Quy cách đóng gói')]]/td[last()]"],
                "nhom_thuoc": ["xpath=//tr[td[contains(normalize-space(), 'Chuyên mục')]]/td[last()]"],
                "thanh_phan": ["xpath=//h2[contains(normalize-space(), 'Thành phần')]/following-sibling::*[preceding-sibling::h2[1][contains(normalize-space(), 'Thành phần')]]"],
                "cong_dung": ["xpath=//h2[contains(normalize-space(), 'Công dụng')]/following-sibling::*[preceding-sibling::h2[1][contains(normalize-space(), 'Công dụng')]]"]
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
                # From nhathuoclongchau_extract.py:
                # div.flex has p:text("Label") -> div.flex-1 span/p
                # Use strict xpath to emulate this robustly
                "so_dang_ky": ["xpath=//div[contains(@class,'flex')][descendant::p[contains(text(),'Số đăng ký')]]//div[contains(@class,'flex-1')]//span"],
                "hoat_chat": ["xpath=//div[contains(@class,'flex')][descendant::p[contains(text(),'Thành phần')]]//div[contains(@class,'flex-1')]//p"],
                "dang_bao_che": ["xpath=//div[contains(@class,'flex')][descendant::p[contains(text(),'Dạng bào chế')]]//div[contains(@class,'flex-1')]//span"],
                "ten_thuoc": ['h1[data-test="product_name"]'],
                "mo_ta": ["#detail-content-0"],
                "cong_dung": ["#detail-content-2"]
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
                # From dichvucong_search_extract.py directly mapped to columns
                # 3: so_gplh (SDK), 5: ten_thuoc, 9: hoat_chat, ...
                "so_dang_ky": ["td:nth-child(4)"], # Script says index 3 (0-based) -> 4th child
                "ten_thuoc": ["td:nth-child(6)"], # Script 5 -> 6th child
                "hoat_chat": ["td:nth-child(10)"], # Script 9 -> 10th child
                "ham_luong": ["td:nth-child(11)"], # Script 10 -> 11th child
                "cong_ty_san_xuat": ["td:nth-child(22)"], # Script 21 -> 22nd child
                "nuoc_sx": ["td:nth-child(23)"]
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
