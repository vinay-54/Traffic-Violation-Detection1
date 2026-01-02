@echo off
echo Starting Red Light Violation Detection System...
echo.
echo Setting environment variables...
set STREAMLIT_SERVER_HEADLESS=true
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo Starting Streamlit app...
streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false

echo.
echo App should be running at: http://localhost:8501
pause
