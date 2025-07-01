import pytest
from unittest.mock import Mock, patch
from fastapi import status
from app.auth import verify_password, get_password_hash, create_access_token, verify_token
from app.models import UserRegister, UserLogin

class TestPasswordHashing:
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

class TestTokenCreation:
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "test_user_id"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

class TestAuthEndpoints:
    @patch('app.routers.auth.supabase')
    def test_register_success(self, mock_supabase, client):
        """Test successful user registration"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {
                'id': 'test_user_id',
                'email': 'test@example.com',
                'full_name': 'Test User'
            }
        ]
        
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.supabase')
    def test_register_duplicate_email(self, mock_supabase, client):
        """Test registration with duplicate email"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'existing_user'}
        ]
        
        user_data = {
            "email": "existing@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_data(self, client):
        """Test registration with invalid data"""
        user_data = {
            "email": "invalid-email",
            "password": "123",  # Too short
            "full_name": ""
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.routers.auth.supabase')
    @patch('app.routers.auth.verify_password')
    def test_login_success(self, mock_verify_password, mock_supabase, client):
        """Test successful login"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'id': 'test_user_id',
                'email': 'test@example.com',
                'password_hash': 'hashed_password'
            }
        ]
        mock_verify_password.return_value = True
        
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.supabase')
    def test_login_user_not_found(self, mock_supabase, client):
        """Test login with non-existent user"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]

    @patch('app.routers.auth.supabase')
    @patch('app.routers.auth.verify_password')
    def test_login_wrong_password(self, mock_verify_password, mock_supabase, client):
        """Test login with wrong password"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'id': 'test_user_id',
                'email': 'test@example.com',
                'password_hash': 'hashed_password'
            }
        ]
        mock_verify_password.return_value = False
        
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]

    def test_get_current_user_info(self, authenticated_client, mock_user):
        """Test getting current user info"""
        response = authenticated_client.get("/api/auth/me")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == mock_user["id"]
        assert data["email"] == mock_user["email"]
        assert data["full_name"] == mock_user["full_name"]