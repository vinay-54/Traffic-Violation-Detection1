#!/usr/bin/env python3
"""
Comprehensive test script for the FINAL FIXED VERSION
"""

import os
import cv2
import numpy as np
from enhanced_detector_fixed import RedLightViolationDetector

def create_test_video_with_vehicles():
    """Create a test video with moving vehicles"""
    output_path = "test_video_final.mp4"
    
    # Video parameters
    fps = 25
    width, height = 640, 480
    duration = 5  # 5 seconds
    
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
        
        # Add moving vehicles (cars) that will cross the detection line
        for j in range(3):
            x = int((i + j * 50) % width)
            y = 250 - j * 30
            
            # Make vehicles move down (towards detection line)
            if i > fps * 2:  # After 2 seconds, vehicles move down
                y = min(300, 250 - j * 30 + (i - fps * 2) * 2)
            
            cv2.rectangle(frame, (x, y), (x + 60, y + 40), (0, 255, 0), -1)
            cv2.rectangle(frame, (x, y), (x + 60, y + 40), (0, 0, 0), 2)
        
        # Add traffic light
        if i > fps * 2:  # Red light after 2 seconds
            cv2.circle(frame, (width - 50, 50), 20, (0, 0, 255), -1)  # Red light
        else:
            cv2.circle(frame, (width - 50, 50), 20, (0, 255, 0), -1)  # Green light
        
        out.write(frame)
    
    out.release()
    print(f"✅ Test video created: {output_path}")
    return output_path

def test_final_version():
    """Test the final fixed version"""
    print("🚀 Testing FINAL FIXED VERSION...")
    print("=" * 50)
    
    # Create test video
    test_video_path = create_test_video_with_vehicles()
    
    # Initialize detector with optimal settings for testing
    config = {
        'frame_skip': 2,  # Process more frames for better testing
        'confidence_threshold': 0.1,  # Low threshold to catch all detections
        'red_light_start_time': 2,  # Red light starts at 2 seconds
        'line_y_threshold': 280,  # Detection line position
        'flash_duration_frames': 30,
        'output_resolution': (640, 480),
        'violation_save_path': 'test_violations_final'
    }
    
    print("📋 Configuration:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    try:
        detector = RedLightViolationDetector('yolov8n.pt', config)
        print("✅ Detector initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}")
        return
    
    # Process video
    output_path = "final_output_test.mp4"
    try:
        print(f"\n🎬 Processing video: {test_video_path}")
        print(f"📤 Output will be saved to: {output_path}")
        
        results = detector.process_video(test_video_path, output_path)
        
        print("\n✅ Video processing completed!")
        print("📊 Results:")
        print(f"   - Total frames: {results['total_frames']}")
        print(f"   - Processed frames: {results['processed_frames']}")
        print(f"   - Total violations: {results['total_violations']}")
        print(f"   - Processing time: {results['processing_time']:.2f}s")
        print(f"   - Output path: {results['output_path']}")
        
        # Check if output video exists and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"\n✅ Output video created: {output_path}")
            print(f"📁 File size: {file_size:,} bytes")
            
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
                    print("✅ All conditions met:")
                    print("   ✓ Video file created")
                    print("   ✓ File size > 0")
                    print("   ✓ Frame count > 0")
                    print("   ✓ Processing completed successfully")
                    print("   ✓ Results returned")
                else:
                    print("⚠️ WARNING: Output video has 0 frames")
            else:
                print("❌ ERROR: Output video file is empty")
        else:
            print("❌ ERROR: Output video file not found")
            
        # Check violations directory
        violations_dir = config['violation_save_path']
        if os.path.exists(violations_dir):
            violation_images = [f for f in os.listdir(violations_dir) if f.endswith(('.jpg', '.png'))]
            print(f"📸 Violation screenshots: {len(violation_images)} found")
        else:
            print("📸 Violation screenshots: Directory not found")
            
    except Exception as e:
        print(f"❌ Error during video processing: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
        print(f"\n🧹 Cleaned up test video: {test_video_path}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_final_version()
