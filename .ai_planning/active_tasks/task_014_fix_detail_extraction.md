# Task 014: Fix Detail Extraction Selectors (BUG-012)

**Objective**: Port working selectors from the bulk scraper script to the main API crawler config.

## Problem
- **API Crawler** (`config.py`) uses Table-based selectors (`//td...`) which are outdated.
- **Bulk Scraper** (`crapper_data_drugs.py`) uses Div-based selectors (`//div...`) and works correctly.
- Result: API search finds items but returns `null` for details.

## Working Selectors (from Bulk Scraper)
- **SDK**: `//div[contains(text(),'Số đăng ký')]/following-sibling::div`
- **Hoat Chat**: `.ingredient-content`
- **Chi Dinh**: `#chi-dinh` or `//h2[contains(text(),'Chỉ định')]/following-sibling::div`
- **Nha San Xuat**: `//div[contains(text(),'Nhà sản xuất')]/following-sibling::div`

## Checklist
- [ ] Update `config.py` with these selectors as primary options
- [ ] Keep old selectors as fallbacks (just in case)
- [ ] Verify with Debug Script
