import pandas as pd

def get_drug_web_config():
    """
    Trả về DataFrame cấu hình các trang web thuốc
    Updated: 2026-01-07 - Specific XPaths from BUG-001 report
    """
    data = {
        "STT": [0, 1, 2],
        "TenTrang": [
            "DAV (Dịch Vụ Công)", 
            "ThuocBietDuoc", 
            "TrungTamThuoc"
        ],
        "URL": [
            "https://dichvucong.dav.gov.vn/congbothuoc/index",
            "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx",
            "https://trungtamthuoc.com.vn/"
        ],
        "XPath_Input_Search": [
            "xpath=/html/body/div[4]/div/div[1]/div/div/div[2]/div[1]/div/input[2]",
            "xpath=//*[@id=\"search-input\"]",
            "xpath=//*[@id=\"txtKeywords\"]"
        ],
        "HanhDong_TimKiem": [
            "xpath=/html/body/div[4]/div/div[1]/div/div/div[2]/div[2]/button[1]",
            "ENTER",
            "ENTER"
        ],
        "XPath_Item_Container": [
            "xpath=/html/body/div[4]/div/div[2]/div[3]/div[2]/table/tbody/tr", 
            "xpath=/html/body/main/section[2]/div/div[2]/div/div/h3/a", 
            "xpath=//*[@id=\"cscontentdetail\"]/div/div/div/strong/a | //*[@id=\"cscontentdetail\"]/div/div/strong/a"
        ],
        "XPath_Link_ChiTiet": [
            "NO_LINK", 
            ".",
            "."
        ],

        "Field_Selectors": [
             None,
             {
                 "ten_thuoc": "//h1 | /html/body/main/div[2]/div/div[1]/div/div/div[2]/h1",
                 "so_dang_ky": "//*[contains(text(), 'Số đăng ký')]/following-sibling::* | //*[contains(text(), 'SĐK')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div[2]",
                 "hoat_chat": "//div[contains(text(), 'Hoạt chất')]/following-sibling::* | //div[contains(text(), 'Thành phần')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[2]/div/div/div/div/a",
                 "ham_luong": "//div[contains(text(), 'Hàm lượng')]/following-sibling::* | //*[@id=\"thanh-phan-hoat-chat\"]/div[2]/table/tbody/tr/td[2]/span",
                 "dang_bao_che": "//div[contains(text(), 'Dạng bào chế')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div/div[2]/div/div[2]",
                 "danh_muc": "//div[contains(text(), 'Nhóm thuốc')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div/div[4]/div/a",
                 "chi_dinh": "//h2[contains(text(), 'Chỉ định')]/following-sibling::* | #chi-dinh | //*[@id=\"cong-dung-thuoc\"]/div[2]"
             },
             {
                 "ten_thuoc": "//h1 | //*[@id=\"cscontentdetail\"]/header/div[2]/div/h1/strong",
                 "so_dang_ky": "//*[contains(text(), 'Số đăng ký')]/parent::*/td[2] | //*[@id=\"cscontentdetail\"]/header/div[2]/div/table/tbody/tr[3]/td[2]",
                 "hoat_chat": "//*[contains(text(), 'Hoạt chất')]/parent::*/td[2] | //*[contains(text(), 'Thành phần')]/parent::*/td[2] | //*[@id=\"cs-hoat-chat\"]/td[2]",
                 "ham_luong": "//*[@id=\"pro-mo-ta-noi-dung\"]/table | //*[@id=\"pro-mo-ta-noi-dung\"]/table",
                 "dang_bao_che": "//*[contains(text(), 'Dạng bào chế')]/parent::*/td[2] | //*[@id=\"cscontentdetail\"]/header/div[2]/div/table/tbody/tr[4]/td[2]",
                 "danh_muc": "//*[@id=\"cscategorymain\"]/td[2] | //*[@id=\"cscategorymain\"]/td[2]",
                 "chi_dinh": "//*[@id=\"pro-mo-ta-noi-dung\"]/p[3] | //div[contains(@class, 'cs-content')]"
             }
        ],
        "UuTien": [99, 1, 3],
        "Max_Item": [1, 2, 2]
    }
    df = pd.DataFrame(data)
    return df.sort_values(by='UuTien')

def get_icd_web_config():
    """Cấu hình Scraper ICD"""
    data = {
        "STT": [1],
        "TenTrang": ["ICD Cục KCB"],
        "URL": ["https://icd.kcb.vn/icd-10/icd10"],
        "XPath_Input_Search": ["//*[@id='search']"],
        "HanhDong_TimKiem": ["ENTER"],
        "XPath_Item_Container": ["//*[@id='recommend-box']//li//a"], 
        "XPath_Link_ChiTiet": ["."],
        "XPath_Nut_Mo_Rong": ["//*[@id='detail']/div/div[4]/div/div[2]/dl[4]/div/div[1]/div/div/h5"],
        "XPath_NoiDung_Lay": ["//*[@id='detail']/div/div[4]/div"],
        "UuTien": [1],
        "Max_Item": [1]
    }
    return pd.DataFrame(data)
