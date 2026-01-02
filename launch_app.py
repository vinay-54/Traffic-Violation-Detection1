import os
import subprocess
import sys

def main():
    print("🚦 Starting Red Light Violation Detection System...")
    print()
    
    # Set environment variables to disable usage stats
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    print("✅ Environment variables set")
    print("🌐 Starting Streamlit app...")
    print("📍 App will be available at: http://localhost:8501")
    print()
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.headless', 'true',
            '--server.port', '8501',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n🛑 App stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")

if __name__ == "__main__":
    main()
