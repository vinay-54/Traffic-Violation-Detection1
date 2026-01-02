#!/usr/bin/env python3
"""
Deployment script for Red Light Violation Detection System
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_system_requirements():
    """Check if system meets deployment requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check available memory
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        if memory_gb < 4:
            print(f"⚠️  Low memory: {memory_gb:.1f} GB (4+ GB recommended)")
        else:
            print(f"✅ Memory: {memory_gb:.1f} GB")
    except ImportError:
        print("⚠️  psutil not available, cannot check memory")
    
    # Check disk space
    try:
        disk = psutil.disk_usage('.')
        disk_gb = disk.free / (1024**3)
        if disk_gb < 1:
            print(f"❌ Low disk space: {disk_gb:.1f} GB free")
            return False
        print(f"✅ Disk space: {disk_gb:.1f} GB free")
    except:
        print("⚠️  Cannot check disk space")
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_production_config():
    """Create production configuration"""
    print("\n⚙️  Creating production configuration...")
    
    config_content = """
# Production configuration for Streamlit
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
"""
    
    config_dir = Path.home() / ".streamlit"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.toml"
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Production config created: {config_file}")
    return True

def create_startup_script():
    """Create startup script for the application"""
    print("\n🚀 Creating startup script...")
    
    if platform.system() == "Windows":
        script_content = """@echo off
echo Starting Red Light Violation Detection System...
cd /d "%~dp0"
python -m streamlit run app.py --server.port 8501 --server.headless true
pause
"""
        script_name = "start_app.bat"
    else:
        script_content = """#!/bin/bash
echo "Starting Red Light Violation Detection System..."
cd "$(dirname "$0")"
python -m streamlit run app.py --server.port 8501 --server.headless true
"""
        script_name = "start_app.sh"
        # Make executable
        os.chmod(script_name, 0o755)
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    print(f"✅ Startup script created: {script_name}")
    return True

def create_dockerfile():
    """Create Dockerfile for containerized deployment"""
    print("\n🐳 Creating Dockerfile...")
    
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    libgl1-mesa-glx \\
    libglib2.0-0 \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p violations results charts

# Expose port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
"""
    
    with open("Dockerfile", 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile created")
    return True

def create_docker_compose():
    """Create docker-compose.yml for easy deployment"""
    print("\n🐳 Creating docker-compose.yml...")
    
    compose_content = """version: '3.8'

services:
  red-light-detection:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./violations:/app/violations
      - ./results:/app/results
      - ./charts:/app/charts
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_HEADLESS=true
    restart: unless-stopped
"""
    
    with open("docker-compose.yml", 'w') as f:
        f.write(compose_content)
    
    print("✅ docker-compose.yml created")
    return True

def create_nginx_config():
    """Create nginx configuration for production"""
    print("\n🌐 Creating nginx configuration...")
    
    nginx_config = """server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
"""
    
    with open("nginx.conf", 'w') as f:
        f.write(nginx_config)
    
    print("✅ nginx.conf created")
    return True

def create_systemd_service():
    """Create systemd service for Linux deployment"""
    print("\n🔧 Creating systemd service...")
    
    service_content = """[Unit]
Description=Red Light Violation Detection System
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/venv/bin
ExecStart=/path/to/your/app/venv/bin/streamlit run app.py --server.port 8501 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open("red-light-detection.service", 'w') as f:
        f.write(service_content)
    
    print("✅ systemd service file created")
    return True

def main():
    """Main deployment function"""
    print("🚦 Red Light Violation Detection System - Deployment Setup")
    print("=" * 60)
    
    # Check system requirements
    if not check_system_requirements():
        print("\n❌ System requirements not met!")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies!")
        return
    
    # Create production configuration
    create_production_config()
    
    # Create startup script
    create_startup_script()
    
    # Create Docker files
    create_dockerfile()
    create_docker_compose()
    
    # Create nginx config
    create_nginx_config()
    
    # Create systemd service
    create_systemd_service()
    
    print("\n" + "=" * 60)
    print("🎉 Deployment setup completed!")
    print("\n📋 Deployment Options:")
    print("\n1. Local Development:")
    print("   python -m streamlit run app.py")
    print("   or")
    print("   ./start_app.sh (Linux/Mac)")
    print("   start_app.bat (Windows)")
    
    print("\n2. Docker Deployment:")
    print("   docker-compose up -d")
    print("   or")
    print("   docker build -t red-light-detection .")
    print("   docker run -p 8501:8501 red-light-detection")
    
    print("\n3. Production Server:")
    print("   - Copy files to server")
    print("   - Install nginx")
    print("   - Configure nginx.conf")
    print("   - Use systemd service")
    
    print("\n🌐 Access your app at: http://localhost:8501")
    print("\n📁 Generated files:")
    print("   - start_app.sh/bat: Startup script")
    print("   - Dockerfile: Container configuration")
    print("   - docker-compose.yml: Multi-container setup")
    print("   - nginx.conf: Web server configuration")
    print("   - red-light-detection.service: System service")
    
    print("\n🚀 Your app is ready for deployment!")

if __name__ == "__main__":
    main()


