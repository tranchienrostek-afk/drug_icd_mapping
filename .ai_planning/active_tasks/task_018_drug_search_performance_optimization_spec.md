# Task 018: Drug Search Performance Optimization Spec

## 1. Problem Description
The current drug search API response time is too slow (up to 5 minutes for a small batch). Key bottlenecks identified:
- **Sequential site scraping**: Sites are visited one by one.
- **Sequential drug processing**: The verification script/API might be processing drugs in a loop instead of parallel batches.
- **Heavy UI overhead**: Browser loads images, fonts, and CSS. Popups cause repeated delays.
- **Normalization regression**: `normalize_name` or `normalize_text` is corrupting names (e.g., "Berodual 200 liều" -> "Berodual Iều").

## 2. Infrastructure Optimization
### 2.1 Parallel Site Scrapping
- [ ] Refactor `scrape_drug_web_advanced` in `main.py` to ensure all site tasks are launched concurrently using `asyncio.gather`.
- [ ] Ensure that even if one site times out, other results are returned immediately.

### 2.2 Parallel Drug Processing
- [ ] Update verification scripts and batch processing endpoints to process multiple drugs in parallel (while staying within memory/concurrency limits).

### 2.3 Browser Optimization
- [ ] **Strict Resource Blocking**: Block all `image`, `font`, `media`, and `stylesheet` requests in `core_drug.py`.
- [ ] **Fast Popup Handling**: Update `handle_popups` to use `page.add_locator_handler` or faster non-waiting checks to close overlays without blocking the main flow.

## 3. Data Quality & Preprocessing
### 3.1 Fix Normalization Bug
- [ ] Debug `app/utils.py`: `normalize_name` and `normalize_text`.
- [ ] Root cause: Character removal in `re.sub(r'[^a-z0-9\s]', '', text)` when accents are not correctly mapped.
- [ ] [FIX] Ensure all Vietnamese characters are normalized to latin equivalents BEFORE any removal of special characters.

### 3.2 Intelligent Pre-search Cleaning
- [ ] Implement a pre-search step to remove common noise: dosage descriptors ("xịt", "viên", "10ml") if the initial search fails.
- [ ] Avoid redundant fallback loops; determine the most likely search term once.

## 4. Acceptance Criteria
- [ ] Total search time for 5 drugs < 45 seconds.
- [ ] No corruption of names like "Berodual" -> "Iều".
- [ ] All 4 configured sites (ThuocBietDuoc, TrungTamThuoc, LongChau, DAV) return merged results.
