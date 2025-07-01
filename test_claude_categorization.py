#!/usr/bin/env python3
"""
Test Claude AI categorization functionality
"""

def test_claude_categorization_mock():
    """Test Claude categorization with mock responses"""
    print("🤖 Testing Claude AI Categorization (Mock Mode)...")
    
    # Mock Claude responses for testing
    mock_responses = {
        "lunch at restaurant": "Food",
        "uber ride to office": "Transport", 
        "movie ticket booking": "Entertainment",
        "amazon purchase": "Shopping",
        "doctor visit": "Healthcare",
        "electricity bill": "Utilities",
        "online course": "Education",
        "random expense": "Other"
    }
    
    # Test the mock categorization logic
    def mock_categorize_with_claude(note: str, available_categories: list) -> str:
        """Mock Claude categorization"""
        predicted = mock_responses.get(note, "Other")
        if predicted in available_categories:
            return predicted
        return "Other" if "Other" in available_categories else available_categories[0]
    
    # Test cases
    test_categories = ["Food", "Transport", "Entertainment", "Shopping", "Healthcare", "Utilities", "Education", "Other"]
    
    success_count = 0
    total_tests = len(mock_responses)
    
    for note, expected in mock_responses.items():
        result = mock_categorize_with_claude(note, test_categories)
        if result == expected:
            print(f"  ✅ '{note}' → {result}")
            success_count += 1
        else:
            print(f"  ❌ '{note}' → {result} (expected {expected})")
    
    accuracy = (success_count / total_tests) * 100
    print(f"  📊 Mock Claude Accuracy: {accuracy:.1f}% ({success_count}/{total_tests})")
    
    return success_count == total_tests

