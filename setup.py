#!/usr/bin/env python3
"""
Expense Tracker Setup Script
This script helps set up the backend environment and validates the installation.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def setup_virtual_environment():
    """Set up virtual environment"""
    backend_dir = Path("backend")
    venv_dir = backend_dir / "venv"
    
    if not venv_dir.exists():
        print("🔧 Creating virtual environment...")
        if not run_command(f"python3 -m venv {venv_dir}", "Creating venv"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    backend_dir = Path("backend")
    os.chdir(backend_dir)
    
    # Check if we're in a virtual environment
    if 'VIRTUAL_ENV' not in os.environ:
        print("⚠️  Virtual environment not activated")
        print("Please run: source backend/venv/bin/activate (or backend\\venv\\Scripts\\activate on Windows)")
        return False
    
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def setup_environment_file():
    """Set up environment file"""
    backend_dir = Path("backend")
    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creating .env file from template...")
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your actual credentials:")
            print("   - SUPABASE_URL")
            print("   - SUPABASE_KEY") 
            print("   - SUPABASE_SERVICE_KEY")
            print("   - JWT_SECRET")
            print("   - ANTHROPIC_API_KEY")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def run_tests():
    """Run basic tests"""
    print("🧪 Running core functionality tests...")
    
    # Test core functionality without dependencies
    if run_command("python3 test_core_functionality.py", "Core functionality tests"):
        print("✅ Core tests passed")
    else:
        print("❌ Core tests failed")
        return False
    
    # Test Claude integration structure
    if run_command("python3 test_claude_categorization.py", "Claude integration tests"):
        print("✅ Claude integration tests passed")
    else:
        print("❌ Claude integration tests failed")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Expense Tracker Backend Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Please run this script from the ExpenseTracker root directory")
        return False
    
    steps = [
        ("Check Python Version", check_python_version),
        ("Setup Virtual Environment", setup_virtual_environment),
        ("Setup Environment File", setup_environment_file),
        ("Run Basic Tests", run_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Activate virtual environment: source backend/venv/bin/activate")
    print("2. Install dependencies: cd backend && pip install -r requirements.txt")
    print("3. Edit backend/.env with your API credentials")
    print("4. Set up Supabase database with the provided schema")
    print("5. Run the backend: cd backend && python main.py")
    print("6. Test API at: http://localhost:8000")
    print("\n📖 Get Claude API key: https://console.anthropic.com")
    print("📖 Set up Supabase: https://supabase.com")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)