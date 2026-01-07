# Task 007: Refactor Web Crawler (CR-004)

**Objective**: Split `app/service/web_crawler.py` into smaller files (< 200 lines) to improve maintainability and debugging capability.

## Plan
1. [ ] Create package directory `fastapi-medical-app/app/service/crawler/`.
2. [ ] Create `__init__.py` to expose public API.
3. [ ] Create `utils.py`: Logging configuration, screenshot directory constant, and `parse_drug_info` helper.
4. [ ] Create `config.py`: `get_drug_web_config` and `get_icd_web_config` functions.
5. [ ] Create `extractors.py`: Logic to extract details from a drug detail page (extracted from `scrape_single_site_drug`).
6. [ ] Create `core_drug.py`: `scrape_single_site_drug` logic (using `extractors.py`).
7. [ ] Create `core_icd.py`: `scrape_single_site_icd` and `search_icd_online`.
8. [ ] Create `main.py`: `scrape_drug_web_advanced` orchestrator.
9. [ ] Update references in `app/api/drugs.py`, `app/api/diseases.py`, and `scripts/`.
10. [ ] Verify functionality with `scripts/debug_crawler_manual.py` and tests.
11. [ ] Delete original `web_crawler.py`.
