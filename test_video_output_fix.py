#!/usr/bin/env python3
"""
Test script to verify video output fix
"""

import os
import cv2
import numpy as np
from enhanced_detector import RedLightViolationDetector

def create_simple_test_video():
    """Create a simple test video with vehicles"""
    output_path = "simple_test_video.mp4"
    
    # Video parameters
    fps = 25
    width, height = 640, 480
    duration = 3  # 3 seconds
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    print(f"Creating test video: {output_path}")
    
    # Create frames
    for i in range(fps * duration):
        # Create a frame with moving vehicles
        frame = np.ones((height, width, 3), dtype=np.uint8) * 100  # Gray background
        
        # Add road
        cv2.rectangle(frame, (0, 300), (width, height), (50, 50, 50), -1)
        
        # Add moving vehicles (cars)
        for j in range(3):
            x = int((i + j * 50) % width)
            y = 250 - j * 30
            cv2.rectangle(frame, (x, y), (x + 60, y + 40), (0, 255, 0), -1)
            cv2.rectangle(frame, (x, y), (x + 60, y + 40), (0, 0, 0), 2)
        
        # Add traffic light
        if i > fps * 1.5:  # Red light after 1.5 seconds
            cv2.circle(frame, (width - 50, 50), 20, (0, 0, 255), -1)  # Red light
        else:
            cv2.circle(frame, (width - 50, 50), 20, (0, 255, 0), -1)  # Green light
        
        out.write(frame)
    
    out.release()
    print(f"✅ Test video created: {output_path}")
    return output_path

def test_video_output():
    """Test video output functionality"""
    print("🚀 Testing Video Output Fix...")
    
    # Create test video
    test_video_path = create_simple_test_video()
    
    # Initialize detector with lower confidence for testing
    config = {
        'frame_skip': 3,
        'confidence_threshold': 0.1,  # Very low threshold for testing
        'red_light_start_time': 1.5,
        'line_y_threshold': 280,
        'flash_duration_frames': 30,
        'output_resolution': (640, 480),
        'violation_save_path': 'test_violations'
    }
    
    detector = RedLightViolationDetector('yolov8n.pt', config)
    
    # Process video
    output_path = "test_output_fixed.mp4"
    try:
        print(f"Processing video: {test_video_path}")
        print(f"Output will be saved to: {output_path}")
        
        results = detector.process_video(test_video_path, output_path)
        
        print("✅ Video processing completed!")
        print(f"📊 Results:")
        print(f"   - Total frames: {results['total_frames']}")
        print(f"   - Total violations: {results['total_violations']}")
        print(f"   - Processing time: {results['processing_time']:.2f}s")
        
        # Check if output video exists and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Output video created: {output_path}")
            print(f"📁 File size: {file_size} bytes")
            
            if file_size > 0:
                # Get video info
                cap = cv2.VideoCapture(output_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                
                print(f"📹 Video info: {frame_count} frames, {fps:.1f} FPS, {width}x{height}")
                
                if frame_count > 0:
                    print("🎉 SUCCESS: Video output is working correctly!")
                else:
                    print("⚠️ WARNING: Output video has 0 frames")
            else:
                print("❌ ERROR: Output video file is empty")
        else:
            print("❌ ERROR: Output video file not found")
            
    except Exception as e:
        print(f"❌ Error during video processing: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
        print(f"🧹 Cleaned up test video: {test_video_path}")

if __name__ == "__main__":
    test_video_output()
