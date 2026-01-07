import re
from .utils import parse_drug_info

async def extract_drug_details(target, site_config, site_name, logger):
    """
    Extracts data from a Page OR Locator.
    Args:
        target: Playwright Page object (usually).
    """
    fields_config = site_config.get('fields', {})
    extracted_fields = {}
    
    # 1. Structured Data Extraction
    if fields_config:
        logger.info(f"[{site_name}] Extracting fields...")
        for field, selectors in fields_config.items():
            # Selectors is now a LIST
            val = None
            found = False
            
            for sel in selectors:
                try:
                    if not sel: continue
                    # Clean XPath
                    final_sel = sel
                    if not final_sel.startswith("xpath=") and (final_sel.startswith("//") or final_sel.startswith("./")):
                         final_sel = f"xpath={final_sel}"
                    
                    # Check count
                    if await target.locator(final_sel).count() > 0:
                        val = await target.locator(final_sel).first.inner_text()
                        if val:
                            extracted_fields[field] = val.strip()
                            found = True
                            break # Stop fallback if found
                except Exception as e:
                     continue
            
            if not found:
                 # logger.debug(f"Field '{field}' not found.")
                 pass

    # 2. Main Content
    full_content = ""
    try:
        detail_cfg = site_config.get('detail_logic', {})
        content_xp = detail_cfg.get('content_container')
        if content_xp:
             if not content_xp.startswith("xpath=") and (content_xp.startswith("//") or content_xp.startswith(".")):
                  content_xp = f"xpath={content_xp}"
             
             if await target.locator(content_xp).count() > 0:
                  full_content = await target.locator(content_xp).first.inner_text()
             else:
                  full_content = "Content container not found."
    except:
        full_content = "Error extracting content."
        
    return full_content, extracted_fields
