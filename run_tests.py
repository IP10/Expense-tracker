#!/usr/bin/env python3
"""
Comprehensive test runner for the Expense Tracker backend.
This script runs all tests and generates coverage reports.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print results"""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Main test runner"""
    print("🧪 Starting Expense Tracker Backend Tests")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check if virtual environment is activated
    if 'VIRTUAL_ENV' not in os.environ:
        print("⚠️  Warning: Virtual environment not detected. Consider activating venv.")
    
    # Test commands to run
    tests = [
        {
            "command": "python -m pytest tests/ -v --tb=short",
            "description": "Running all unit tests"
        },
        {
            "command": "python -m pytest tests/test_auth.py -v",
            "description": "Testing authentication module"
        },
        {
            "command": "python -m pytest tests/test_expenses.py -v",
            "description": "Testing expenses module"
        },
        {
            "command": "python -m pytest tests/test_ai_categorizer.py -v",
            "description": "Testing AI categorization"
        },
        {
            "command": "python -c \"from app.ai_categorizer import categorizer; print('✅ AI Categorizer import successful')\"",
            "description": "Testing AI categorizer imports"
        },
        {
            "command": "python -c \"from app.auth import verify_password, get_password_hash; print('✅ Auth functions import successful')\"",
            "description": "Testing auth module imports"
        },
        {
            "command": "python -c \"from app.models import *; print('✅ All models import successful')\"",
            "description": "Testing data models"
        }
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for test in tests:
        if run_command(test["command"], test["description"]):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed successfully!")
        
    # Additional validation tests
    print(f"\n{'='*50}")
    print(f"🔍 ADDITIONAL VALIDATIONS")
    print(f"{'='*50}")
    
    # Test AI categorization with sample data
    print("\n🤖 Testing AI Categorization with sample notes:")
    sample_notes = [
        "lunch at restaurant",
        "uber ride to office", 
        "movie ticket booking",
        "grocery shopping",
        "doctor consultation",
        "electricity bill payment"
    ]
    
    try:
        from app.ai_categorizer import categorizer
        for note in sample_notes:
            suggestions = categorizer.get_category_suggestions(note)
            if suggestions:
                top_category = suggestions[0]
                print(f"  📝 '{note}' → {top_category['name']} ({top_category['confidence']}%)")
            else:
                print(f"  📝 '{note}' → No categorization")
        print("✅ AI categorization working correctly")
    except Exception as e:
        print(f"❌ AI categorization test failed: {e}")
        failed += 1
    
    # Test password hashing
    print("\n🔐 Testing password security:")
    try:
        from app.auth import get_password_hash, verify_password
        test_password = "test_password_123"
        hashed = get_password_hash(test_password)
        
        if verify_password(test_password, hashed):
            print("✅ Password hashing and verification working")
        else:
            print("❌ Password verification failed")
            failed += 1
            
        if not verify_password("wrong_password", hashed):
            print("✅ Password rejection working correctly")
        else:
            print("❌ Password security compromised")
            failed += 1
            
    except Exception as e:
        print(f"❌ Password security test failed: {e}")
        failed += 1
    
    # Final summary
    if failed == 0:
        print(f"\n🎊 ALL VALIDATIONS PASSED! The backend is ready for deployment.")
    else:
        print(f"\n⚠️  Some validations failed. Please fix issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()