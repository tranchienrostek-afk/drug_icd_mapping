# TASK 017: IMPROVE SEARCH EFFICIENCY (GOOGLE SEARCH STRATEGY)
**Status:** [Logged]
**Assignee:** Senior Dev
**Priority:** High (Blocking BUG-013)

## 1. Context & Motivation
- **Issue:** `BUG-013` reports that the current Playwright-based internal search on `ThuocBietDuoc` is:
    1.  **Too Slow:** Navigating to search page -> Typing -> Waiting -> Clicking result takes 15-20s/drug.
    2.  **Inaccurate:** Internal search engines often have poor fuzzy matching (e.g., "Symbicort 120" might fail if the site expects "Symbicort Turbuhaler").
- **Agent Consultation:**
    - **Dr. BA:** We need results. If the official search fails, finding the direct link via Google is acceptable as long as the domain is trusted (`thuocbietduoc.com.vn`, `drugbank.vn`).
    - **Prof. AI:** Search Engines (Google/Bing) have superior NLP/Fuzzy matching. Using them as an indexer is $O(1)$ complexity for finding the URL compared to $O(N)$ navigation steps.
    - **Senior Dev:** Hard-coding selectors for search bars is brittle. URL pattern matching is more robust.

## 2. Technical Solution: "Google First" Strategy
Instead of:
`Open Browser -> Go to Search Page -> Type Keyword -> Wait -> Click Result -> Scrape`

We will do:
1.  **Google Query:** `site:thuocbietduoc.com.vn {drug_name}` via `googlesearch-python` (lightweight HTTP).
2.  **Filter:** Pick the first URL that looks like a detail page.
3.  **Direct Scrape:** `page.goto(direct_url)` -> Extract.

**Benefits:**
- **Speed:** Skips the "Search Page" interaction entirely.
- **Accuracy:** Leverages Google's typo correction and semantic understanding.

## 3. Implementation Plan
- [ ] **Step 1:** Create `GoogleSearchService` (wrapper for `googlesearch-python`).
- [ ] **Step 2:** Refactor `CrawlerService` to accept a direct URL or finding it via Google.
- [ ] **Step 3:** Update `config.py` to support "Search Strategy" configuration (Generic Search vs. Site-Specific).
- [ ] **Step 4:** Benchmark with the failing list ("Ludox", "Symbicort", "Berodual").

## 4. Requirement
- **Output:** Must find SDK and Ingredients for at least 80% of the `BUG-013` list.
- **Latency:** Target < 10s per drug (average).
