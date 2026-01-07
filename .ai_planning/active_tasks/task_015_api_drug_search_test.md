# Task 015: API Drug Search Testing

**Objective**: Verify the `/api/v1/drugs/identify` endpoint works functionality, especially the search and detail extraction logic after recent fixes.

## Scope
- Test basic drug search (Database & Web).
- Test complex search (Web with Detail Extraction).
- Test error handling.
- Save all results for audit.

## Steps
- [ ] Create timestamped test script `tests/YYYY_MM_DD_HH_MM_test_api_search.py`
- [ ] Implement result saving to `tests/result_tests/`
- [ ] Run test against localhost
- [ ] Generate execution report

## Success Criteria
- Test script runs without errors.
- JSON results are saved.
- "Symbicort" search returns valid SDK and Ingredients (verifying BUG-012 fix).
