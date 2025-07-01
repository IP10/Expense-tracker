import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import uuid
from datetime import datetime, date
from decimal import Decimal

from main import app
from app.auth import get_current_user

# Mock user for testing
MOCK_USER = {
    'id': str(uuid.uuid4()),
    'email': 'test@example.com',
    'full_name': 'Test User',
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

MOCK_CATEGORY = {
    'id': str(uuid.uuid4()),
    'name': 'Food',
    'emoji': '🍽️',
    'is_system': False,
    'user_id': MOCK_USER['id'],
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

MOCK_EXPENSE = {
    'id': str(uuid.uuid4()),
    'user_id': MOCK_USER['id'],
    'amount': Decimal('100.50'),
    'note': 'Lunch at restaurant',
    'date': date.today().isoformat(),
    'category_id': MOCK_CATEGORY['id'],
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return MOCK_USER

@pytest.fixture
def mock_category():
    """Mock category"""
    return MOCK_CATEGORY

@pytest.fixture
def mock_expense():
    """Mock expense"""
    return MOCK_EXPENSE

@pytest.fixture
def authenticated_client(client):
    """Client with authenticated user"""
    def mock_get_current_user():
        return MOCK_USER
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch('app.database.supabase') as mock:
        yield mock