import re
from .utils import parse_drug_info

async def extract_drug_details(new_page, site_config, site_name, logger):
    """
    Extracts structured data and content from a drug detail page.
    """
    field_selectors = site_config.get('Field_Selectors')
    extracted_fields = {}
    
    # 1. Structured Data Extraction
    if field_selectors and isinstance(field_selectors, dict):
        logger.info(f"[{site_name}] Using Field Selectors...")
        for field, selector in field_selectors.items():
            try:
                if not selector: continue
                # Selector Handling (Logic reused from original)
                sel_str = selector
                
                # Selector Handling (Logic reused from original)
                sel_str = selector
                
                if "|" in selector:
                     if selector.startswith("xpath="):
                         sel_str = selector 
                     elif "//" in selector:
                         sel_str = f"xpath={selector}"
                else:
                    if selector.startswith("//") or selector.startswith("/html") or selector.startswith("xpath="):
                        sel_str = f"xpath={selector}" if not selector.startswith("xpath=") else selector
                
                # Wait optional (fast check)
                if await new_page.locator(sel_str).count() > 0:
                    val = await new_page.locator(sel_str).first.inner_text()
                    extracted_fields[field] = val.strip()
                else:
                    # Fallback for chi_dinh if backup exists
                    if field == "chi_dinh" and "chi_dinh_bk" in field_selectors:
                        bk = field_selectors["chi_dinh_bk"]
                        if await new_page.locator(f"xpath={bk}").count() > 0:
                            val = await new_page.locator(f"xpath={bk}").first.inner_text()
                            extracted_fields["chi_dinh"] = val.strip()
            except Exception as f_err:
                logger.warning(f"Field '{field}' extract error: {f_err}")

        # Post-Process 'chi_dinh'
        if "chi_dinh" in extracted_fields and extracted_fields["chi_dinh"]:
             raw_cd = extracted_fields["chi_dinh"]
             
             if "trungtamthuoc" in site_name.lower():
                 # Apply TTT Regex to chi_dinh field
                 pattern = r'(?:^|[\r\n]+)\s*1\.?\s+(?P<muc1>.*?)(?=[\r\n]+\s*2\.?\s+).*?(?:^|[\r\n]+)\s*2\.?\s+(?P<muc2>.*?)(?=[\r\n]+\s*3\.?\s+)'
                 match = re.search(pattern, raw_cd, re.DOTALL)
                 if match:
                     m1 = match.group('muc1').strip()
                     m2 = match.group('muc2').strip()
                     processed_cd = f"1. {m1}\n2. {m2}"
                     # Truncate
                     if len(processed_cd) > 800:
                          processed_cd = processed_cd[:800] + "... (Truncated)"
                     extracted_fields["chi_dinh"] = processed_cd
                     logger.info(f"[{site_name}] Extracted 'chi_dinh' refined by Regex ({len(processed_cd)} chars).")
                 else:
                     # Regex failed, Fallback Truncate
                     if len(raw_cd) > 800:
                          extracted_fields["chi_dinh"] = raw_cd[:800] + "... (Truncated)"
             else:
                  # Generic Truncation for other sites
                  if len(raw_cd) > 800:
                      extracted_fields["chi_dinh"] = raw_cd[:800] + "... (Truncated)"

    # 2. Main Content Extraction
    xp_content = site_config['XPath_NoiDung_Lay']
    full_content = "Không lấy được nội dung."
    
    try:
        await new_page.wait_for_selector(f"xpath={xp_content}", timeout=5000)
        raw_content = await new_page.locator(f"xpath={xp_content}").first.inner_text()
        
        if "trungtamthuoc" in site_name.lower():
            # Apply Robust Regex to TTT content
            logger.info(f"[{site_name}] Applying Robust Regex to TTT content...")
            pattern = r'(?:^|[\r\n]+)\s*1\.?\s+(?P<muc1>.*?)(?=[\r\n]+\s*2\.?\s+).*?(?:^|[\r\n]+)\s*2\.?\s+(?P<muc2>.*?)(?=[\r\n]+\s*3\.?\s+)'
            match = re.search(pattern, raw_content, re.DOTALL)
            if match:
                m1 = match.group('muc1').strip()
                m2 = match.group('muc2').strip()
                full_content = f"1. {m1}\n2. {m2}"
                logger.info(f"[{site_name}] Regex Success. Len: {len(full_content)}")
            else:
                full_content = raw_content # Fallback
        else:
            # Truncate for others
            full_content = raw_content
            if len(full_content) > 1000:
                full_content = full_content[:1000] + "... (Truncated)"
                
        logger.info(f"[{site_name}] Content extracted ({len(full_content)} chars).")

    except:
        if extracted_fields:
            full_content = "Structured Data Extracted: " + str(extracted_fields)
        else:
            try:
                full_content = await new_page.locator("body").inner_text()
                full_content = "⚠️ (Fallback) " + full_content[:800]
            except: pass
        logger.warning(f"[{site_name}] Main content not found, using Fallback.")

    return full_content, extracted_fields
