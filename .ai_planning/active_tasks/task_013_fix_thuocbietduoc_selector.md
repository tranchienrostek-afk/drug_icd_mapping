# Task 013: Fix ThuocBietDuoc Search Selector (BUG-011)

**Objective**: Fix the failing search input selector for ThuocBietDuoc based on Docker logs.

## Problem
Docker logs show:
```
[ThuocBietDuoc] Input not found, retrying...
[ThuocBietDuoc] Finding search input (attempt 2)...
[ThuocBietDuoc] Input not found, retrying...
```

All 3 retry attempts fail to find the search input field.

## Checklist
- [ ] Inspect ThuocBietDuoc search page to find correct selectors
- [ ] Update `config.py` with working selectors
- [ ] Test fix with debug script
- [ ] Verify in Docker logs

## Notes
- The bulk scraper script works fine (direct URL pagination)
- The API search flow uses search form (selector issue)
