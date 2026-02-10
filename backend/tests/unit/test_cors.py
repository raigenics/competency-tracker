"""
Unit tests for CORS middleware configuration.

ROOT CAUSE of recurring CORS bugs:
- Frontend dev server port changes (3000 -> 3001 -> 3002, etc.)
- Hardcoded allow_origins list misses the new port
- All API calls fail with "No 'Access-Control-Allow-Origin' header"

FIX: Use allow_origin_regex in development to allow ANY localhost port.
This regex matches: http://localhost:3000, http://127.0.0.1:5173, etc.

MANUAL VERIFICATION (run from terminal):
  curl -i -X OPTIONS "http://localhost:8000/api/dashboard/org-skill-coverage" \\
    -H "Origin: http://localhost:3002" \\
    -H "Access-Control-Request-Method: GET"
  # Expected: Access-Control-Allow-Origin: http://localhost:3002, 200 OK

These tests ensure CORS is properly configured for all dev origins.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestCorsMiddleware:
    """Tests for CORS middleware configuration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.mark.parametrize("origin", [
        # localhost variants - common dev ports
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",  # REGRESSION: This was missing, causing CORS failures
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Another common port
        # 127.0.0.1 variants - must also work
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ])
    def test_cors_allows_dev_origins(self, client, origin):
        """
        CORS should allow requests from all localhost/127.0.0.1 origins.
        
        Regression test: Frontend port changed to 3002, CORS was not updated.
        Fix: Use allow_origin_regex to match any localhost port.
        """
        response = client.options(
            "/api/employees",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert response.status_code == 200, f"Preflight failed for origin {origin}"
        assert response.headers.get("access-control-allow-origin") == origin, \
            f"Origin {origin} not allowed - got {response.headers.get('access-control-allow-origin')}"
        assert "GET" in response.headers.get("access-control-allow-methods", "")

    def test_cors_preflight_includes_all_methods(self, client):
        """Preflight should allow all HTTP methods."""
        response = client.options(
            "/api/employees",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "POST",
            }
        )
        
        allowed = response.headers.get("access-control-allow-methods", "")
        for method in ["GET", "POST", "PUT", "DELETE", "OPTIONS"]:
            assert method in allowed, f"Method {method} should be allowed"

    def test_cors_allows_credentials(self, client):
        """CORS should allow credentials for auth cookies."""
        response = client.options(
            "/api/employees",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_get_includes_headers(self, client):
        """GET requests should include CORS headers in response."""
        response = client.get(
            "/api/employees/?page=1&size=10",
            headers={
                "Origin": "http://localhost:3001",
                "X-RBAC-Role": "SUPER_ADMIN",
            }
        )
        
        # Response should include CORS headers regardless of status
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3001"

    def test_cors_rejects_unknown_origin(self, client):
        """CORS should not include allow header for unknown origins."""
        response = client.options(
            "/api/employees",
            headers={
                "Origin": "http://malicious-site.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # Unknown origins should not get the allow-origin header
        # (FastAPI CORS middleware returns 400 for unmatched origins)
        allow_origin = response.headers.get("access-control-allow-origin")
        assert allow_origin is None or allow_origin != "http://malicious-site.com"

    @pytest.mark.parametrize("endpoint", [
        "/api/dashboard/org-skill-coverage",  # Specifically mentioned in bug report
        "/api/dropdown/sub-segments",          # Specifically mentioned in bug report
        "/api/employees",
    ])
    def test_cors_preflight_port_3002_on_various_endpoints(self, client, endpoint):
        """
        REGRESSION TEST: Port 3002 must work on all endpoints.
        
        This test specifically covers the endpoints that were failing:
        - /api/dashboard/org-skill-coverage
        - /api/dropdown/sub-segments
        """
        response = client.options(
            endpoint,
            headers={
                "Origin": "http://localhost:3002",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert response.status_code == 200, \
            f"Preflight failed for {endpoint} with origin localhost:3002"
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3002", \
            f"Origin not reflected for {endpoint}"
