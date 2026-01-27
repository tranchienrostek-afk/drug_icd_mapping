import asyncio
import os
import sys

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "fastapi-medical-app"))

# Load environment variables from .env
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "..", "fastapi-medical-app", ".env")
load_dotenv(env_path)

from app.mapping_drugs.service import ClaimsMedicineMatchingService
from app.mapping_drugs.models import MatchingRequest, ClaimItem, MedicineItem, MatchConfig

async def test_service_v2():
    print("Testing ClaimsMedicineMatchingService.process_v2 directly...")
    
    # Initialize service
    # We might need to mock some things if it depends on DB paths relative to app/
    os.environ["DB_PATH"] = os.path.join(os.path.dirname(__file__), "..", "fastapi-medical-app", "app", "database", "medical.db")
    
    service = ClaimsMedicineMatchingService()
    
    request = MatchingRequest(
        claims=[
            ClaimItem(id="1", service_name="MEDOVENT 30 10X10", amount=10000),
            ClaimItem(id="2", service_name="PANTOLOC 40MG TAKEDA 1X7", amount=10000),
            ClaimItem(id="3", service_name="Thăm dò chức năng", amount=10000)
        ],
        medicines=[
            MedicineItem(id="1", service_name="Ambroxol hydrochloride (Medovent 30mg)", amount=0),
            MedicineItem(id="2", service_name="Pantoprazole (dưới dạng Pantoprazole sodium sesquihydrate)(Pantoloc 40mg)", amount=0)
        ],
        config=MatchConfig(ai_model="gpt-4o-mini")
    )
    
    try:
        result = await service.process_v2(request)
        print("\n=== MATCHING RESULTS V2 ===")
        print(f"Summary: {result.summary}")
        for match in result.results:
            print(f"- Claim: {match.claim_service} -> Med: {match.medicine_service} (Conf: {match.confidence_score})")
            print(f"  Reasoning: {match.evidence.notes}")
            
        print("\n=== ANOMALIES ===")
        for claim in result.anomalies.claim_without_purchase:
            print(f"- Claim without purchase: {claim.service} (Risk: {claim.risk_flag})")
            
    except Exception as e:
        print(f"Error during service test: {e}")

if __name__ == "__main__":
    asyncio.run(test_service_v2())
