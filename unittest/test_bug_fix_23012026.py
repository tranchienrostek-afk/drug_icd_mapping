import unittest
from unittest.mock import MagicMock
import sys
import os
import asyncio

# Setup path
# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is c:\...\drug_icd_mapping\unittest
project_root = os.path.dirname(current_dir)
# project_root is c:\...\drug_icd_mapping

app_path = os.path.join(project_root, 'fastapi-medical-app')
if os.path.exists(app_path):
    sys.path.append(app_path)
    print(f"Added {app_path} to sys.path")
else:
    print(f"WARNING: Could not find app path at {app_path}")

from app.service.consultation_service import ConsultationService
from app.service.consultation_service import ConsultationService
from app.models import ConsultRequest, DrugItem, DiagnosisItem

class TestBugFix23012026(unittest.IsolatedAsyncioTestCase):
    async def test_medical_equipment_category(self):
        """
        Verify that if role is 'medical equipment', category is 'nodrug' and validity is empty.
        """
        service = ConsultationService(db_core=MagicMock())
        # Mock kb_matcher
        service.kb_matcher = MagicMock()
        
        # Simulate KB return
        service.kb_matcher.find_best_match_with_icd.return_value = {
            "tdv_feedback": "medical equipment",
            "match_method": "fuzzy_test",
            "match_score": 95,
            "drug_name_norm": "natriclorid normalized"
        }
        
        payload = ConsultRequest(
            request_id="test-bug-fix",
            symptom="test",
            diagnoses=[DiagnosisItem(code="J00", name="Test Diag", type="MAIN")],
            items=[DrugItem(id="item1", name="natriclorid srk saltmax")]
        )
        
        results = await service.process_integrated_consultation(payload)
        
        self.assertEqual(len(results), 1)
        res = results[0]
        
        print("\nResult:", res)
        
        self.assertEqual(res['role'], "medical equipment")
        self.assertEqual(res['category'], "nodrug")
        self.assertEqual(res['validity'], "") # Should be empty string as per logic
        
    async def test_main_drug_category(self):
        """
        Verify that 'main drug' maps to category='drug', validity='valid'.
        """
        service = ConsultationService(db_core=MagicMock())
        service.kb_matcher = MagicMock()
        service.kb_matcher.find_best_match_with_icd.return_value = {
            "tdv_feedback": "main drug",
            "match_method": "fuzzy_test",
            "match_score": 95,
            "drug_name_norm": "panadol normalized"
        }
        
        payload = ConsultRequest(
            request_id="test-bug-fix-2",
            symptom="test",
            diagnoses=[DiagnosisItem(code="J00", name="Test Diag", type="MAIN")],
            items=[DrugItem(id="item2", name="Panadol")]
        )
        
        results = await service.process_integrated_consultation(payload)
        res = results[0]
        
    async def test_auto_correct_logic_comprehensive(self):
        """
        Verify strict whitelist rules via auto_correct_mapping logic.
        """
        service = ConsultationService(db_core=MagicMock())
        
        # 1. NODRUG Group
        for role in ["medical equipment", "thiết bị y tế", "supplement", "thực phẩm chức năng", "cosmeceuticals"]:
            cat, val, clean_role = service.auto_correct_mapping(role)
            self.assertEqual(cat, "nodrug", f"Role '{role}' should be nodrug")
            self.assertEqual(val, "", f"Role '{role}' should have empty validity")
            
        # 2. DRUG Group
        for role in ["main drug", "secondary drug"]:
            cat, val, clean_role = service.auto_correct_mapping(role)
            self.assertEqual(cat, "drug", f"Role '{role}' should be drug")
            self.assertEqual(val, "valid", f"Role '{role}' should be valid")
            
        # 3. Invalid Group
        cat, val, clean_role = service.auto_correct_mapping("invalid")
        self.assertEqual(cat, "drug")
        self.assertEqual(val, "invalid")
        
        # 4. Unknown/Fallback
        cat, val, clean_role = service.auto_correct_mapping("some unknown therapy")
        self.assertEqual(cat, "drug")
        self.assertEqual(val, "valid")

if __name__ == '__main__':
    unittest.main()
