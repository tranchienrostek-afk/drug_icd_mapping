import re
import asyncio
from playwright.async_api import async_playwright
from .utils import logger, parse_drug_info
from .config import get_drug_web_config
from .core_drug import scrape_single_site_drug
from .google_search import GoogleSearchService

async def scrape_drug_web_advanced(keyword, **kwargs):
    """
    Advanced Parallel Search & Merge with Google Search Fallback
    """
    config_list = get_drug_web_config()
    
    # --- Robust Keyword Cleaning ---
    clean_kw = re.sub(r'[-–():+/]', ' ', keyword)
    clean_kw = re.sub(r'\s+', ' ', clean_kw).strip()
    
    # Try multiple search variants if needed
    variants = [clean_kw]
    
    # Fallback variant: Try only the first word or words before the first number
    if " " in clean_kw:
        simplified = re.split(r'\d', clean_kw)[0].strip()
        if simplified and simplified != clean_kw and len(simplified) > 2:
            variants.append(simplified)

    async with async_playwright() as p:
        # Allow headless toggle for debugging
        headless_mode = kwargs.get('headless', True) # Support passing via function arg
        display_mode = False if headless_mode is False else True # Logic inversion fix: launch(headless=True) is default
        
        # Better: just use a variable
        is_headless = True
        if "headless" in kwargs:
             is_headless = kwargs["headless"]
        
        browser = await p.chromium.launch(
            headless=is_headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        try:
            # --- GOOGLE SEARCH FIRST STRATEGY (NEW) ---
            google_service = GoogleSearchService(domain="thuocbietduoc.com.vn")
            
            for kw_variant in variants:
                logger.info(f"[WebAdvanced] Attempting search with: '{kw_variant}'")
                
                # Try Google Search first for ThuocBietDuoc
                direct_url = None
                try:
                    logger.info(f"[GoogleSearch] Searching for direct URL...")
                    direct_url = google_service.find_drug_url(kw_variant)
                except Exception as e:
                    logger.warning(f"[GoogleSearch] Failed: {e}")
                
                tasks = []
                for site in config_list: # Support all enabled sites
                    if site.get('enabled', True):
                        # If Google found a URL for ThuocBietDuoc, use it
                        if site['site_name'] == 'ThuocBietDuoc' and direct_url:
                            logger.info(f"[WebAdvanced] Using Google-found URL for {site['site_name']}")
                            tasks.append(scrape_single_site_drug(browser, site, kw_variant, direct_url=direct_url))
                        else:
                            # Original search path for other sites
                            tasks.append(scrape_single_site_drug(browser, site, kw_variant))
                
                results_lists = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check if we got ANY candidates from this variant
                has_results = False
                for r_list in results_lists:
                    if isinstance(r_list, list) and len(r_list) > 0:
                        has_results = True
                        break
                
                if has_results:
                    logger.info(f"[WebAdvanced] Found potential results for variant: '{kw_variant}'")
                    break 
                else:
                    logger.warning(f"[WebAdvanced] No items found for variant: '{kw_variant}'. Trying fallback...")
        finally:
            await browser.close()
            
    # 2. Flatten & Parse
    candidates = []
    logger.info(f"[WebAdvanced] Flattening results from {len(results_lists)} site lists...")
    for res in results_lists:
        if isinstance(res, list):
            for item in res:
                content = item.get('Content', '')
                parsed = parse_drug_info(content)
                
                # --- Prefer Extracted Data over Regex ---
                if '_extracted_data' in item and item['_extracted_data']:
                    for f_key, f_val in item['_extracted_data'].items():
                        if f_key == "so_dang_ky" and f_val:
                            sdk_clean = parse_drug_info(f_val).get('so_dang_ky')
                            if sdk_clean: 
                                parsed['so_dang_ky'] = sdk_clean
                            else:
                                parsed['so_dang_ky'] = f_val.strip()
                        else:
                             parsed[f_key] = f_val
                
                item.update(parsed)
                if 'ten_thuoc' not in item or not item['ten_thuoc']: 
                     item['ten_thuoc'] = keyword 
                
                candidates.append(item)
    
    logger.info(f"[WebAdvanced] Total items found: {len(candidates)}")
    
    # 3. Stop Condition & Selection
    if not candidates:
        return {"status": "not_found", "message": "No drugs found on web."}
        
    sdk_candidates = [c for c in candidates if c.get('so_dang_ky')]
    logger.info(f"[WebAdvanced] Candidates with SDK: {len(sdk_candidates)}")
    
    if not sdk_candidates:
        logger.warning(f"[WebAdvanced] No SDK found. Returning best item without SDK.")
        best_candidate = candidates[0]
        if not best_candidate.get('so_dang_ky'): 
             best_candidate['so_dang_ky'] = "Web Result (No SDK)"
        sdk_groups = {"Web Result (No SDK)": [best_candidate]}
    else:
        sdk_groups = {}
        for c in sdk_candidates:
            sdk = c['so_dang_ky']
            if sdk not in sdk_groups: sdk_groups[sdk] = []
            sdk_groups[sdk].append(c)
        
    sorted_groups = sorted(sdk_groups.values(), key=len, reverse=True)
    best_group = sorted_groups[0]
    
    # 4. Merge Logic
    final_name = best_group[0]['ten_thuoc']
    final_sdk = best_group[0]['so_dang_ky']
    
    hoat_chat_set = {i['hoat_chat'] for i in best_group if i.get('hoat_chat')}
    cong_ty_set = {i['cong_ty_san_xuat'] for i in best_group if i.get('cong_ty_san_xuat')}
    sources = {i['Link'] for i in best_group if i.get('Link')}
    
    best_candidate = best_group[0]
    dang_bao_che = best_candidate.get('dang_bao_che')
    nhom_thuoc = best_candidate.get('nhom_thuoc')
    ham_luong = best_candidate.get('ham_luong')
    
    note_parts = []
    if nhom_thuoc: note_parts.append(f"Nhóm: {nhom_thuoc}")
    if ham_luong: note_parts.append(f"Hàm lượng: {ham_luong}")
    final_note = " | ".join(note_parts)

    # Combine long fields properly
    final_chi_dinh = " | ".join(filter(None, {i.get('chi_dinh') for i in best_group if i.get('chi_dinh')}))
    final_chong_chi_dinh = " | ".join(filter(None, {i.get('chong_chi_dinh') for i in best_group if i.get('chong_chi_dinh')}))
    final_lieu_dung = " | ".join(filter(None, {i.get('lieu_dung') for i in best_group if i.get('lieu_dung')}))

    final_data = {
        "ten_thuoc": final_name,
        "so_dang_ky": final_sdk,
        "hoat_chat": " | ".join(filter(None, hoat_chat_set)),
        "cong_ty_san_xuat": " | ".join(filter(None, cong_ty_set)),
        "chi_dinh": final_chi_dinh or best_candidate.get('chi_dinh'),
        "chong_chi_dinh": final_chong_chi_dinh or best_candidate.get('chong_chi_dinh'),
        "lieu_dung": final_lieu_dung or best_candidate.get('lieu_dung'),
        "classification": dang_bao_che,
        "note": final_note, 
        "source_urls": list(sources),
        "confidence": 0.8,
        "source": "Web Search (Advanced)"
    }
    
    return final_data
