from fastapi.testclient import TestClient
from app.main import app  # Import FastAPI app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200

# tests/test_neo4j.py
import requests

def test_neo4j_availability():
    # Attempt to connect to the Neo4j HTTP endpoint.
    # For Neo4j with authentication disabled, you'll likely get a login page or a specific API response.
    response = requests.get("http://localhost:7474")
    assert response.status_code == 200