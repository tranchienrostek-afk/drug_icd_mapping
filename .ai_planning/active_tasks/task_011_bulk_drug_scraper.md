# Task 011: Bulk Drug Data Scraper

**Objective**: Scrape drug data from thuocbietduoc.com.vn (pages 1800-3424) and import to database.

## Status
- **Script**: `scripts/2026_01_07_15_35_crapper_data_drugs.py`
- **Output**: `ketqua_thuoc_part_20260107_154800.csv`
- **Progress**: Running (started page 1800)

## Checklist
- [/] Run high-speed scraper from page 1800-3424
- [ ] Monitor output CSV file for completeness
- [ ] Validate scraped data quality
- [ ] Import scraped data into `drugs` table in database

## Notes
- MAX_WORKERS: 6 (parallel scraping)
- BATCH_SAVE: 50 records per CSV write
- ~20 drugs per page × 1624 pages = ~32,480 drugs expected
