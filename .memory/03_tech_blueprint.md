# TECH BLUEPRINT & ARCHITECTURE LOG

## 1. Task Backlog

### [IN-PROGRESS]
- [ ] **TASK-019:** Monitor System Performance & Auto-scaling
- [ ] **TASK-023:** Knowledge Graph Integration (Drug-Disease Links)

### [DONE]
- [x] **TASK-010:** Async Crawler Implementation
- [x] **TASK-016:** API Endpoint `/api/v1/drugs/identify`
- [x] **TASK-020:** Optimize Web Search & Normalization
- [x] **TASK-021:** Smart Upsert & Database Schema Migration
- [x] **TASK-022:** Import DataCore (65k Drugs)
- [x] **TASK-018:** Optimize Search Algorithm (Removal of SDK from Vector Index, RapidFuzz Integration)

## 2. Architecture Decision Records (ADR)

### [ADR-003] Smart Upsert for Large Datasets
- **Status:** Accepted
- **Context:** Importing 65k records using `INSERT OR IGNORE` or row-by-row `SELECT` is inefficient (N queries).
- **Decision:** Use **In-Memory Hash Map** (Pre-load existing SDKs) to check existence in O(1).
- **Logic:** 
  - If SDK exists -> `UPDATE` missing fields only (Enrichment).
  - If SDK new -> `INSERT` full record.
- **Consequence:** Import time reduced from hours to < 2 mins.

### [ADR-004] Hybrid Search Intelligence
- **Status:** Accepted
- **Context:** User queries vary (Typos, Accents, Semantic). SQL `LIKE` is not enough.
- **Decision:** Stacked Layers: Exact -> Fuzzy (RapidFuzz) -> Vector (TF-IDF).
- **Consequence:** High hit-rate on local DB, reducing reliance on slow Web Search.

## 3. Tech Stack (Updated)
- **Language:** Python 3.11 (Docker Slim)
- **Database:** SQLite (with FTS/Vector Logic in app)
- **Search Engine:** `scikit-learn` (TF-IDF), `rapidfuzz` (Levenshtein)
- **Scraper:** Playwright (Async)
- **Container:** Docker Compose