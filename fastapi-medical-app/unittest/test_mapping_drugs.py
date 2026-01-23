import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
from datetime import datetime

# ==========================================
# Setup Environment & Path
# ==========================================
# ==========================================
# Setup Environment & Path
# ==========================================
# Determine path to project root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Check if we are in a structure where 'fastapi-medical-app' is a sibling or if we are IN it
possible_roots = [
    os.path.join(parent_dir, 'fastapi-medical-app'), # Local host structure
    parent_dir, # Container /app structure (unittest is in /app/unittest)
]

found_root = None
for root in possible_roots:
    if os.path.exists(os.path.join(root, 'app')):
        found_root = root
        break

if found_root:
    sys.path.append(found_root)
    print(f"DEBUG: Added {found_root} to sys.path")
else:
    print(f"WARNING: Could not find 'app' package in standard locations. PWD: {os.getcwd()}")
    # Fallback to current directory or parent
    sys.path.append(parent_dir)

try:
    from app.mapping_drugs.service import ClaimsMedicineMatchingService
    from app.mapping_drugs.models import (
        ClaimItem, MedicineItem, MatchingRequest, MatchingResponse,
        MatchedPair, MatchEvidence
    )
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import app modules. sys.path: {sys.path}")
    raise e

class TestClaimsMedicineMatching(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Setup test environment before each test method"""
        # Patch DrugMatcher to mock DB interactions
        self.mock_matcher_patcher = patch('app.mapping_drugs.service.DrugMatcher')
        self.MockDrugMatcher = self.mock_matcher_patcher.start()
        self.mock_matcher_instance = self.MockDrugMatcher.return_value
        
        # Default mock behavior: NO_MATCH in DB
        self.mock_matcher_instance.match.return_value = {
            "status": "NOT_FOUND",
            "data": None,
            "confidence": 0.0,
            "method": "MOCK"
        }
        
        # Patch AI Matcher to prevent real API calls
        self.mock_ai_patcher = patch('app.mapping_drugs.service.AISemanticMatcher')
        self.MockAISemanticMatcher = self.mock_ai_patcher.start()
        self.mock_ai_instance = self.MockAISemanticMatcher.return_value
        # Mock AI match to return no matches by default
        self.mock_ai_instance.match_claims_medicine = MagicMock(return_value={"matches": [], "ai_model": "MOCK_AI"})
        # Make async mock return value work
        async def async_return():
            return {"matches": [], "ai_model": "MOCK_AI"}
        self.mock_ai_instance.match_claims_medicine.return_value = {"matches": [], "ai_model": "MOCK_AI"}
        self.mock_ai_instance.match_claims_medicine.side_effect = None
        # Since we use await, the return value must be awaitable if not using AsyncMock (which implies 3.8+)
        # But IsolatedAsyncioTestCase handles async.
        # Ideally use AsyncMock if available.
        # Simplest is to just set side_effect to an async function
        async def mock_ai_match(*args, **kwargs):
             return {"matches": [], "ai_model": "MOCK_AI"}
        self.mock_ai_instance.match_claims_medicine.side_effect = mock_ai_match

        # Initialize Service with mocked matcher
        self.service = ClaimsMedicineMatchingService(db_path=":memory:")
        # Force inject our mock instance (in case init created a new one)
        self.service.matcher = self.mock_matcher_instance

    def tearDown(self):
        """Clean up after test"""
        self.mock_matcher_patcher.stop()
        self.mock_ai_patcher.stop()

    async def test_01_exact_match(self):
        """Test Case 1: Matching hoàn hảo (Cùng tên, cùng giá)"""
        print("\n--- Running Test 01: Exact Match ---")
        request = MatchingRequest(
            request_id="t1",
            claims=[ClaimItem(claim_id="c1", service="Paracetamol 500mg", amount=15000)],
            medicine=[MedicineItem(medicine_id="m1", service="Paracetamol 500mg", amount=15000)]
        )
        
        # Mock DB response
        self.mock_matcher_instance.match.return_value = {
            "status": "FOUND",
            "data": {"ten_thuoc": "Paracetamol 500mg", "so_dang_ky": "VD-1234", "hoat_chat": "Paracetamol"},
            "confidence": 1.0,
            "method": "EXACT_MATCH"
        }

        response = await self.service.process(request)
        
        self.assertEqual(len(response.results), 1)
        match = response.results[0]
        self.assertEqual(match.match_status, "matched")
        self.assertEqual(match.medicine_id, "m1")
        self.assertEqual(match.confidence_score, 1.0)
        print("✅ Test 01 Passed")

    async def test_02_fuzzy_match(self):
        """Test Case 2: Matching mờ (Viết tắt, sai chính tả nhẹ)"""
        print("\n--- Running Test 02: Fuzzy Match (Para 500 vs Paracetamol 500mg) ---")
        request = MatchingRequest(
            request_id="t2",
            # Use 'Paracetamol 500' vs 'Paracetamol 500mg' to ensure > 80 score 
            # (non-DB match max conf = 0.65 -> weak_match)
            claims=[ClaimItem(claim_id="c1", service="Paracetamol 500", amount=10000)],
            medicine=[MedicineItem(medicine_id="m1", service="Paracetamol 500mg", amount=10000)]
        )
        
        # Mock DB: Not Found
        self.mock_matcher_instance.match.return_value = {
             "status": "NOT_FOUND", "data": None, "confidence": 0.0, "method": "MOCK"
        }

        response = await self.service.process(request)
        match = response.results[0]
        
        # Non-DB match -> Conf max 0.65 -> weak_match
        self.assertEqual(match.match_status, "weak_match")
        self.assertEqual(match.medicine_id, "m1")
        self.assertEqual(response.summary.need_manual_review, 1)
        print(f"✅ Test 02 Passed - Confidence: {match.confidence_score} (Weak Match)")

    async def test_03_db_enrichment_logic(self):
        """Test Case 3: Matching dựa trên kiến thức DB (Cùng map về 1 chuẩn)"""
        print("\n--- Running Test 03: DB Enrichment Matching ---")
        request = MatchingRequest(
            request_id="t3",
            claims=[ClaimItem(claim_id="c1", service="BrandName X", amount=100)],
            medicine=[MedicineItem(medicine_id="m1", service="GenericName X", amount=100)]
        )
        
        def side_effect(name):
            if "BrandName" in name:
                 return {"status": "FOUND", "data": {"ten_thuoc": "StandardDrug", "so_dang_ky": "V1", "hoat_chat": "A"}, "confidence": 1.0, "method": "MOCK"}
            if "GenericName" in name:
                 return {"status": "FOUND", "data": {"ten_thuoc": "StandardDrug", "so_dang_ky": "V1", "hoat_chat": "A"}, "confidence": 1.0, "method": "MOCK"}
            return {"status": "NOT_FOUND", "data": None, "confidence": 0, "method": "MOCK"}
            
        self.mock_matcher_instance.match.side_effect = side_effect

        response = await self.service.process(request)
        match = response.results[0]
        
        # DB Match -> Conf > 0.85 -> Matched
        self.assertEqual(match.medicine_id, "m1")
        self.assertTrue(match.evidence.drug_knowledge_match)
        print("✅ Test 03 Passed - Matched via Standard DB Name")

    async def test_04_anomaly_detection(self):
        """Test Case 4: Phát hiện bất thường (Thừa/Thiếu thuốc)"""
        print("\n--- Running Test 04: Anomaly Detection ---")
        request = MatchingRequest(
            request_id="t4",
            # Claim C1 không có thuốc tương ứng
            claims=[ClaimItem(claim_id="c1", service="Expensive Cancer Drug", amount=5000000)],
            # Medicine M1 không được claim
            medicine=[MedicineItem(medicine_id="m1", service="Vitamin C", amount=20000)]
        )
        
        self.mock_matcher_instance.match.return_value = {"status": "NOT_FOUND", "data": None, "confidence": 0, "method": "MOCK"}

        response = await self.service.process(request)
        
        # Check Unmatched Claim
        self.assertEqual(len(response.anomalies.claim_without_purchase), 1)
        self.assertEqual(response.anomalies.claim_without_purchase[0].id, "c1")
        
        # Check Unclaimed Purchase
        self.assertEqual(len(response.anomalies.purchase_without_claim), 1)
        self.assertEqual(response.anomalies.purchase_without_claim[0].id, "m1")
        
        print("✅ Test 04 Passed - Anomalies Detected Correctly")

    async def test_05_multi_item_matching(self):
        """Test Case 5: Matching danh sách hỗn hợp"""
        print("\n--- Running Test 05: Multi-item Matching ---")
        request = MatchingRequest(
            request_id="t5",
            claims=[
                ClaimItem(claim_id="c1", service="Drug Alpha", amount=10),
                ClaimItem(claim_id="c2", service="Drug Beta", amount=20)
            ],
            medicine=[
                MedicineItem(medicine_id="m2", service="Drug Beta", amount=20),
                MedicineItem(medicine_id="m1", service="Drug Alpha", amount=10)
            ]
        )
        # Mock trả not found -> Fuzzy match based on text
        self.mock_matcher_instance.match.return_value = {"status": "NOT_FOUND", "data": None, "confidence": 0, "method": "MOCK"}
        
        response = await self.service.process(request)
        
        # Non-DB match -> Weak Match -> Need Review
        self.assertEqual(response.summary.matched_items, 0)
        self.assertEqual(response.summary.need_manual_review, 2)
        
        # Verify correctness
        # c1 -> m1
        match1 = next(r for r in response.results if r.claim_id == "c1")
        self.assertEqual(match1.medicine_id, "m1")
        self.assertEqual(match1.match_status, "weak_match")
        
        # c2 -> m2
        match2 = next(r for r in response.results if r.claim_id == "c2")
        self.assertEqual(match2.medicine_id, "m2")
        print("✅ Test 05 Passed - Multi-item list handled correctly")

if __name__ == '__main__':
    unittest.main()
