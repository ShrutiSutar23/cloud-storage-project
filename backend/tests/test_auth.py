from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend is running"}

def test_register_and_login():
    # Use a random-ish email so re-running tests doesn't clash with "already registered"
    import uuid
    test_email = f"pytest_{uuid.uuid4().hex[:8]}@example.com"

    register_response = client.post("/auth/register", json={
        "email": test_email,
        "password": "testpass123",
        "name": "Pytest User"
    })
    assert register_response.status_code == 200
    assert register_response.json()["email"] == test_email

    login_response = client.post("/auth/login", json={
        "email": test_email,
        "password": "testpass123"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

def test_login_wrong_password():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401