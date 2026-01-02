# 🚦 Red Light Violation Detection System - Deployment Guide

## 📋 Overview

This guide will help you deploy your Red Light Violation Detection System in various environments, from local development to production servers.

## 🚀 Quick Start

### Option 1: Local Development (Recommended for testing)

```bash
# Method 1: Direct command
python -m streamlit run app.py

# Method 2: Using startup script (Windows)
start_app.bat

# Method 3: Using startup script (Linux/Mac)
./start_app.sh
```

**Access your app at:** http://localhost:8501

### Option 2: Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t red-light-detection .
docker run -p 8501:8501 red-light-detection
```

### Option 3: Production Server

Follow the detailed steps below for production deployment.

## 🐳 Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose installed

### Steps

1. **Build the container:**
   ```bash
   docker build -t red-light-detection .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Open http://localhost:8501 in your browser

4. **View logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Docker Configuration

The `docker-compose.yml` file includes:
- Port mapping: 8501:8501
- Volume mounts for data persistence
- Environment variables for configuration
- Automatic restart policy

## 🌐 Production Server Deployment

### Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Python 3.8+
- Nginx (optional, for reverse proxy)
- SSL certificate (recommended)

### Step 1: Server Setup

1. **Update system:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Python and dependencies:**
   ```bash
   sudo apt install python3 python3-pip python3-venv nginx -y
   ```

3. **Create application directory:**
   ```bash
   sudo mkdir -p /opt/red-light-detection
   sudo chown $USER:$USER /opt/red-light-detection
   ```

### Step 2: Application Deployment

1. **Copy application files:**
   ```bash
   cp -r * /opt/red-light-detection/
   cd /opt/red-light-detection
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories:**
   ```bash
   mkdir -p violations results charts
   ```

### Step 3: Systemd Service Setup

1. **Create service file:**
   ```bash
   sudo nano /etc/systemd/system/red-light-detection.service
   ```

2. **Add service configuration:**
   ```ini
   [Unit]
   Description=Red Light Violation Detection System
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/opt/red-light-detection
   Environment=PATH=/opt/red-light-detection/venv/bin
   ExecStart=/opt/red-light-detection/venv/bin/streamlit run app.py --server.port 8501 --server.headless true
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable red-light-detection
   sudo systemctl start red-light-detection
   ```

4. **Check service status:**
   ```bash
   sudo systemctl status red-light-detection
   ```

### Step 4: Nginx Configuration (Optional)

1. **Create Nginx configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/red-light-detection
   ```

2. **Add configuration:**
   ```nginx
   server {
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
   ```

3. **Enable site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/red-light-detection /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Step 5: SSL Certificate (Recommended)

1. **Install Certbot:**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. **Obtain SSL certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## 🔧 Configuration

### Environment Variables

You can configure the application using environment variables:

```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
```

### Streamlit Configuration

Create `~/.streamlit/config.toml`:

```toml
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
```

## 📊 Monitoring and Maintenance

### Logs

- **Systemd logs:**
  ```bash
  sudo journalctl -u red-light-detection -f
  ```

- **Application logs:**
  ```bash
  tail -f /opt/red-light-detection/logs/app.log
  ```

### Performance Monitoring

- **System resources:**
  ```bash
  htop
  df -h
  free -h
  ```

- **Application metrics:**
  - Access http://localhost:8501 for real-time statistics
  - Check `detection_results.json` for processing metrics

### Backup

1. **Backup application data:**
   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz violations/ results/ charts/
   ```

2. **Backup configuration:**
   ```bash
   cp detection_results.json backup/
   cp config.py backup/
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   sudo netstat -tulpn | grep 8501
   sudo kill -9 <PID>
   ```

2. **Permission denied:**
   ```bash
   sudo chown -R $USER:$USER /opt/red-light-detection
   chmod +x start_app.sh
   ```

3. **Dependencies missing:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Model not found:**
   - Ensure `yolov8n.pt` is in the application directory
   - Check file permissions

### Service Management

```bash
# Start service
sudo systemctl start red-light-detection

# Stop service
sudo systemctl stop red-light-detection

# Restart service
sudo systemctl restart red-light-detection

# Check status
sudo systemctl status red-light-detection

# View logs
sudo journalctl -u red-light-detection -f
```

## 🔒 Security Considerations

1. **Firewall configuration:**
   ```bash
   sudo ufw allow 8501
   sudo ufw enable
   ```

2. **SSL/TLS encryption** (recommended for production)

3. **Regular updates:**
   ```bash
   sudo apt update && sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

4. **Access control:**
   - Use reverse proxy with authentication
   - Implement IP whitelisting
   - Regular security audits

## 📈 Scaling

### Horizontal Scaling

1. **Load balancer setup**
2. **Multiple application instances**
3. **Shared storage for data**

### Vertical Scaling

1. **Increase server resources**
2. **Optimize application performance**
3. **Use more powerful hardware**

## 🎯 Next Steps

1. **Set up monitoring and alerting**
2. **Implement automated backups**
3. **Configure CI/CD pipeline**
4. **Add user authentication**
5. **Implement API endpoints**

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Consult the main README file
4. Check system requirements

---

**Your Red Light Violation Detection System is now ready for production use!** 🚦✨


