import asyncio
import json
import os
import sys

# Thêm app vào path để import được
sys.path.append(os.path.join(os.getcwd(), "app"))

from mapping_drugs.service import ClaimsMedicineMatchingService
from mapping_drugs.models import MatchingRequest

async def debug():
    service = ClaimsMedicineMatchingService()
    data_path = r"c:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\unittest\datatest_mapping.json"
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Xử lý config rác nếu có
    if "config" in data:
        print(f"Original config: {data['config']}")
        # MatchingRequest rẽ nhánh sang extra="ignore" nên config này sẽ bị bỏ qua
    
    request = MatchingRequest(**data)
    print("Request object created successfully")
    
    try:
        print("Starting process...")
        result = await service.process(request)
        print("Process completed successfully")
        
        # Thử dump ra JSON để xem có lỗi serialization không
        json_result = result.model_dump_json(indent=2)
        print("Result dumped to JSON successfully")
        
        # Save output for review
        with open("debug_result.json", "w", encoding="utf-8") as f:
            f.write(json_result)
        print("Result saved to debug_result.json")
        
    except Exception as e:
        print(f"Error during process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug())
