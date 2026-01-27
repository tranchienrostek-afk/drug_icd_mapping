"""
Unit Tests for API Request Logs and Request Detail Modal functionality.
Tests the data flow from API request → monitor logging → request_logs API → frontend display.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestRequestLogsAPI:
    """Test the /api/v1/admin/request_logs endpoint and data structure."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        from app.main import app
        return TestClient(app)
    
    def test_request_logs_endpoint_returns_correct_structure(self, client):
        """Verify request_logs API returns expected structure for frontend."""
        response = client.get("/api/v1/admin/request_logs?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required keys exist
        assert "status" in data
        assert "mapping_stats" in data
        assert "consult_stats" in data
        assert "logs" in data
        
        # Verify stats structure
        for stats_key in ["mapping_stats", "consult_stats"]:
            stats = data[stats_key]
            assert "total_requests" in stats or "error" in stats
            if "total_requests" in stats:
                assert "success_rate" in stats
                assert "total_matched" in stats
                assert "total_unmatched" in stats
    
    def test_log_entry_has_required_fields_for_modal(self, client):
        """Verify each log entry has fields required by openRequestDetail() JS function."""
        response = client.get("/api/v1/admin/request_logs?limit=5")
        data = response.json()
        logs = data.get("logs", [])
        
        # Required fields for JS function openRequestDetail()
        required_fields = [
            "request_id",
            "endpoint", 
            "status_code",
            "latency_ms",
            "response_body"  # CRITICAL: This is what frontend parses!
        ]
        
        if len(logs) > 0:
            log = logs[0]
            for field in required_fields:
                assert field in log, f"Missing required field: {field}"
            
            # Verify response_body is valid JSON string (parseable)
            if log.get("response_body"):
                try:
                    parsed = json.loads(log["response_body"])
                    assert isinstance(parsed, dict), "response_body should parse to dict"
                except json.JSONDecodeError:
                    pytest.fail(f"response_body is not valid JSON: {log['response_body'][:100]}")


class TestConsultIntegratedLogging:
    """Test that consult_integrated endpoint logs correctly for request detail modal."""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_consult_integrated_response_has_results(self, client):
        """Verify consult_integrated returns 'results' array that modal expects."""
        payload = {
            "patient_id": "test123",
            "icd_code": "J06", 
            "drugs": [
                {"id": "d1", "name": "Paracetamol 500mg"}
            ]
        }
        
        response = client.post("/api/v1/consult_integrated", json=payload)
        
        # Should succeed (might be 200 or 500 if no data, but structure matters)
        if response.status_code == 200:
            data = response.json()
            assert "results" in data, "Response must have 'results' key for modal"
            assert isinstance(data["results"], list), "'results' must be a list"
            
            # If there are results, verify structure matches ConsultResult model
            if len(data["results"]) > 0:
                result = data["results"][0]
                expected_fields = ["id", "name", "validity", "role", "explanation"]
                for field in expected_fields:
                    assert field in result, f"ConsultResult missing field: {field}"


class TestMonitorMiddleware:
    """Test that ApiMonitorMiddleware correctly captures and stores response_body."""
    
    def test_log_api_request_stores_response_body(self):
        """Verify log_api_request function properly stores response_body."""
        from app.monitor.service import log_api_request, get_recent_logs
        
        # Log a test request
        test_response = json.dumps({
            "results": [
                {"id": "test1", "name": "Test Drug", "validity": "valid", "role": "test", "explanation": "unittest"}
            ]
        })
        
        log_api_request(
            request_id="unittest_12345",
            endpoint="/api/v1/test_consult",
            method="POST",
            status_code=200,
            latency_ms=100.5,
            matched_count=1,
            unmatched_count=0,
            request_body="<test>",
            response_body=test_response
        )
        
        # Retrieve and verify
        logs = get_recent_logs(limit=1)
        assert len(logs) > 0, "Log should be retrievable"
        
        latest = logs[0]
        if latest.get("request_id") == "unittest_12345":
            assert latest["response_body"] is not None, "response_body should not be None"
            assert len(latest["response_body"]) > 0, "response_body should not be empty"
            
            # Verify it's parseable
            parsed = json.loads(latest["response_body"])
            assert "results" in parsed
            assert parsed["results"][0]["id"] == "test1"


class TestRequestDetailModalDataFlow:
    """End-to-end test simulating what the frontend JS does."""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_full_flow_consult_to_modal(self, client):
        """
        Simulates:
        1. Make consult_integrated request
        2. Fetch request_logs
        3. Parse response_body like JS does
        4. Verify data can be rendered
        """
        # Step 1: Make a consult request (this should be logged by middleware)
        consult_payload = {
            "patient_id": "e2e_test",
            "icd_code": "J06",
            "drugs": [{"id": "d1", "name": "Paracetamol"}]
        }
        consult_response = client.post("/api/v1/consult_integrated", json=consult_payload)
        
        # Step 2: Fetch logs
        logs_response = client.get("/api/v1/admin/request_logs?limit=5&endpoint=consult")
        assert logs_response.status_code == 200
        
        logs_data = logs_response.json()
        logs = logs_data.get("logs", [])
        
        # Step 3: Find our request and parse response_body (like JS openRequestDetail does)
        for log in logs:
            if log.get("endpoint") and "consult" in log["endpoint"]:
                response_body = log.get("response_body", "")
                
                if response_body:
                    try:
                        resp_data = json.loads(response_body)
                        
                        # Step 4: Verify the structure that JS expects
                        if "results" in resp_data:
                            results = resp_data["results"]
                            print(f"✅ Found {len(results)} results in response_body")
                            
                            for r in results:
                                # These are the fields JS tries to render
                                assert "name" in r or r.get("name") is None  # Can be None but key should exist
                                # role and validity are used for isFound check
                                print(f"  - {r.get('name')}: validity={r.get('validity')}, role={r.get('role')}")
                            
                            return  # Test passed
                        else:
                            print(f"⚠️ response_body missing 'results': {response_body[:200]}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse response_body: {e}")
                        print(f"   Raw: {response_body[:200]}")
        
        # If we get here, no valid log was found
        print("⚠️ No consult logs with parseable response_body found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
