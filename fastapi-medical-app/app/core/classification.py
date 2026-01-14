
# Single Source of Truth for Classification Logic
# Based on knowledge for agent/logs_to_database/group_definitions.md

CLASSIFICATION_RULES = [
    {
        "keywords": ["main drug", "start_drug", "valid"],
        "required_all": ["drug"],  # For "main drug", usually implies "drug" + "valid"
        "value": "valid",
        "label": "Có điều trị",
        "tags": ["drug", "valid", "main drug"],
        "description": "Thuốc chính / Có điều trị",
        "priority": 1 # Higher priority if conflicting matches?
    },
    {
        "keywords": ["secondary drug"],
        "value": "secondary drug",
        "label": "Hỗ trợ điều trị",
        "tags": ["drug", "valid", "secondary drug"],
        "description": "Thuốc hỗ trợ",
        "priority": 2
    },
    {
        "keywords": ["medical supplies"],
        "value": "medical supplies",
        "label": "Vật tư y tế",
        "tags": ["nodrug", "medical supplies"],
        "description": "Vật tư y tế",
        "priority": 3
    },
    {
        "keywords": ["supplement"],
        "value": "supplement",
        "label": "Thực phẩm chức năng",
        "tags": ["nodrug", "supplement"],
        "description": "Thực phẩm chức năng",
        "priority": 3
    },
    {
        "keywords": ["cosmeceuticals"],
        "value": "cosmeceuticals",
        "label": "Dược mĩ phẩm",
        "tags": ["nodrug", "cosmeceuticals"],
        "description": "Dược mĩ phẩm", 
        "priority": 3
    },
    {
        "keywords": ["medical equipment"],
        "value": "medical equipment",
        "label": "Thiết bị y tế",
        "tags": ["nodrug", "medical equipment"],
        "description": "Thiết bị y tế",
        "priority": 3
    },
    {
        "keywords": ["invalid"],
        "value": "invalid",
        "label": "Không điều trị",
        "tags": ["drug", "invalid"],
        "description": "Không điều trị",
        "priority": 4 # Fallback for invalid drug
    }
]

def get_classification_by_key(key: str):
    """
    Look up classification by strict value key (e.g. 'secondary drug') 
    or loosely by keyword.
    """
    key = key.lower().strip().replace('"', '').replace("'", "")
    
    # 1. Exact match on value
    for rule in CLASSIFICATION_RULES:
        if rule["value"] == key:
            return rule
            
    # 2. Keyword match
    for rule in CLASSIFICATION_RULES:
        for k in rule["keywords"]:
            if k in key:
                return rule
                
    return None

def parse_csv_classification(phan_loai: str, tdv_feedback: str) -> dict:
    """
    Determine the standard classification based on CSV columns.
    Priority: tdv_feedback > phan_loai keywords.
    """
    phan_loai = phan_loai.lower()
    tdv_feedback = tdv_feedback.lower()
    
    # Cleaning Postgres array string formatting e.g. "{valid}" -> "valid"
    clean_tdv = tdv_feedback.replace("{", "").replace("}", "").replace('"', '').strip()
    
    # 1. Try to use tdv_feedback if it contains a known valid value
    if clean_tdv:
        # Check if clean_tdv matches a known value directly/partially
        # Example: "secondary drug" -> matches value "secondary drug"
        # Example: "valid" -> matches value "valid"
        match = get_classification_by_key(clean_tdv)
        if match:
            return match

    # 2. Fallback: Parse phan_loai combined string
    # LEVERAGE POSTGRES ARRAY FORMAT: {tag1,tag2,"tag 3"}
    combined_raw = f"{phan_loai},{tdv_feedback}" # Join with comma to treat as one big list
    
    # Simple parser: Remove braces, then split by comma
    cleaned_str = combined_raw.replace("{", "").replace("}", "")
    
    tags = set()
    for item in cleaned_str.split(','):
        t = item.strip().replace('"', '').replace("'", "")
        if t:
            tags.add(t.lower())
    
    # Iterate rules in order
    for rule in CLASSIFICATION_RULES:
        # Check if any keyword matches exactly in the tags set
        for k in rule["keywords"]:
            if k in tags:
                # Special handler for 'valid' vs 'invalid' conflict
                # If we found 'valid' but 'invalid' is ALSO in tags, we might prefer invalid?
                # Actually, if we use exact tag match:
                # 'invalid' tag will match 'invalid' keyword.
                # 'valid' tag will match 'valid' keyword.
                # In "{drug,invalid}", tags are {"drug", "invalid"}. "valid" is NOT in tags.
                return rule
                
    # Default/Unknown
    return {
        "value": "unknown",
        "label": "Chưa phân loại",
        "tags": [],
        "description": "Unknown"
    }
