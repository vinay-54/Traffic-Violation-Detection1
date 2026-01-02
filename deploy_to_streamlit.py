#!/usr/bin/env python3
"""
🚀 Streamlit Cloud Deployment Helper
This script helps prepare your project for Streamlit Cloud deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def check_files():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'enhanced_detector.py', 
        'requirements.txt',
        'packages.txt',
        'runtime.txt',
        '.streamlit/config.toml',
        'yolov8n.pt'
    ]
    
    print("🔍 Checking required files...")
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return missing_files

def check_git_status():
    """Check git repository status"""
    try:
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📁 Git repository status:")
            print(result.stdout)
            return True
        else:
            print("\n❌ Not a git repository or git not available")
            return False
    except FileNotFoundError:
        print("\n❌ Git not installed")
        return False

def create_git_commands():
    """Create git commands for deployment"""
    print("\n🚀 Git commands for deployment:")
    print("git add .")
    print("git commit -m \"Prepare for Streamlit Cloud deployment\"")
    print("git push origin main")
    print("\n🌐 Then go to: https://share.streamlit.io")

def main():
    print("🚦 Red Light Violation Detection System")
    print("🌐 Streamlit Cloud Deployment Helper")
    print("=" * 50)
    
    # Check files
    missing_files = check_files()
    
    # Check git status
    is_git_repo = check_git_status()
    
    print("\n" + "=" * 50)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease create these files before deploying.")
        return
    
    if not is_git_repo:
        print("\n❌ Git repository not found.")
        print("Please initialize git and connect to GitHub:")
        print("git init")
        print("git remote add origin <your-github-repo-url>")
        return
    
    print("\n🎉 All checks passed! Your project is ready for deployment!")
    create_git_commands()
    
    print("\n📋 Next steps:")
    print("1. Push your code to GitHub")
    print("2. Go to https://share.streamlit.io")
    print("3. Sign in with GitHub")
    print("4. Click 'New app'")
    print("5. Select your repository and branch")
    print("6. Set main file path to: app.py")
    print("7. Click 'Deploy!'")
    
    print("\n🌍 Your app will be available at:")
    print("https://your-app-name-username.streamlit.app")

if __name__ == "__main__":
    main()
