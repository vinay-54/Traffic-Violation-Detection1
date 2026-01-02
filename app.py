import streamlit as st
import os
import cv2
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import tempfile
import time
from enhanced_detector import RedLightViolationDetector
from PIL import Image
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
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #FF4B4B;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
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
    
    .video-container {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

def process_frame_with_detections(frame, detector, frame_number):
    """Process a single frame and return annotated frame with detections"""
    try:
        # Run detection on the frame
        results = detector.model(frame, verbose=False)
        
        annotated_frame = frame.copy()
        violations_in_frame = 0
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Get confidence and class
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    # Check if it's a vehicle class and meets confidence threshold
                    # Add fallback for classes_to_detect if not in config
                    classes_to_detect = detector.config.get('classes_to_detect', [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12])
                    confidence_threshold = detector.config.get('confidence_threshold', 0.5)
                    
                    if cls in classes_to_detect and conf >= confidence_threshold:
                        # Check if vehicle crosses the line (potential violation)
                        center_y = (y1 + y2) // 2
                        line_y_threshold = detector.config.get('line_y_threshold', 310)
                        is_violation = center_y > line_y_threshold
                        
                        # Choose color based on violation status
                        if is_violation:
                            color = (0, 0, 255)  # Red for violations
                            violations_in_frame += 1
                        else:
                            color = (0, 255, 0)  # Green for normal
                        
                        # Draw bounding box
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Draw label
                        label = f"{detector._get_class_name(cls)} {conf:.2f}"
                        cv2.putText(annotated_frame, label, (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw detection line
        cv2.line(annotated_frame, (0, detector.config['line_y_threshold']), 
                (frame.shape[1], detector.config['line_y_threshold']), (255, 0, 0), 2)
        
        # Draw violation count
        cv2.putText(annotated_frame, f"Violations: {violations_in_frame}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Draw frame number
        cv2.putText(annotated_frame, f"Frame: {frame_number}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return annotated_frame, violations_in_frame
        
    except Exception as e:
        st.error(f"Error processing frame: {e}")
        return frame, 0

def _save_processed_video(video_path, detector, frame_count, fps):
    """Save the processed video with annotations"""
    try:
        # Create output directory
        output_dir = "processed_videos"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"processed_video_{timestamp}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # Setup video writer with better codec settings
        # Use H.264 codec for better compatibility
        if os.name == 'nt':  # Windows
            fourcc = cv2.VideoWriter_fourcc(*'H264')
        else:  # Linux/Mac
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
        
        frame_skip = detector.config.get('frame_skip', 5)
        output_fps = max(1, fps / frame_skip)  # Ensure minimum 1 FPS
        output_resolution = detector.config.get('output_resolution', (854, 480))
        
        # Create video writer
        out = cv2.VideoWriter(output_path, fourcc, output_fps, output_resolution)
        
        # Verify video writer is initialized properly
        if not out.isOpened():
            st.error("❌ Failed to initialize video writer. Trying alternative codec...")
            # Fallback to MP4V codec
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, output_fps, output_resolution)
            
            if not out.isOpened():
                st.error("❌ Video writer initialization failed completely")
                return None
        
        # Process video again to save annotated version
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_number = 0
        processed_frames = 0
        
        with st.spinner("🎬 Saving processed video..."):
            while cap.isOpened() and frame_number < frame_count:
                ret, frame = cap.read()
                if not ret:
                    break
                # ... your processing ...
                frame_number += 1
                
                # Process every nth frame based on frame_skip
                if frame_number % frame_skip == 0:
                    try:
                        # Process frame with detections
                        annotated_frame, _ = process_frame_with_detections(frame, detector, frame_number)
                        
                        # Ensure frame is in BGR format
                        if len(annotated_frame.shape) == 3 and annotated_frame.shape[2] == 3:
                            # Resize frame to output resolution
                            annotated_frame_resized = cv2.resize(annotated_frame, output_resolution)
                            
                            # Write frame to output video
                            out.write(annotated_frame_resized)
                            processed_frames += 1
                        else:
                            st.warning(f"⚠️ Frame {frame_number} has invalid format, skipping...")
                    
                    except Exception as e:
                        st.error(f"❌ Error processing frame {frame_number}: {e}")
                        continue
                
                frame_number += 1
                
                # Update progress
                if frame_number % 10 == 0:
                    progress = min(100, (frame_number / frame_count) * 100)
                    st.progress(int(progress))
        
        cap.release()
        out.release()
        
        # Verify the video was created successfully
        if processed_frames > 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            st.success(f"✅ Processed video saved: {output_filename} ({processed_frames} frames)")
            return output_path
        else:
            st.error("❌ Failed to create valid video file")
            return None
        
    except Exception as e:
        st.error(f"❌ Error saving processed video: {e}")
        return None

def _create_compatible_video(video_path, detector, frame_count, fps):
    """Create a video using a more compatible method"""
    try:
        # Create output directory
        output_dir = "processed_videos"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"processed_video_{timestamp}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # Try different codecs in order of preference
        codecs = [
            ('mp4v', 'MP4V'),
            ('avc1', 'AVC1'), 
            ('H264', 'H264'),
            ('XVID', 'XVID')
        ]
        
        frame_skip = detector.config.get('frame_skip', 5)
        output_fps = max(1, fps / frame_skip)
        output_resolution = detector.config.get('output_resolution', (854, 480))
        
        out = None
        successful_codec = None
        
        for codec_name, codec_display in codecs:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec_name)
                out = cv2.VideoWriter(output_path, fourcc, output_fps, output_resolution)
                
                if out.isOpened():
                    successful_codec = codec_display
                    st.info(f"✅ Using codec: {codec_display}")
                    break
                else:
                    out.release()
            except Exception as e:
                st.warning(f"⚠️ Codec {codec_display} failed: {e}")
                continue
        
        if out is None or not out.isOpened():
            st.error("❌ All video codecs failed. Cannot create video.")
            return None
        
        # Process video frames
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_number = 0
        processed_frames = 0
        
        with st.spinner(f"🎬 Creating video with {successful_codec} codec..."):
            while cap.isOpened() and frame_number < frame_count:
                ret, frame = cap.read()
                if not ret:
                    break
                # ... your processing ...
                frame_number += 1
                
                if frame_number % frame_skip == 0:
                    try:
                        # Process frame
                        annotated_frame, _ = process_frame_with_detections(frame, detector, frame_number)
                        
                        # Ensure proper format
                        if len(annotated_frame.shape) == 3:
                            # Resize and write frame
                            annotated_frame_resized = cv2.resize(annotated_frame, output_resolution)
                            out.write(annotated_frame_resized)
                            processed_frames += 1
                    
                    except Exception as e:
                        st.warning(f"⚠️ Error processing frame {frame_number}: {e}")
                        continue
                
                frame_number += 1
                
                # Update progress
                if frame_number % 20 == 0:
                    progress = min(100, (frame_number / frame_count) * 100)
                    st.progress(int(progress))
        
        cap.release()
        out.release()
        
        # Final validation
        if processed_frames > 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            st.success(f"✅ Video created successfully: {output_filename} ({processed_frames} frames)")
            return output_path
        else:
            st.error("❌ Video creation failed - file is invalid or empty")
            return None
            
    except Exception as e:
        st.error(f"❌ Error in video creation: {e}")
        return None

def _validate_video(video_path):
    """Validate that the video file is playable"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, "Video file cannot be opened"
        
        # Check if we can read at least one frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return False, "Cannot read frames from video"
        
        # Check file size
        file_size = os.path.getsize(video_path)
        if file_size < 1024:  # Less than 1KB
            return False, "Video file is too small"
        
        return True, "Video is valid"
        
    except Exception as e:
        return False, f"Video validation error: {e}"

def _create_test_video():
    """Create a simple test video to verify video creation works"""
    try:
        output_dir = "processed_videos"
        os.makedirs(output_dir, exist_ok=True)
        
        test_filename = "test_video.mp4"
        test_path = os.path.join(output_dir, test_filename)
        
        # Create a simple test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(test_path, fourcc, 10.0, (640, 480))
        
        if not out.isOpened():
            return False, "Failed to create test video writer"
        
        # Create 50 frames of a simple animation
        for i in range(50):
            # Create a frame with a moving rectangle
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            x = int((i * 10) % 600)
            cv2.rectangle(frame, (x, 200), (x + 40, 280), (0, 255, 0), -1)
            cv2.putText(frame, f"Frame {i}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            out.write(frame)
        
        out.release()
        
        # Validate the test video
        is_valid, message = _validate_video(test_path)
        return is_valid, message
        
    except Exception as e:
        return False, f"Test video creation failed: {e}"

def main():
    # Initialize default configuration if not exists
    if 'config' not in st.session_state:
        st.session_state.config = {
            'frame_skip': 5,
            'confidence_threshold': 0.5,
            'red_light_start_time': 12,
            'line_y_threshold': 310,
            'flash_duration_frames': 60,
            'output_resolution': (854, 480),
            'violation_save_path': 'violations',
            'classes_to_detect': [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]
        }
    
    # Header
    st.markdown('<h1 class="main-header">🚦 Red Light Violation Detection System</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Model selection
        model_path = st.selectbox(
            "Select Model",
            ["yolov8n.pt", "best.pt"],
            help="Choose the YOLO model for detection"
        )
        
        # Detection parameters
        st.markdown("### Detection Parameters")
        frame_skip = st.slider("Frame Skip", 1, 10, 5)
        confidence_threshold = st.slider("Confidence Threshold", 0.1, 1.0, 0.5, 0.1)
        red_light_start_time = st.number_input("Red Light Start Time (seconds)", 0, 60, 12)
        line_y_threshold = st.slider("Detection Line Y-Position", 200, 400, 310)
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            flash_duration = st.slider("Flash Duration (frames)", 30, 120, 60)
            output_width = st.number_input("Output Width", 640, 1920, 854)
            output_height = st.number_input("Output Height", 480, 1080, 480)
        
        # Create configuration with ALL required parameters
        st.session_state.config = {
            'frame_skip': frame_skip,
            'confidence_threshold': confidence_threshold,
            'red_light_start_time': red_light_start_time,
            'line_y_threshold': line_y_threshold,
            'flash_duration_frames': flash_duration,
            'output_resolution': (output_width, output_height),
            'violation_save_path': 'violations',
            'classes_to_detect': [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]  # Vehicle classes
        }
    
    # Main content
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
            
            # Display video info
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            st.info(f"📊 Video Info: {frame_count} frames, {fps:.1f} FPS, {duration:.1f} seconds")
            
            # Show processing capability for longer videos
            if duration > 30:
                st.success(f"🎬 This video will be processed completely! Duration: {duration:.1f} seconds")
            elif duration > 10:
                st.info(f"📹 Video will be processed completely. Duration: {duration:.1f} seconds")
            else:
                st.info(f"📹 Short video - will be processed completely. Duration: {duration:.1f} seconds")
            
            # Initialize detector
            try:
                # Debug: Show configuration being used
                st.info(f"🔧 Using configuration: {json.dumps(st.session_state.config, indent=2)}")
                
                detector = RedLightViolationDetector(model_path, st.session_state.config)
                st.success("✅ Detector initialized successfully!")
                
                # Process button
                if st.button("🎬 Start Video Processing", type="primary"):
                    st.markdown("### 🎥 Video Processing")
                    
                    # Create progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Create temporary output file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_output:
                        output_path = tmp_output.name
                    
                    # Setup video writer
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    frame_skip = st.session_state.config.get('frame_skip', 5)
                    output_fps = max(1, fps / frame_skip)
                    output_resolution = st.session_state.config.get('output_resolution', (854, 480))
                    
                    out = cv2.VideoWriter(output_path, fourcc, output_fps, output_resolution)
                    
                    if not out.isOpened():
                        st.error("❌ Failed to initialize video writer")
                        cap.release()
                        return
                    
                    # Process video
                    cap = cv2.VideoCapture(video_path)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    frame_number = 0
                    total_violations = 0
                    processed_frames = 0
                    
                    with st.spinner("🎬 Processing video frames..."):
                        frame_number = 0
                        while cap.isOpened() and frame_number < frame_count:
                            ret, frame = cap.read()
                            if not ret:
                                break
                            # ... your processing ...
                            frame_number += 1
                            
                            # Process every nth frame based on frame_skip
                            if frame_number % frame_skip == 0:
                                # Process frame with detections
                                annotated_frame, violations = process_frame_with_detections(
                                    frame, detector, frame_number
                                )
                                total_violations += violations
                                
                                # Ensure proper format and write to video
                                if len(annotated_frame.shape) == 3:
                                    # Resize frame to output resolution
                                    annotated_frame_resized = cv2.resize(annotated_frame, output_resolution)
                                    out.write(annotated_frame_resized)
                                    processed_frames += 1
                                
                                # Update progress
                                progress = min(100, (frame_number / frame_count) * 100)
                                progress_bar.progress(int(progress))
                                
                                # Update status
                                if frame_number % 30 == 0:
                                    status_text.text(f"Processing frame {frame_number}/{frame_count} - Violations: {total_violations}")
                            
                            frame_number += 1
                    
                    # Close video writer and capture
                    out.release()
                    cap.release()
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Video processing completed!")
                    
                    # Store results
                    st.session_state.results = {
                        'total_frames': frame_number,
                        'total_violations': total_violations,
                        'processing_time': time.time() - detector.start_time,
                        'video_duration': duration,
                        'processing_fps': frame_number / (time.time() - detector.start_time) if (time.time() - detector.start_time) > 0 else 0,
                        'stats': {'frame': frame_number, 'violations': total_violations}
                    }
                    
                    # Display the processed video
                    st.markdown("### 🎬 Processed Video Output")
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                        # Display the processed video
                        st.video(output_path)
                        
                        # Download button for the processed video
                        with open(output_path, "rb") as video_file:
                            st.download_button(
                                label="📥 Download Processed Video",
                                data=video_file.read(),
                                file_name=f"processed_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                mime="video/mp4"
                            )
                        
                        st.success(f"🎉 Video processing completed! Found {total_violations} violations in {processed_frames} processed frames.")
                        
                        # Show video info
                        cap = cv2.VideoCapture(output_path)
                        video_fps = cap.get(cv2.CAP_PROP_FPS)
                        video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        video_duration = video_frames / video_fps if video_fps > 0 else 0
                        cap.release()
                        
                        st.info(f"📊 Output Video Info: {video_frames} frames, {video_fps:.1f} FPS, {video_duration:.1f} seconds")
                        
                    else:
                        st.error("❌ Failed to create valid video file. Please try again.")
                    
                    st.session_state.output_video_path = output_path
                    st.session_state.detector = detector
                    
                    st.balloons()  # Celebrate completion!
                    
            except Exception as e:
                st.error(f"❌ Error initializing detector: {e}")
                st.error("Please check if the model file exists and try again.")
    
    with col2:
        st.markdown("## 📊 Live Statistics")
        
        # Display current statistics if detector exists
        if 'detector' in st.session_state:
            detector = st.session_state.detector
            stats = detector.get_statistics()
            
            # Metrics
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
        
        if "Red" in light_status:
            st.markdown('<div class="success-card">🔴 RED LIGHT ACTIVE</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-card">🟢 GREEN LIGHT ACTIVE</div>', unsafe_allow_html=True)
        
        # Video processing status
        if 'output_video_path' in st.session_state and st.session_state.output_video_path:
            st.markdown("### 🎬 Video Status")
            st.success("✅ Processed video ready!")
            st.info(f"📁 Saved to: {os.path.basename(st.session_state.output_video_path)}")
        else:
            st.markdown("### 🎬 Video Status")
            st.info("⏳ No processed video yet")
        
        # Video troubleshooting
        with st.expander("🔧 Video Troubleshooting"):
            st.markdown("**If videos don't play after download:**")
            st.markdown("1. Try different video players (VLC, Windows Media Player)")
            st.markdown("2. Check if your browser supports MP4 playback")
            st.markdown("3. Try downloading and playing locally")
            
            if st.button("🧪 Test Video Creation"):
                with st.spinner("Creating test video..."):
                    success, message = _create_test_video()
                    if success:
                        st.success("✅ Test video created successfully!")
                        st.info("Video creation is working properly")
                    else:
                        st.error(f"❌ Test video failed: {message}")
                        st.info("There may be a system-level video codec issue")
    
    # Results section
    if 'results' in st.session_state:
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
            st.metric("Video Duration", f"{results.get('video_duration', 0):.1f}s")
        
        # Additional metrics
        col_result5, col_result6 = st.columns(2)
        
        with col_result5:
            fps = results['total_frames'] / results['processing_time'] if results['processing_time'] > 0 else 0
            st.metric("Processing FPS", f"{fps:.1f}")
        
        with col_result6:
            st.metric("Processing Speed", f"{results.get('processing_fps', 0):.1f} fps")
        
        # Processed Video Display
        if 'output_video_path' in st.session_state and st.session_state.output_video_path:
            st.markdown("### 🎬 Processed Video Output")
            
            video_path = st.session_state.output_video_path
            if os.path.exists(video_path):
                # Validate the video before displaying
                is_valid, validation_message = _validate_video(video_path)
                
                if is_valid:
                    # Display the processed video
                    st.video(video_path)
                    
                    # Download button for the processed video
                    with open(video_path, "rb") as video_file:
                        st.download_button(
                            label="📥 Download Processed Video",
                            data=video_file.read(),
                            file_name=os.path.basename(video_path),
                            mime="video/mp4"
                        )
                    
                    st.success(f"🎉 Your processed video is ready! Found {results['total_violations']} violations.")
                    
                    # Show video info
                    cap = cv2.VideoCapture(video_path)
                    video_fps = cap.get(cv2.CAP_PROP_FPS)
                    video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    video_duration = video_frames / video_fps if video_fps > 0 else 0
                    cap.release()
                    
                    st.info(f"📊 Video Info: {video_frames} frames, {video_fps:.1f} FPS, {video_duration:.1f} seconds")
                    
                else:
                    st.error(f"❌ Video validation failed: {validation_message}")
                    st.error("Please try processing again with different settings.")
            else:
                st.error("❌ Processed video file not found. Please try processing again.")
        
        # Download results
        st.markdown("### 💾 Download Results")
        # ...existing code...
        # Create results JSON
        serializable_results = recursive_convert(results)
        results_json = json.dumps(serializable_results, indent=2)
        st.download_button(
            label="📄 Download Results JSON",
            data=results_json,
            file_name="detection_results.json",
            mime="application/json"
        )
# ...existing code...
        # Create results JSON
       # ...existing code...
# Create results JSON
        serializable_results = recursive_convert(results)
        results_json = json.dumps(serializable_results, indent=2)
        st.download_button(
            label="📄 Download Results JSON",
            data=results_json,
            file_name="detection_results.json",
            mime="application/json"
        )
    
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
