"""
Unit Tests for Task 047: Consult Integrated TDV Fallback Logic.
Tests Vote & Promote logic: TDV > AI, TDV null = agrees with AI.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.service.consultation_service import ConsultationService


class TestGetValidRole:
    """Test the _get_valid_role helper function."""
    
    @pytest.fixture
    def service(self):
        """Create ConsultationService with mocked DB."""
        with patch('app.service.consultation_service.DatabaseCore'):
            with patch('app.service.consultation_service.KBFuzzyMatchService'):
                return ConsultationService()
    
    def test_returns_valid_role(self, service):
        """Valid roles should be returned as-is."""
        assert service._get_valid_role("main drug") == "main drug"
        assert service._get_valid_role("secondary drug") == "secondary drug"
        assert service._get_valid_role("supplement") == "supplement"
    
    def test_returns_none_for_null_values(self, service):
        """Empty and null values should return None."""
        assert service._get_valid_role(None) is None
        assert service._get_valid_role("") is None
        assert service._get_valid_role("null") is None
        assert service._get_valid_role("none") is None
        assert service._get_valid_role("None") is None
    
    def test_returns_none_for_valid_keyword(self, service):
        """'valid' is not a role, just confirmation - should return None."""
        assert service._get_valid_role("valid") is None
        assert service._get_valid_role("VALID") is None
        assert service._get_valid_role("Valid") is None
    
    def test_returns_none_for_invalid_keyword(self, service):
        """'invalid' and 'unknown' are not informative - should return None."""
        assert service._get_valid_role("invalid") is None
        assert service._get_valid_role("unknown") is None
    
    def test_cleans_json_artifacts(self, service):
        """Should parse JSON arrays and extract actual role."""
        # JSON array format: [category, validity, role]
        assert service._clean_role_string('["drug", "valid", "main drug"]') == "main drug"
        assert service._clean_role_string('["drug", "valid", "secondary drug"]') == "secondary drug"
        assert service._clean_role_string('["nodrug", "supplement"]') == "supplement"
        assert service._clean_role_string('["drug", "invalid"]') == ""  # No role, just invalid
        
    def test_handles_dirty_concatenated_strings(self, service):
        """Should handle badly formatted strings with commas."""
        # This was causing the bug: 'drug, drug, valid, main drug, main drug'
        assert service._clean_role_string("drug, valid, main drug") == "main drug"
        assert service._clean_role_string("drug, drug, valid, secondary drug") == "secondary drug"
        
    def test_handles_plain_strings(self, service):
        """Plain role strings should pass through."""
        assert service._clean_role_string("main drug") == "main drug"
        assert service._clean_role_string("supplement") == "supplement"


class TestTDVFallbackLogic:
    """Test Vote & Promote logic: TDV > AI, TDV null = agrees with AI."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock ConsultRequest."""
        request = MagicMock()
        request.items = [MagicMock(id="d1", name="Paracetamol")]
        request.diagnoses = [MagicMock(code="J06", name="Viêm họng")]
        return request
    
    @pytest.fixture
    def service_with_mock_kb(self):
        """Create service with mocked KB matcher."""
        with patch('app.service.consultation_service.DatabaseCore'):
            with patch('app.service.consultation_service.KBFuzzyMatchService') as MockKB:
                service = ConsultationService()
                service.kb_matcher = MagicMock()
                return service
    
    @pytest.mark.asyncio
    async def test_tdv_has_value_uses_tdv(self, service_with_mock_kb, mock_request):
        """When TDV has valid value, use TDV."""
        service_with_mock_kb.kb_matcher.find_best_match_with_icd.return_value = {
            'tdv_feedback': 'main drug',
            'treatment_type': 'secondary drug',
            'match_method': 'exact'
        }
        
        results = await service_with_mock_kb.process_integrated_consultation(mock_request)
        
        assert len(results) == 1
        assert results[0]['role'] == 'main drug'
        assert results[0]['source'] == 'INTERNAL_KB_TDV'
    
    @pytest.mark.asyncio
    async def test_tdv_null_uses_ai(self, service_with_mock_kb, mock_request):
        """When TDV is null, fallback to AI (TDV agrees with AI)."""
        service_with_mock_kb.kb_matcher.find_best_match_with_icd.return_value = {
            'tdv_feedback': None,
            'treatment_type': 'secondary drug',
            'match_method': 'fuzzy(85%)'
        }
        
        results = await service_with_mock_kb.process_integrated_consultation(mock_request)
        
        assert len(results) == 1
        assert results[0]['role'] == 'secondary drug'
        assert results[0]['source'] == 'INTERNAL_KB_AI'
    
    @pytest.mark.asyncio
    async def test_tdv_valid_uses_ai(self, service_with_mock_kb, mock_request):
        """When TDV='valid' (not a role), fallback to AI."""
        service_with_mock_kb.kb_matcher.find_best_match_with_icd.return_value = {
            'tdv_feedback': 'valid',  # This is NOT a role
            'treatment_type': 'main drug',
            'match_method': 'exact'
        }
        
        results = await service_with_mock_kb.process_integrated_consultation(mock_request)
        
        assert len(results) == 1
        assert results[0]['role'] == 'main drug'
        assert results[0]['source'] == 'INTERNAL_KB_AI'
    
    @pytest.mark.asyncio
    async def test_tdv_empty_uses_ai(self, service_with_mock_kb, mock_request):
        """When TDV is empty string, fallback to AI."""
        service_with_mock_kb.kb_matcher.find_best_match_with_icd.return_value = {
            'tdv_feedback': '',
            'treatment_type': 'supplement',
            'match_method': 'partial'
        }
        
        results = await service_with_mock_kb.process_integrated_consultation(mock_request)
        
        assert len(results) == 1
        assert results[0]['role'] == 'supplement'
        assert results[0]['source'] == 'INTERNAL_KB_AI'
    
    @pytest.mark.asyncio
    async def test_no_kb_match_returns_unknown(self, service_with_mock_kb, mock_request):
        """When no KB match found, return unknown (keep old format)."""
        service_with_mock_kb.kb_matcher.find_best_match_with_icd.return_value = None
        
        results = await service_with_mock_kb.process_integrated_consultation(mock_request)
        
        assert len(results) == 1
        assert results[0]['id'] == 'd1'
        assert results[0]['validity'] == 'unknown'
        assert results[0]['source'] == 'INTERNAL_KB_EMPTY'
    
    @pytest.mark.asyncio
    async def test_both_null_returns_unknown(self, service_with_mock_kb, mock_request):
        """When both TDV and AI are null, return unknown."""
        service_with_mock_kb.kb_matcher.find_best_match_with_icd.return_value = {
            'tdv_feedback': None,
            'treatment_type': None,
            'match_method': 'exact'
        }
        
        results = await service_with_mock_kb.process_integrated_consultation(mock_request)
        
        assert len(results) == 1
        assert results[0]['validity'] == 'unknown'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
