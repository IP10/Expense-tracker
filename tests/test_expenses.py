import pytest
from unittest.mock import Mock, patch
from fastapi import status
from decimal import Decimal
from datetime import date, datetime

class TestExpenseEndpoints:
    @patch('app.routers.expenses.supabase')
    @patch('app.routers.expenses.categorizer')
    def test_create_expense_success(self, mock_categorizer, mock_supabase, authenticated_client, mock_user, mock_category):
        """Test successful expense creation"""
        mock_categorizer.categorize_expense.return_value = mock_category['id']
        
        # Mock category lookup
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_category]
        
        # Mock expense creation
        mock_expense = {
            'id': 'expense_id',
            'user_id': mock_user['id'],
            'amount': 100.50,
            'note': 'Lunch at restaurant',
            'date': date.today().isoformat(),
            'category_id': mock_category['id'],
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [mock_expense]
        
        expense_data = {
            "amount": 100.50,
            "note": "Lunch at restaurant",
            "date": date.today().isoformat()
        }
        
        response = authenticated_client.post("/api/expenses/", json=expense_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == "100.50"
        assert data["note"] == "Lunch at restaurant"
        assert data["category_name"] == "Food"

    @patch('app.routers.expenses.supabase')
    def test_create_expense_invalid_category(self, mock_supabase, authenticated_client):
        """Test expense creation with invalid category"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        expense_data = {
            "amount": 100.50,
            "note": "Lunch at restaurant",
            "date": date.today().isoformat(),
            "category_id": "invalid_category_id"
        }
        
        response = authenticated_client.post("/api/expenses/", json=expense_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Category not found" in response.json()["detail"]

    def test_create_expense_invalid_amount(self, authenticated_client):
        """Test expense creation with invalid amount"""
        expense_data = {
            "amount": -100.50,  # Negative amount
            "note": "Test expense",
            "date": date.today().isoformat()
        }
        
        response = authenticated_client.post("/api/expenses/", json=expense_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_expense_empty_note(self, authenticated_client):
        """Test expense creation with empty note"""
        expense_data = {
            "amount": 100.50,
            "note": "",  # Empty note
            "date": date.today().isoformat()
        }
        
        response = authenticated_client.post("/api/expenses/", json=expense_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.routers.expenses.supabase')
    def test_get_expenses_success(self, mock_supabase, authenticated_client, mock_user):
        """Test successful expense retrieval"""
        mock_expenses = [
            {
                'id': 'expense1',
                'amount': 100.50,
                'note': 'Lunch',
                'date': date.today().isoformat(),
                'category_id': 'cat1',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'categories': {'name': 'Food'}
            },
            {
                'id': 'expense2',
                'amount': 50.25,
                'note': 'Coffee',
                'date': date.today().isoformat(),
                'category_id': 'cat1',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'categories': {'name': 'Food'}
            }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.order.return_value.range.return_value.execute.return_value.data = mock_expenses
        
        response = authenticated_client.get("/api/expenses/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["amount"] == "100.50"
        assert data[1]["amount"] == "50.25"

    @patch('app.routers.expenses.supabase')
    def test_get_expense_by_id_success(self, mock_supabase, authenticated_client, mock_expense):
        """Test successful expense retrieval by ID"""
        mock_expense_with_category = {
            **mock_expense,
            'amount': float(mock_expense['amount']),
            'categories': {'name': 'Food'}
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_expense_with_category]
        
        response = authenticated_client.get(f"/api/expenses/{mock_expense['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == mock_expense["id"]
        assert data["note"] == mock_expense["note"]

    @patch('app.routers.expenses.supabase')
    def test_get_expense_not_found(self, mock_supabase, authenticated_client):
        """Test expense retrieval with non-existent ID"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        response = authenticated_client.get("/api/expenses/nonexistent_id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Expense not found" in response.json()["detail"]

    @patch('app.routers.expenses.supabase')
    @patch('app.routers.expenses.categorizer')
    def test_update_expense_success(self, mock_categorizer, mock_supabase, authenticated_client, mock_expense):
        """Test successful expense update"""
        # Mock existing expense check
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_expense]
        
        # Mock categorization
        mock_categorizer.categorize_expense.return_value = mock_expense['category_id']
        
        # Mock update
        updated_expense = {**mock_expense, 'note': 'Updated lunch', 'amount': 120.75}
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [updated_expense]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {**updated_expense, 'categories': {'name': 'Food'}}
        ]
        
        update_data = {
            "note": "Updated lunch",
            "amount": 120.75
        }
        
        response = authenticated_client.put(f"/api/expenses/{mock_expense['id']}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["note"] == "Updated lunch"
        assert data["amount"] == "120.75"

    @patch('app.routers.expenses.supabase')
    def test_update_expense_not_found(self, mock_supabase, authenticated_client):
        """Test expense update with non-existent ID"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        update_data = {"note": "Updated expense"}
        
        response = authenticated_client.put("/api/expenses/nonexistent_id", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.routers.expenses.supabase')
    def test_delete_expense_success(self, mock_supabase, authenticated_client, mock_expense):
        """Test successful expense deletion"""
        # Mock existing expense check
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{'id': mock_expense['id']}]
        
        # Mock deletion
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [mock_expense]
        
        response = authenticated_client.delete(f"/api/expenses/{mock_expense['id']}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @patch('app.routers.expenses.supabase')
    def test_delete_expense_not_found(self, mock_supabase, authenticated_client):
        """Test expense deletion with non-existent ID"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        response = authenticated_client.delete("/api/expenses/nonexistent_id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.routers.expenses.categorizer')
    def test_preview_categorization(self, mock_categorizer, authenticated_client, mock_supabase, mock_category):
        """Test expense categorization preview"""
        mock_categorizer.categorize_expense.return_value = mock_category['id']
        mock_categorizer.get_category_suggestions.return_value = [
            {"name": "Food", "confidence": 85.5}
        ]
        
        with patch('app.routers.expenses.supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {'name': 'Food', 'emoji': '🍽️'}
            ]
            
            response = authenticated_client.post("/api/expenses/categorize-preview?note=lunch at restaurant")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["category_name"] == "Food"
            assert data["emoji"] == "🍽️"
            assert len(data["suggestions"]) > 0