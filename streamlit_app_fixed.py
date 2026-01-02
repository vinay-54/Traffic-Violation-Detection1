import streamlit as st
import os
import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
from PIL import Image
import tempfile
from enhanced_detector_fixed import RedLightViolationDetector
import threading
import queue

def tensor_to_list(obj):
    try:
        import torch
        if isinstance(obj, torch.Tensor):
            return obj.tolist()
    except ImportError:
        pass
    return obj

def recursive_convert(item):
    if isinstance(item, dict):
        return {k: recursive_convert(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [recursive_convert(v) for v in item]
    else:
        return tensor_to_list(item)
# Page configuration
st.set_page_config(
    page_title="🚦 Red Light Violation Detection System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF4B4B;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    
    .violation-card {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .video-output-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    .video-player-container {
        background: #1a1a1a;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 2px solid #FF4B4B;
    }
    
    .stProgress > div > div > div > div {
        background-color: #FF4B4B;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2C3E50 0%, #34495E 100%);
    }
    
    .video-info-box {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    def __init__(self):
        self.detector = None
        self.processing_queue = queue.Queue()
        self.results_queue = queue.Queue()
        
    def initialize_detector(self, model_path, config):
        """Initialize the detector with given parameters"""
        try:
            self.detector = RedLightViolationDetector(model_path, config)
            return True
        except Exception as e:
            st.error(f"Error initializing detector: {e}")
            return False
    
    def process_video_thread(self, video_path, output_path):
        """Process video in a separate thread"""
        try:
            results = self.detector.process_video(video_path, output_path)
            self.results_queue.put(('success', results))
        except Exception as e:
            self.results_queue.put(('error', str(e)))

def main():
    # Initialize app
    if 'app' not in st.session_state:
        st.session_state.app = StreamlitApp()
    
    app = st.session_state.app
    
    # Header
    st.markdown('<h1 class="main-header">🚦 Red Light Violation Detection System</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Model selection
        model_path = st.selectbox(
            "Select Model",
            ["yolov8n.pt", "best.pt"],
            help="Choose the YOLO model for detection"
        )
        
        # Configuration parameters
        st.markdown("### Detection Parameters")
        
        frame_skip = st.slider("Frame Skip", 1, 10, 5, help="Skip frames for faster processing")
        confidence_threshold = st.slider("Confidence Threshold", 0.1, 1.0, 0.5, 0.1, help="Minimum confidence for detection")
        red_light_start_time = st.number_input("Red Light Start Time (seconds)", 0, 60, 12, help="When red light starts in video")
        line_y_threshold = st.slider("Detection Line Y-Position", 200, 400, 310, help="Y-coordinate of detection line")
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            flash_duration = st.slider("Flash Duration (frames)", 30, 120, 60, help="How long to flash violation indicator")
            output_width = st.number_input("Output Width", 640, 1920, 854, help="Output video width")
            output_height = st.number_input("Output Height", 480, 1080, 480, help="Output video height")
        
        # Create config
        config = {
            'frame_skip': frame_skip,
            'confidence_threshold': confidence_threshold,
            'red_light_start_time': red_light_start_time,
            'line_y_threshold': line_y_threshold,
            'flash_duration_frames': flash_duration,
            'output_resolution': (output_width, output_height),
            'violation_save_path': 'violations'
        }
        
        # Initialize detector
        if st.button("🔄 Initialize Detector", type="primary"):
            with st.spinner("Initializing detector..."):
                if app.initialize_detector(model_path, config):
                    st.success("✅ Detector initialized successfully!")
                else:
                    st.error("❌ Failed to initialize detector")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📹 Video Processing")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Traffic Video",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Upload a traffic video for violation detection"
        )
        
        if uploaded_file is not None:
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                video_path = tmp_file.name
            
            # Save original video for comparison
            st.session_state.original_video_path = video_path
            st.session_state.uploaded_file = uploaded_file
            
            # Display video info
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            st.info(f"📊 Video Info: {frame_count} frames, {fps:.1f} FPS, {duration:.1f} seconds")
            
            # Processing controls
            col_process1, col_process2 = st.columns(2)
            
            with col_process1:
                if st.button("🎬 Start Processing", type="primary", disabled=app.detector is None):
                    if app.detector:
                        # Start processing in thread
                        output_path = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        
                        # Clear previous results
                        st.session_state.results = None
                        st.session_state.processing = True
                        st.session_state.output_path = output_path
                        
                        # Start processing thread
                        thread = threading.Thread(
                            target=app.process_video_thread,
                            args=(video_path, output_path)
                        )
                        thread.start()
                        
                        st.success(f"🎬 Processing started! Output will be saved to: {output_path}")
                        st.rerun()
            
            with col_process2:
                if st.button("⏹ Stop Processing", disabled=not st.session_state.get('processing', False)):
                    st.session_state.processing = False
                    st.rerun()
            
            # Processing progress with live preview
            if st.session_state.get('processing', False):
                st.markdown("### 🔄 Processing Video...")
                
                # Progress section
                progress_col1, progress_col2 = st.columns([3, 1])
                
                with progress_col1:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                with progress_col2:
                    st.markdown("**Live Preview:**")
                    preview_placeholder = st.empty()
                
                # Processing status
                status_container = st.container()
                
                # Simulate progress with live updates
                for i in range(100):
                    time.sleep(0.1)
                    progress_bar.progress(i + 1)
                    status_text.text(f"Processing... {i+1}%")
                    
                    # Update live preview (simulate frame processing)
                    if i % 10 == 0:
                        with status_container:
                            st.info(f"📹 Processing frame {i*10} of {frame_count}...")
                    
                    # Check for results
                    try:
                        result_type, result_data = app.results_queue.get_nowait()
                        if result_type == 'success':
                            st.session_state.results = result_data
                            st.session_state.processing = False
                            st.success("✅ **Video Processing Completed Successfully!**")
                            st.balloons()
                            
                            # Auto-refresh to show video output
                            st.rerun()
                            break
                        elif result_type == 'error':
                            st.error(f"❌ **Processing failed:** {result_data}")
                            st.session_state.processing = False
                            break
                    except queue.Empty:
                        pass
                
                if st.session_state.get('processing', False):
                    st.session_state.processing = False
                    st.warning("⚠️ Processing was interrupted or timed out.")
    
    with col2:
        st.markdown("## 📊 Real-time Statistics")
        
        if app.detector:
            stats = app.detector.get_statistics()
            
            # Display metrics
            col_metric1, col_metric2 = st.columns(2)
            
            with col_metric1:
                st.metric("🚗 Active Vehicles", stats['active_vehicles'])
                st.metric("⏱️ Processing Time", f"{stats['processing_time']:.1f}s")
            
            with col_metric2:
                st.metric("🚨 Violations", stats['total_violations'])
                st.metric("📹 Frames Processed", stats['frame_count'])
        
        # Traffic light status
        st.markdown("### 🚦 Traffic Light Status")
        light_status = st.selectbox("Current Status", ["🟢 Green", "🔴 Red"], index=0)
        
        # Display status with color
        if "Red" in light_status:
            st.markdown('<div class="violation-card">🔴 RED LIGHT ACTIVE</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-card">🟢 GREEN LIGHT ACTIVE</div>', unsafe_allow_html=True)
    
    # Results section
    if st.session_state.get('results'):
        st.markdown("## 📈 Processing Results")
        
        results = st.session_state.results
        
        # Results metrics
        col_result1, col_result2, col_result3, col_result4 = st.columns(4)
        
        with col_result1:
            st.metric("Total Frames", results['total_frames'])
        
        with col_result2:
            st.metric("Total Violations", results['total_violations'])
        
        with col_result3:
            st.metric("Processing Time", f"{results['processing_time']:.1f}s")
        
        with col_result4:
            fps = results['total_frames'] / results['processing_time'] if results['processing_time'] > 0 else 0
            st.metric("Processing FPS", f"{fps:.1f}")
        
        # VIDEO OUTPUT SECTION - ENHANCED
        st.markdown('<div class="video-output-card">', unsafe_allow_html=True)
        st.markdown("## 🎬 Processed Video Output")
        st.markdown("### 📹 Annotated Video with Violation Detection")
        st.markdown("**Watch the processed video below to see detected violations, traffic light status, and real-time statistics:**")
        st.markdown('</div>', unsafe_allow_html=True)
        
        output_path = st.session_state.get('output_path', '')
        
        # Check if processing is still ongoing
        if st.session_state.get('processing', False):
            st.info("🔄 **Video is still being processed...** Please wait for completion.")
            st.progress(0.5)  # Show indeterminate progress
            return
        
        if output_path and os.path.exists(output_path):
            # Check file size
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                st.error("❌ **Output video file is empty!** Processing may have failed.")
                return
            
            # Video comparison section
            st.markdown("### 📺 Video Comparison")
            
            # Create two columns for side-by-side comparison
            col_original, col_processed = st.columns(2)
            
            with col_original:
                st.markdown("**🎬 Original Video**")
                if st.session_state.get('uploaded_file') is not None:
                    st.video(st.session_state.uploaded_file, start_time=0)
                else:
                    st.info("Original video not available")
            
            with col_processed:
                st.markdown("**🚦 Processed Video with Detection**")
                # Video player container with styling
                st.markdown('<div class="video-player-container">', unsafe_allow_html=True)
                
                # Video player with controls
                with open(output_path, 'rb') as video_file:
                    video_bytes = video_file.read()
                    st.video(video_bytes, start_time=0)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Video information box
            st.markdown('<div class="video-info-box">', unsafe_allow_html=True)
            st.markdown(f"📊 **Video Details:** Processed video with **{results['total_violations']} violations** detected")
            st.markdown(f"⏱️ **Processing Time:** {results['processing_time']:.1f} seconds")
            st.markdown(f"📹 **Total Frames:** {results['total_frames']} frames")
            st.markdown(f"📁 **File Size:** {file_size:,} bytes")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Video controls
            col_video1, col_video2, col_video3, col_video4 = st.columns(4)
            
            with col_video1:
                if st.button("🔄 Replay Video", help="Replay the processed video", type="primary"):
                    st.rerun()
            
            with col_video2:
                st.download_button(
                    label="📥 Download Video",
                    data=video_bytes,
                    file_name=f"annotated_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                    mime="video/mp4",
                    help="Download the processed video with detection results"
                )
            
            with col_video3:
                if st.button("📊 Show Statistics", help="Show detailed video statistics"):
                    st.session_state.show_detailed_stats = True
                    st.rerun()
            
            with col_video4:
                if st.button("🎯 View Violations", help="View individual violation screenshots"):
                    st.session_state.show_violations = True
                    st.rerun()
        else:
            st.error("⚠️ **Processed video not found!** Please ensure video processing completed successfully.")
            st.info("💡 **Tip:** Click 'Start Processing' to generate the annotated video output.")
            
            # Show debug information
            if st.button("🔍 Debug Video Output"):
                st.markdown("### 🔍 Debug Information")
                st.write(f"**Output Path:** {output_path}")
                st.write(f"**File Exists:** {os.path.exists(output_path) if output_path else 'No path set'}")
                
                if output_path and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    st.write(f"**File Size:** {file_size} bytes")
                    
                    if file_size > 0:
                        try:
                            cap = cv2.VideoCapture(output_path)
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            cap.release()
                            st.write(f"**Video Info:** {frame_count} frames, {fps:.1f} FPS")
                        except Exception as e:
                            st.error(f"Error reading video: {e}")
                    else:
                        st.error("Video file is empty!")
                else:
                    st.error("Video file does not exist!")
        
        # Violations timeline chart
        if results.get('stats'):
            st.markdown("### 📊 Violations Timeline")
            
            df_stats = pd.DataFrame(results['stats'])
            df_stats['timestamp'] = pd.date_range(
                start=datetime.now() - timedelta(seconds=len(df_stats)),
                periods=len(df_stats),
                freq='S'
            )
            
            fig = px.line(df_stats, x='timestamp', y='violations', 
                         title="Violations Over Time",
                         labels={'violations': 'Number of Violations', 'timestamp': 'Time'})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Download results
        st.markdown("### 💾 Download Results")
        
        col_download1, col_download2 = st.columns(2)
        
        with col_download1:
            if os.path.exists(st.session_state.get('output_path', '')):
                with open(st.session_state.output_path, 'rb') as f:
                    st.download_button(
                        label="📹 Download Annotated Video",
                        data=f.read(),
                        file_name="annotated_video.mp4",
                        mime="video/mp4"
                    )
        
        with col_download2:
            # Create results JSON
            serializable_results = recursive_convert(results)
            results_json = json.dumps(serializable_results, indent=2)
            st.download_button(
                label="📄 Download Results JSON",
                data=results_json,
                file_name="detection_results.json",
                mime="application/json"
            )
    
    # Violations gallery - Enhanced
    if st.session_state.get('show_violations', False) or (app.detector and app.detector.violations):
        st.markdown("## 🚨 Violations Gallery")
        st.markdown("### 📸 Individual Violation Screenshots")
        
        violations_dir = app.detector.config['violation_save_path']
        if os.path.exists(violations_dir):
            violation_images = [f for f in os.listdir(violations_dir) if f.endswith(('.jpg', '.png'))]
            
            if violation_images:
                st.success(f"📊 **Found {len(violation_images)} violation screenshots**")
                
                # Display violations in a grid with better styling
                cols = st.columns(3)
                for i, img_file in enumerate(violation_images[:9]):  # Show first 9 violations
                    img_path = os.path.join(violations_dir, img_file)
                    try:
                        image = Image.open(img_path)
                        with cols[i % 3]:
                            st.markdown(f"**Violation {i+1}:** {img_file}")
                            st.image(image, use_column_width=True, caption=f"Violation detected at {img_file}")
                    except Exception as e:
                        cols[i % 3].error(f"Error loading {img_file}: {e}")
                
                # Show more violations if available
                if len(violation_images) > 9:
                    st.info(f"💡 **Showing first 9 violations.** Total violations: {len(violation_images)}")
                    
                    if st.button("📋 Show All Violations"):
                        st.session_state.show_all_violations = True
                        st.rerun()
            else:
                st.info("📭 No violation screenshots found. Violations may not have been detected or saved.")
        else:
            st.warning("⚠️ Violations directory not found. Please ensure video processing completed successfully.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>🚦 Enhanced Red Light Violation Detection System</p>
        <p>Built with Streamlit, YOLO, and OpenCV</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
