import pytest
import asyncio
from fastapi_medical_app.app.service.web_crawler import scrape_drug_web_advanced

@pytest.mark.asyncio
@pytest.mark.xfail(reason="Flaky due to external site antibot/rate-limiting")
async def test_scrape_paracetamol_bug_001():
    """
    RED PHASE: Mô tả hành vi mong muốn.
    Input là 'Paracetamol 500mg' -> Phải lấy được ít nhất 1 kết quả hợp lệ với SĐK.
    """
    keyword = "Paracetamol 500mg"
    
    # Act
    result = await scrape_drug_web_advanced(keyword)
    
    # Assert
    assert result["status"] != "not_found", "Crawler should find results for Paracetamol 500mg"
    assert result["so_dang_ky"] and result["so_dang_ky"] != "Web Result (No SDK)", "Crawler should find a real SDK"
    assert len(result["ten_thuoc"]) > 0, "Name should not be empty"
