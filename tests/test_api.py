from fastapi.testclient import TestClient
from auramed.api import app
import os
import pytest

client = TestClient(app)

def test_api_key_required():
    # Simulate SaaS environment
    os.environ["REQUIRE_API_KEY"] = "true"
    
    response = client.post(
        "/api/v1/scan",
        data={"raw_barcode": "(01)04150000000000(17)280500(10)CH123(21)SN987"}
    )
    
    assert response.status_code == 401
    assert "API Key fehlt" in response.json()["detail"]
    
def test_rate_limiting():
    # Simulate Local open source environment to bypass API Key
    os.environ["REQUIRE_API_KEY"] = "false"
    
    # We allow 30 requests per minute. Let's make 32 requests.
    for i in range(31):
        response = client.post(
            "/api/v1/scan",
            data={"raw_barcode": "invalid_string"}
        )
    
    # The 32nd request should be rate limited
    response = client.post(
        "/api/v1/scan",
        data={"raw_barcode": "invalid_string"}
    )
    
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["error"]
