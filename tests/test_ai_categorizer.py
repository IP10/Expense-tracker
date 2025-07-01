import pytest
from unittest.mock import Mock, patch
from app.ai_categorizer import ExpenseCategorizer

class TestExpenseCategorizer:
    def setup_method(self):
        """Set up test categorizer"""
        self.categorizer = ExpenseCategorizer()

    def test_clean_text(self):
        """Test text cleaning function"""
        text = "  Hello, World! This is a TEST...  "
        cleaned = self.categorizer._clean_text(text)
        assert cleaned == "hello world this is a test"

    def test_calculate_category_score_exact_match(self):
        """Test category scoring with exact keyword match"""
        note = "lunch at restaurant"
        score = self.categorizer._calculate_category_score(note, "Food")
        assert score > 0

    def test_calculate_category_score_partial_match(self):
        """Test category scoring with partial keyword match"""
        note = "food delivery"
        score = self.categorizer._calculate_category_score(note, "Food")
        assert score > 0

    def test_calculate_category_score_no_match(self):
        """Test category scoring with no keyword match"""
        note = "random text without food keywords"
        score = self.categorizer._calculate_category_score(note, "Food")
        assert score == 0

    def test_get_category_suggestions(self):
        """Test getting category suggestions"""
        note = "lunch at cafe with coffee"
        suggestions = self.categorizer.get_category_suggestions(note)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all("name" in suggestion and "confidence" in suggestion for suggestion in suggestions)
        assert suggestions[0]["name"] == "Food"  # Should be highest scored

    @patch('app.ai_categorizer.supabase')
    def test_categorize_expense_success(self, mock_supabase):
        """Test successful expense categorization"""
        user_id = "test_user_id"
        note = "lunch at restaurant"
        
        # Mock categories
        mock_categories = [
            {"name": "Food", "id": "food_id"},
            {"name": "Transport", "id": "transport_id"},
            {"name": "Other", "id": "other_id"}
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_categories
        
        result = self.categorizer.categorize_expense(note, user_id)
        
        assert result == "food_id"

    @patch('app.ai_categorizer.supabase')
    def test_categorize_expense_fallback_to_other(self, mock_supabase):
        """Test expense categorization fallback to 'Other' category"""
        user_id = "test_user_id"
        note = "random unrecognizable expense"
        
        # Mock categories
        mock_categories = [
            {"name": "Food", "id": "food_id"},
            {"name": "Transport", "id": "transport_id"},
            {"name": "Other", "id": "other_id"}
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_categories
        
        result = self.categorizer.categorize_expense(note, user_id)
        
        assert result == "other_id"

    @patch('app.ai_categorizer.supabase')
    def test_categorize_expense_no_categories(self, mock_supabase):
        """Test expense categorization when no categories exist"""
        user_id = "test_user_id"
        note = "lunch at restaurant"
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = self.categorizer.categorize_expense(note, user_id)
        
        assert result is None

    @patch('app.ai_categorizer.supabase')
    def test_categorize_expense_database_error(self, mock_supabase):
        """Test expense categorization with database error"""
        user_id = "test_user_id"
        note = "lunch at restaurant"
        
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.categorizer.categorize_expense(note, user_id)
        
        assert result is None

    def test_food_category_keywords(self):
        """Test food category keyword matching"""
        food_notes = [
            "lunch at restaurant",
            "coffee and snacks",
            "grocery shopping",
            "ordered from swiggy",
            "pizza delivery",
            "breakfast at hotel"
        ]
        
        for note in food_notes:
            score = self.categorizer._calculate_category_score(note, "Food")
            assert score > 0, f"Failed to categorize food note: {note}"

    def test_transport_category_keywords(self):
        """Test transport category keyword matching"""
        transport_notes = [
            "uber ride to office",
            "bus ticket booking",
            "petrol for car",
            "auto rickshaw fare",
            "flight to mumbai",
            "ola cab payment"
        ]
        
        for note in transport_notes:
            score = self.categorizer._calculate_category_score(note, "Transport")
            assert score > 0, f"Failed to categorize transport note: {note}"

    def test_entertainment_category_keywords(self):
        """Test entertainment category keyword matching"""
        entertainment_notes = [
            "movie ticket",
            "netflix subscription",
            "concert tickets",
            "gaming purchase",
            "gym membership",
            "spotify premium"
        ]
        
        for note in entertainment_notes:
            score = self.categorizer._calculate_category_score(note, "Entertainment")
            assert score > 0, f"Failed to categorize entertainment note: {note}"

    def test_shopping_category_keywords(self):
        """Test shopping category keyword matching"""
        shopping_notes = [
            "clothes from myntra",
            "amazon purchase",
            "new laptop",
            "mobile phone",
            "furniture shopping",
            "electronics store"
        ]
        
        for note in shopping_notes:
            score = self.categorizer._calculate_category_score(note, "Shopping")
            assert score > 0, f"Failed to categorize shopping note: {note}"

    def test_healthcare_category_keywords(self):
        """Test healthcare category keyword matching"""
        healthcare_notes = [
            "doctor visit",
            "pharmacy medicines",
            "dental checkup",
            "hospital bill",
            "blood test",
            "eye examination"
        ]
        
        for note in healthcare_notes:
            score = self.categorizer._calculate_category_score(note, "Healthcare")
            assert score > 0, f"Failed to categorize healthcare note: {note}"

    def test_utilities_category_keywords(self):
        """Test utilities category keyword matching"""
        utilities_notes = [
            "electricity bill",
            "internet payment",
            "mobile recharge",
            "water bill",
            "gas connection",
            "maintenance charges"
        ]
        
        for note in utilities_notes:
            score = self.categorizer._calculate_category_score(note, "Utilities")
            assert score > 0, f"Failed to categorize utilities note: {note}"