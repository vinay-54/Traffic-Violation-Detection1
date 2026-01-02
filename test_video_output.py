#!/usr/bin/env python3
"""
Test script for video output functionality
"""

import os
import cv2
import numpy as np
from enhanced_detector import RedLightViolationDetector

def create_test_video():
    """Create a simple test video for testing"""
    output_path = "test_video.mp4"
    
    # Video parameters
    fps = 25
    width, height = 640, 480
    duration = 5  # 5 seconds
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Create frames
    for i in range(fps * duration):
        # Create a simple frame with moving rectangle (simulating a vehicle)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add a moving rectangle (vehicle)
        x = int((i / (fps * duration)) * width)
        cv2.rectangle(frame, (x, 200), (x + 50, 250), (0, 255, 0), -1)
        
        # Add traffic light indicator
        if i > fps * 2:  # Red light after 2 seconds
            cv2.circle(frame, (width - 50, 50), 20, (0, 0, 255), -1)  # Red light
        else:
            cv2.circle(frame, (width - 50, 50), 20, (0, 255, 0), -1)  # Green light
        
        out.write(frame)
    
    out.release()
    print(f"✅ Test video created: {output_path}")
    return output_path

def test_video_processing():
    """Test video processing with output"""
    print("🚀 Testing Video Processing and Output...")
    
    # Create test video
    test_video_path = create_test_video()
    
    # Initialize detector
    config = {
        'frame_skip': 2,
        'confidence_threshold': 0.3,
        'red_light_start_time': 2,
        'line_y_threshold': 250,
        'flash_duration_frames': 30,
        'output_resolution': (640, 480),
        'violation_save_path': 'test_violations'
    }
    
    detector = RedLightViolationDetector('yolov8n.pt', config)
    
    # Process video
    output_path = "test_output.mp4"
    try:
        results = detector.process_video(test_video_path, output_path)
        
        print("✅ Video processing completed successfully!")
        print(f"📊 Results:")
        print(f"   - Total frames: {results['total_frames']}")
        print(f"   - Total violations: {results['total_violations']}")
        print(f"   - Processing time: {results['processing_time']:.2f}s")
        print(f"   - Output video: {output_path}")
        
        # Check if output video exists
        if os.path.exists(output_path):
            print(f"✅ Output video created successfully: {output_path}")
            
            # Get video info
            cap = cv2.VideoCapture(output_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            print(f"📹 Output video info: {frame_count} frames, {fps:.1f} FPS")
        else:
            print("❌ Output video not found!")
            
    except Exception as e:
        print(f"❌ Error during video processing: {e}")
    
    # Cleanup
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
        print(f"🧹 Cleaned up test video: {test_video_path}")

if __name__ == "__main__":
    test_video_processing()
