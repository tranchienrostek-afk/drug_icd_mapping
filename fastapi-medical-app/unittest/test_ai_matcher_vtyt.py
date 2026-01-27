"""
Unit Tests for Task 048: AI Matcher VTYT & Equipment Support.
Validates that AI correctly matches Drugs, Supplements, Medical Supplies, Equipment
and EXCLUDES services (exams, labs, etc).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.mapping_drugs.ai_matcher import AISemanticMatcher

# Mock AI responses for various scenarios
MOCK_RESPONSES = {
    # Case 1: VTYT Basic
    "xlear": {
        "matches": [{
            "claim_id": "c1", "medicine_id": "m1", 
            "claim_service": "Xlear nasal spray", "medicine_service": "Xlear nasal spray",
            "match_status": "matched", "confidence_score": 0.95
        }]
    },
    # Case 2: VTYT Generic
    "bom_tiem": {
        "matches": [{
            "claim_id": "c2", "medicine_id": "m2",
            "claim_service": "Bơm tiêm 5ml", "medicine_service": "Bơm tiêm nhựa 5ml",
            "match_status": "matched", "confidence_score": 0.9
        }]
    },
    # Case 3: Service Exclusion
    "cong_kham": {
        "matches": [{
            "claim_id": "c3", "medicine_id": None,
            "claim_service": "Công khám bệnh", "medicine_service": None,
            "match_status": "no_match", "confidence_score": 0.0,
            "reasoning": "Dịch vụ y tế, không phải thuốc hay vật tư"
        }]
    },
    # Case 4: Lab Exclusion
    "xet_nghiem": {
        "matches": [{
            "claim_id": "c4", "medicine_id": None,
            "claim_service": "Xét nghiệm máu", "medicine_service": None,
            "match_status": "no_match", "confidence_score": 0.0,
            "reasoning": "Dịch vụ xét nghiệm"
        }]
    },
    # Case 5: Drug Basic
    "panadol": {
        "matches": [{
            "claim_id": "c5", "medicine_id": "m5",
            "claim_service": "Panadol", "medicine_service": "Paracetamol 500mg",
            "match_status": "matched", "confidence_score": 0.95
        }]
    },
    # Case 6: Supply vs Drug (Conflict)
    "tim_thuoc": {
        "matches": [{
            "claim_id": "c6", "medicine_id": None,
            "claim_service": "Bơm tiêm", "medicine_service": None, # Should not match "Thuốc tiêm A"
            "match_status": "no_match", "confidence_score": 0.2,
            "reasoning": "Khác loại: Vật tư vs Thuốc"
        }]
    },
    # Case 7: TPCN (Vitamin)
    "vitamin": {
        "matches": [{
            "claim_id": "c7", "medicine_id": "m7",
            "claim_service": "Vitamin C", "medicine_service": "Viên sủi Vitamin C",
            "match_status": "matched", "confidence_score": 0.85
        }]
    },
    # Case 8: TBYT (Equipment)
    "huyet_ap": {
        "matches": [{
            "claim_id": "c8", "medicine_id": "m8",
            "claim_service": "Máy đo danh mục", "medicine_service": "Máy đo huyết áp Omron",
            "match_status": "matched", "confidence_score": 0.8
        }]
    },
    # Case 9: Ambiguous (NaCl)
    "nacl": {
        "matches": [{
            "claim_id": "c9", "medicine_id": "m9",
            "claim_service": "Dung dịch NaCl 0.9%", "medicine_service": "Nước muối sinh lý",
            "match_status": "matched", "confidence_score": 0.9
        }]
    },
    # Case 10: Mixed Batch
    "mixed": {
        "matches": [
            {"claim_id": "c10_1", "medicine_id": "m10_1", "match_status": "matched"},   # Drug
            {"claim_id": "c10_2", "medicine_id": "m10_2", "match_status": "matched"},   # VTYT
            {"claim_id": "c10_3", "medicine_id": None,    "match_status": "no_match"}   # Service
        ]
    }
}

import json

class TestAIMatcherVTYT:
    @pytest.fixture
    def matcher(self):
        """Mock matcher with fake API client."""
        matcher = AISemanticMatcher(api_key="fake")
        matcher.client = AsyncMock()
        return matcher

    def _set_mock_response(self, matcher, key):
        """Helper to set mock response properly using json.dumps."""
        resp_data = {"matches": MOCK_RESPONSES[key]["matches"]}
        # Ensure None becomes null, and quotes are correct
        json_str = json.dumps(resp_data)
        matcher.client.chat.completions.create.return_value.choices[0].message.content = json_str

    @pytest.mark.asyncio
    async def test_01_vtyt_basic(self, matcher):
        """Case 1: VTYT Basic (Xlear)"""
        self._set_mock_response(matcher, "xlear")
        
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c1", "service": "Xlear nasal spray"}],
            medicine=[{"id": "m1", "service": "Xlear nasal spray"}]
        )
        match = res["matches"][0]
        assert match["match_status"] == "matched"
        assert match["medicine_id"] == "m1"

    @pytest.mark.asyncio
    async def test_02_vtyt_generic(self, matcher):
        """Case 2: VTYT Generic (Bơm tiêm)"""
        self._set_mock_response(matcher, "bom_tiem")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c2", "service": "Bơm tiêm 5ml"}],
            medicine=[{"id": "m2", "service": "Bơm tiêm nhựa 5ml"}]
        )
        assert res["matches"][0]["match_status"] == "matched"

    @pytest.mark.asyncio
    async def test_03_service_exclusion(self, matcher):
        """Case 3: Service Exclusion (Công khám)"""
        self._set_mock_response(matcher, "cong_kham")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c3", "service": "Công khám bệnh"}],
            medicine=[{"id": "m5", "service": "Panadol"}]
        )
        assert res["matches"][0]["match_status"] == "no_match"
        assert res["matches"][0]["medicine_id"] is None

    @pytest.mark.asyncio
    async def test_04_lab_exclusion(self, matcher):
        """Case 4: Lab Exclusion (Xét nghiệm máu)"""
        self._set_mock_response(matcher, "xet_nghiem")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c4", "service": "Xét nghiệm máu"}],
            medicine=[{"id": "m_kim", "service": "Kim lấy máu"}]
        )
        assert res["matches"][0]["match_status"] == "no_match"

    @pytest.mark.asyncio
    async def test_05_drug_basic(self, matcher):
        """Case 5: Drug Basic (Panadol)"""
        self._set_mock_response(matcher, "panadol")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c5", "service": "Panadol"}],
            medicine=[{"id": "m5", "service": "Paracetamol"}]
        )
        assert res["matches"][0]["match_status"] == "matched"

    @pytest.mark.asyncio
    async def test_06_supply_vs_drug(self, matcher):
        """Case 6: Supply vs Drug -> Mismatch"""
        self._set_mock_response(matcher, "tim_thuoc")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c6", "service": "Bơm tiêm"}],
            medicine=[{"id": "m_drug_inj", "service": "Thuốc tiêm A"}]
        )
        assert res["matches"][0]["match_status"] == "no_match"

    @pytest.mark.asyncio
    async def test_07_tpcn_vitamin(self, matcher):
        """Case 7: TPCN/Vitamin Support"""
        self._set_mock_response(matcher, "vitamin")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c7", "service": "Vitamin C"}],
            medicine=[{"id": "m7", "service": "Viên sủi Vitamin C"}]
        )
        assert res["matches"][0]["match_status"] == "matched"

    @pytest.mark.asyncio
    async def test_08_equipment(self, matcher):
        """Case 8: Equipment Support"""
        self._set_mock_response(matcher, "huyet_ap")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c8", "service": "Máy đo danh mục"}],
            medicine=[{"id": "m8", "service": "Máy đo huyết áp Omron"}]
        )
        assert res["matches"][0]["match_status"] == "matched"

    @pytest.mark.asyncio
    async def test_09_ambiguous_nacl(self, matcher):
        """Case 9: Ambiguous (NaCl)"""
        self._set_mock_response(matcher, "nacl")
             
        res = await matcher.match_claims_medicine(
            claims=[{"id": "c9", "service": "Dung dịch NaCl 0.9%"}],
            medicine=[{"id": "m9", "service": "Nước muối sinh lý"}]
        )
        assert res["matches"][0]["match_status"] == "matched"

    @pytest.mark.asyncio
    async def test_10_mixed_batch(self, matcher):
        """Case 10: Mixed Batch Processing"""
        self._set_mock_response(matcher, "mixed")
             
        res = await matcher.match_claims_medicine(
            claims=[
                {"id": "c10_1", "service": "Panadol"},
                {"id": "c10_2", "service": "Bông băng"},
                {"id": "c10_3", "service": "Khám nội"}
            ],
            medicine=[
                {"id": "m10_1", "service": "Paracetamol"},
                {"id": "m10_2", "service": "Bông y tế"}
            ]
        )
        assert len(res["matches"]) == 3
        statuses = [m["match_status"] for m in res["matches"]]
        assert "matched" in statuses
        assert "no_match" in statuses