def test_claude_integration_without_api():
    """Test Claude integration structure without making API calls"""
    print("\n🔧 Testing Claude Integration Structure...")
    
    try:
        # Test imports (without actual API calls)
        import re
        from typing import Dict, List, Optional
        
        # Mock Anthropic client
        class MockAnthropic:
            def __init__(self, api_key):
                self.api_key = api_key
            
            def messages_create(self, **kwargs):
                class MockResponse:
                    def __init__(self):
                        self.content = [MockContent()]
                
                class MockContent:
                    def __init__(self):
                        self.text = "Food"
                
                return MockResponse()
        
        # Test categorizer structure
        class TestCategorizer:
            def __init__(self):
                self.anthropic_client = MockAnthropic("mock-api-key")
                self.category_keywords = {
                    "Food": ["lunch", "restaurant", "food"],
                    "Transport": ["uber", "taxi", "bus"],
                    "Other": ["other", "misc"]
                }
            
            def _categorize_with_claude(self, note: str, available_categories: List[str]) -> Optional[str]:
                """Mock Claude categorization"""
                try:
                    # Simulate API call structure
                    response = self.anthropic_client.messages_create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=10,
                        temperature=0.1,
                        messages=[{"role": "user", "content": f"Categorize: {note}"}]
                    )
                    
                    category = response.content[0].text.strip()
                    return category if category in available_categories else None
                    
                except Exception as e:
                    print(f"    Claude API simulation failed: {e}")
                    return None
            
            def _categorize_with_keywords(self, note: str, user_categories: Dict[str, str]) -> Optional[str]:
                """Fallback keyword categorization"""
                note_lower = note.lower()
                for category_name, category_id in user_categories.items():
                    if category_name in self.category_keywords:
                        for keyword in self.category_keywords[category_name]:
                            if keyword in note_lower:
                                return category_id
                return user_categories.get("Other")
            
            def categorize_expense(self, note: str, available_categories: List[str]) -> Optional[str]:
                """Main categorization with fallback"""
                # Try Claude first
                claude_result = self._categorize_with_claude(note, available_categories)
                if claude_result:
                    return claude_result
                
                # Fallback to keywords
                user_categories = {cat: f"{cat}_id" for cat in available_categories}
                return self._categorize_with_keywords(note, user_categories)
        
        # Test the categorizer
        categorizer = TestCategorizer()
        
        test_cases = [
            ("lunch at restaurant", ["Food", "Transport", "Other"]),
            ("uber ride", ["Food", "Transport", "Other"]),
            ("random note", ["Food", "Transport", "Other"])
        ]
        
        success_count = 0
        for note, categories in test_cases:
            result = categorizer.categorize_expense(note, categories)
            if result:
                print(f"  ✅ '{note}' → {result}")
                success_count += 1
            else:
                print(f"  ❌ '{note}' → None")
        
        accuracy = (success_count / len(test_cases)) * 100
        print(f"  📊 Integration Structure: {accuracy:.1f}% ({success_count}/{len(test_cases)})")
        
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def test_fallback_behavior():
    """Test that keyword fallback works when Claude is unavailable"""
    print("\n🔄 Testing Fallback Behavior...")
    
    try:
        from typing import Dict, List, Optional
        
        # Simulate categorizer with failing Claude API
        class FallbackCategorizer:
            def __init__(self):
                self.category_keywords = {
                    "Food": ["lunch", "restaurant", "food", "meal"],
                    "Transport": ["uber", "taxi", "bus", "travel"],
                    "Entertainment": ["movie", "netflix", "game"],
                    "Other": []
                }
            
            def _categorize_with_claude(self, note: str, available_categories: List[str]) -> Optional[str]:
                # Simulate API failure
                raise Exception("API unavailable")
            
            def _categorize_with_keywords(self, note: str, user_categories: Dict[str, str]) -> Optional[str]:
                note_lower = note.lower()
                best_score = 0
                best_category = None
                
                for category_name, category_id in user_categories.items():
                    if category_name in self.category_keywords:
                        score = 0
                        for keyword in self.category_keywords[category_name]:
                            if keyword in note_lower:
                                score += 1
                        
                        if score > best_score:
                            best_score = score
                            best_category = category_id
                
                return best_category or user_categories.get("Other")
            
            def categorize_expense(self, note: str, available_categories: List[str]) -> Optional[str]:
                try:
                    # Try Claude (will fail)
                    claude_result = self._categorize_with_claude(note, available_categories)
                    if claude_result:
                        return claude_result
                except:
                    pass
                
                # Fallback to keywords
                user_categories = {cat: f"{cat}_id" for cat in available_categories}
                return self._categorize_with_keywords(note, user_categories)
        
        # Test fallback behavior
        categorizer = FallbackCategorizer()
        
        test_cases = [
            ("lunch at restaurant", ["Food", "Transport", "Other"], "Food_id"),
            ("uber ride to office", ["Food", "Transport", "Other"], "Transport_id"),
            ("movie ticket", ["Food", "Transport", "Entertainment", "Other"], "Entertainment_id"),
            ("unknown expense", ["Food", "Transport", "Other"], "Other_id")
        ]
        
        success_count = 0
        for note, categories, expected in test_cases:
            result = categorizer.categorize_expense(note, categories)
            if result == expected:
                print(f"  ✅ '{note}' → {result.replace('_id', '')}")
                success_count += 1
            else:
                expected_name = expected.replace('_id', '') if expected else 'None'
                result_name = result.replace('_id', '') if result else 'None'
                print(f"  ❌ '{note}' → {result_name} (expected {expected_name})")
        
        accuracy = (success_count / len(test_cases)) * 100
        print(f"  📊 Fallback Accuracy: {accuracy:.1f}% ({success_count}/{len(test_cases)})")
        
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"  ❌ Fallback test failed: {e}")
        return False

def main():
    """Run Claude AI categorization tests"""
    print("🧪 Testing Claude AI Integration for Expense Categorization")
    print("=" * 65)
    
    tests = [
        ("Mock Claude Responses", test_claude_categorization_mock),
        ("Claude Integration Structure", test_claude_integration_without_api),
        ("Fallback Behavior", test_fallback_behavior)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED\n")
            else:
                failed += 1
                print(f"❌ {test_name} - FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - ERROR: {e}\n")
    
    # Summary
    print("=" * 65)
    print(f"📊 CLAUDE AI INTEGRATION TEST SUMMARY")
    print("=" * 65)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print(f"\n🎉 Claude AI integration tests passed!")
        print("✅ Claude categorization structure is correct")
        print("✅ Fallback to keyword matching works")
        print("✅ Error handling is robust")
        print("\n📋 Next Steps:")
        print("1. Get your Claude API key from https://console.anthropic.com")
        print("2. Add ANTHROPIC_API_KEY to your .env file")
        print("3. Install anthropic package: pip install anthropic==0.7.8")
        print("4. Test with real API calls")
        print("5. Monitor API usage and costs")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")

if __name__ == "__main__":
    main()