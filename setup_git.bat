@echo off
echo 🚦 Setting up Git for Streamlit Cloud Deployment
echo ================================================
echo.

echo 📁 Initializing Git repository...
git init

echo.
echo 📝 Adding all files...
git add .

echo.
echo 💾 Making initial commit...
git commit -m "Initial commit: Red Light Violation Detection System"

echo.
echo ================================================
echo ✅ Git repository initialized successfully!
echo.
echo 📋 Next steps:
echo 1. Create a GitHub repository at github.com
echo 2. Make it PUBLIC (required for free Streamlit Cloud)
echo 3. Run these commands:
echo.
echo git remote add origin https://github.com/YOUR_USERNAME/Red-Light-Violation-Detection-main.git
echo git branch -M main
echo git push -u origin main
echo.
echo 4. Then deploy at: https://share.streamlit.io
echo.
echo 🌍 Your app will be accessible worldwide!
pause
