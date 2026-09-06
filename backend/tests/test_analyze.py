from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_analyze_no_file():
    response = client.post("/analyze")
    assert response.status_code == 422 # FastAPI validation error for missing field

def test_analyze_empty_file():
    response = client.post(
        "/analyze",
        files={"file": ("empty.wav", b"")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]
