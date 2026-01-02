#!/usr/bin/env python3
"""
Launcher script for the Enhanced Red Light Violation Detection System
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'ultralytics', 
        'opencv-python',
        'numpy',
        'pandas',
        'plotly',
        'pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def check_model_files():
    """Check if YOLO model files exist"""
    model_files = ['yolov8n.pt', 'best.pt']
    available_models = []
    
    for model in model_files:
        if os.path.exists(model):
            available_models.append(model)
            print(f"✅ Found model: {model}")
        else:
            print(f"⚠️  Model not found: {model}")
    
    if not available_models:
        print("\n❌ No YOLO model files found!")
        print("📥 Download YOLOv8n model:")
        print("   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['violations', 'results', 'charts']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def launch_streamlit():
    """Launch the Streamlit application"""
    print("\n🚀 Launching Enhanced Red Light Violation Detection System...")
    print("🌐 Opening web browser...")
    
    # Start Streamlit in background
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:8501')
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.port', '8501',
            '--server.address', 'localhost',
            '--browser.gatherUsageStats', 'false'
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")

def main():
    """Main launcher function"""
    print("🚦 Enhanced Red Light Violation Detection System")
    print("=" * 50)
    
    # Check dependencies
    print("\n🔍 Checking dependencies...")
    if not check_dependencies():
        return
    
    # Check model files
    print("\n🔍 Checking model files...")
    if not check_model_files():
        return
    
    # Create directories
    print("\n📁 Setting up directories...")
    create_directories()
    
    # Launch application
    print("\n🎯 System ready!")
    launch_streamlit()

if __name__ == "__main__":
    main()
