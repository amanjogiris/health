"""Example test file for the Health Services API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app, get_db
from app.model import Base


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_db():
    """Create test database fixture."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def client():
    """Create test client fixture."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuthenticationEndpoints:
    """Test authentication endpoints."""
    
    def test_register_patient(self, client):
        """Test patient registration."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "role": "patient",
            "mobile_no": "9876543210",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "john@example.com"
        assert data["user"]["role"] == "patient"
        assert "access_token" in data
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "role": "patient",
        }
        
        # Register first user
        client.post("/api/v1/auth/register", json=user_data)
        
        # Try to register with same email
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register user
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "role": "patient",
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Login
        login_data = {
            "email": "john@example.com",
            "password": "SecurePass123",
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "john@example.com"
    
    def test_login_invalid_password(self, client):
        """Test login with invalid password."""
        # Register user
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "role": "patient",
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Login with wrong password
        login_data = {
            "email": "john@example.com",
            "password": "WrongPassword",
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401


class TestValidationSchemas:
    """Test request validation."""
    
    def test_invalid_email_format(self, client):
        """Test invalid email format."""
        user_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "password": "SecurePass123",
            "role": "patient",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_weak_password(self, client):
        """Test weak password validation."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "weak",  # Less than 8 chars
            "role": "patient",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        """Test missing required fields."""
        user_data = {
            "name": "John Doe",
            # Missing email and password
            "role": "patient",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error


class TestDoctorEndpoints:
    """Test doctor management endpoints."""
    
    def test_create_doctor_requires_admin(self, client):
        """Test that creating doctor requires admin role."""
        doctor_data = {
            "user_id": 1,
            "clinic_id": 1,
            "specialty": "Cardiology",
            "license_number": "LIC123456",
            "experience_years": 5,
        }
        response = client.post("/api/v1/doctors", json=doctor_data)
        # Without token, should return 401
        assert response.status_code == 401


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_not_found(self, client):
        """Test 404 error for non-existent resource."""
        response = client.get("/api/v1/patients/99999")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
