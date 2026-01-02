@echo off
echo Starting Red Light Violation Detection System...
cd /d "%~dp0"
python -m streamlit run streamlit_app.py --server.port 8501 --server.headless true
pause


