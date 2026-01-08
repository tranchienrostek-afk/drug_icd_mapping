# TECH BLUEPRINT & ARCHITECTURE LOG

## 1. Task Backlog
### [IN-PROGRESS]
- [ ] **TASK-017:** Implement Google Search Strategy (Fixing Rate Limit issue)
- [ ] **TASK-018:** Optimize `ThuocBietDuoc` selectors (Legacy search fallback)

### [DONE]
- [x] **TASK-010:** Fix blocking behavior in crawler (Added `asyncio` support)
- [x] **TASK-016:** API Endpoint `/api/v1/drugs/identify`

## 2. Architecture Decision Records (ADR)

### [ADR-001] Async Crawler
- **Status:** Accepted
- **Context:** Sequential scraping was too slow (>45s per drug).
- **Decision:** Use `playwright.async_api` and `asyncio.gather`.
- **Consequence:** Latency reduced to ~15s. Requires `async` keyword in all service methods.

### [ADR-002] Google First Search
- **Status:** On-Hold (Rate Issues)
- **Context:** Internal search of `thuocbietduoc.com.vn` is slow (multi-step navigation).
- **Decision:** Use Google `site:` search to find direct URLs.
- **Consequence:** Faster navigation but dependency on Google API stability (Rate limits detected).

## 3. Tech Stack
- **Language:** Python 3.10+
- **Web Framework:** FastAPI
- **Scraper:** Playwright (Chromium)
- **Dependencies:** `googlesearch-python` (newly added), `pandas`, `rapidfuzz`