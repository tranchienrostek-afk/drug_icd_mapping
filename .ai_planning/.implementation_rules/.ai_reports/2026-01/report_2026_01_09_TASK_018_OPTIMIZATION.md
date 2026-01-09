# Report: Task 018 - Drug Search Performance Optimization

**Date**: 2026-01-09
**Author**: Assistant
**Task ID**: TASK_018
**Status**: COMPLETED (with Adjustments)

## 1. Executive Summary
This task addressed critical performance bottlenecks and data quality issues. Initial aggressive optimization caused a regression (0 results found in Docker environment). The final solution balances performance with stability by retaining parallel scraping and normalization fixes while reverting risky resource blocking.

## 2. Problem Statement
1.  **Normalization Corruption**: Fixed. "Berodual 200 liều" -> "Berodual 200 lieu".
2.  **Slow Search**: Addressed via parallel site scraping and timeouts.
3.  **Regression**: Aggressive CSS/Popup blocking caused the scraper to fail completely (0 results) on some environments.

## 3. Implementation Details

### 3.1 Data Quality (Normalization Fix)
- **File**: `app/utils.py`
- **Change**: Robust Vietnamese character mapping before stripping specials. Validated with `Ludox` and `Berodual` cases.

### 3.2 Infrastructure Optimization (Performance)
- **File**: `app/service/crawler/main.py`
- **Change**:
    - **Parallel Scraping**: Used `asyncio.wait_for(timeout=25.0)` to enforce limits.
    - **Outcome**: Prevents infinite hangs.

### 3.3 Stability Adjustments (Reverts)
- **File**: `app/service/crawler/core_drug.py`
- **Change**:
    - **Reverted CSS Blocking**: Stylesheets are allowed again to ensure layout correctness for selectors.
    - **Reverted `add_locator_handler`**: Returned to manual `handle_popups` to avoid potential interference with site interaction flows.

## 4. Verification Results

### 4.1 Automated Benchmark
- **Script**: `tests/benchmark_search.py`
- **Status**: **PASSED**.
- **Results**:
    - "Berodual": FOUND (SDK: VN-17269-13).
    - "Panadol Extra": FOUND.
    - **Speed**: Slower than the broken optimized version (~7s vs 4s) but **correct**. Total time for 5 items is acceptable compared to original >5 mins.

## 5. Lessons Learned
- Blocking `stylesheet` is risky for scrapers relying on visibility checks.
- `add_locator_handler` in Playwright can be too aggressive for sites with ambiguous popup selectors.

## 6. Artifacts
- `tests/benchmark_search.py`
- `result_test/benchmark_*.log`
