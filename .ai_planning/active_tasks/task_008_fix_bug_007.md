# Task 008: Refactor Scraper Config & Logic (BUG-007)

**Objective**: Fix critical architectural and logic flaws in scraper configuration identified in BUG-007.

## Plan
1. [ ] Redesign `config.py` schema:
    - [ ] Remove `None` in `Field_Selectors`.
    - [ ] Replace `NO_LINK` with `Has_Detail_Page: False`.
    - [ ] Split `HanhDong_TimKiem` into `Action_Type` and `Action_Selector`.
    - [ ] Standardize `Max_Item` and `Priority`.
2. [ ] Refactor `core_drug.py` to support new schema:
    - [ ] Handle `Action_Type` (ENTER/CLICK).
    - [ ] Robust fallback logic.
3. [ ] Refactor `extractors.py`:
    - [ ] Support list of selectors (Primary/Fallback).
    - [ ] Handle Table/List extraction cleanly (convert to structured text or list).
4. [ ] Clean up XPaths in `config.py`:
    - [ ] Remove absolute XPaths.
    - [ ] Use relative XPaths with `contains()` or stable attributes.
5. [ ] Verify with `debug_crawler_manual.py`.
