import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from ultralytics import YOLO
import cv2 as cv
from datetime import datetime
from collections import defaultdict
import time
import numpy as np
import json
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
# Configuration
CONFIG = {
    'model_path': 'yolov8n.pt',  # Use yolov8n.pt as fallback if best.pt not available
    'video_path': "input1.mp4",
    'output_path': "Annotated_Video.mp4",
    'frame_skip': 5,
    'red_light_start_time': 12,
    'line_y_threshold': 310,
    'confidence_threshold': 0.5,
    'classes_to_detect': [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12],
    'output_resolution': (854, 480),
    'violation_save_path': 'violations'
}

def load_model():
    """Load YOLO model with fallback"""
    try:
        # Try to load best.pt first
        if os.path.exists('best.pt'):
            print("Loading custom model: best.pt")
            return YOLO('best.pt')
        else:
            print("Custom model not found, loading default: yolov8n.pt")
            return YOLO('yolov8n.pt')
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Falling back to yolov8n.pt")
        return YOLO('yolov8n.pt')

def check_video_file(video_path):
    """Check if video file exists and can be opened"""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        print("Please ensure the video file exists in the current directory.")
        return False
    
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Could not open video file: {video_path}")
        return False
    
    # Get video properties
    fps = cap.get(cv.CAP_PROP_FPS)
    frame_count = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    
    print(f"✅ Video loaded successfully:")
    print(f"   - Resolution: {width}x{height}")
    print(f"   - FPS: {fps:.1f}")
    print(f"   - Total frames: {frame_count}")
    print(f"   - Duration: {frame_count/fps:.1f} seconds")
    
    return True

def is_red_light(cap):
    """Check if traffic light is red based on video timestamp"""
    try:
        current_pos_ms = cap.get(cv.CAP_PROP_POS_MSEC)
        current_pos_seconds = current_pos_ms / 1000.0
        return current_pos_seconds > CONFIG['red_light_start_time']
    except Exception as e:
        print(f"Error checking red light status: {e}")
        return False

def draw_traffic_light(frame, is_red_light):
    """Draw traffic light indicator on frame"""
    # Draw box
    cv.rectangle(frame, (800, 10), (850, 110), (50, 50, 50), -1)
    cv.rectangle(frame, (800, 10), (850, 110), (255, 255, 255), 2)

    # Red light
    color = (0, 0, 255) if is_red_light else (0, 0, 50)
    cv.circle(frame, (825, 35), 15, color, -1)

    # Green light
    color = (0, 255, 0) if not is_red_light else (0, 50, 0)
    cv.circle(frame, (825, 85), 15, color, -1)

def should_flash_vehicle(vehicle_id, violation_timers, flash_duration):
    """Check if vehicle should be flashed (violation indicator)"""
    if vehicle_id in violation_timers:
        time_since_violation = violation_timers[vehicle_id]

        # Stop flashing after the mentioned duration
        if time_since_violation > flash_duration:
            return False

        # Flash after every two processed frames 
        flash_pattern = (time_since_violation // 2) % 2 == 0

        # Increment the counter for next call
        violation_timers[vehicle_id] += 1

        return flash_pattern

    return False

def save_violation_image(frame, box, vehicle_id, violation_count):
    """Save violation image with metadata"""
    try:
        os.makedirs(CONFIG['violation_save_path'], exist_ok=True)
        
        x1, y1, x2, y2 = map(int, box)
        # Ensure coordinates are within frame bounds
        x1 = max(0, x1-5)
        y1 = max(0, y1-5)
        x2 = min(frame.shape[1], x2+5)
        y2 = min(frame.shape[0], y2+5)
        
        cropped = frame[y1:y2, x1:x2]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{CONFIG['violation_save_path']}/vehicle_{vehicle_id}_{timestamp}.jpg"
        
        cv.imwrite(filename, cropped)
        print(f"[SAVED] Violation #{violation_count}: {filename}")
        
        return filename
    except Exception as e:
        print(f"Error saving violation image: {e}")
        return None

def main():
    """Main function for red light violation detection"""
    print("🚦 Red Light Violation Detection System")
    print("=" * 50)
    
    # Check video file
    if not check_video_file(CONFIG['video_path']):
        return
    
    # Load model
    print("\n🔍 Loading YOLO model...")
    model = load_model()
    
    # Initialize video capture
    cap = cv.VideoCapture(CONFIG['video_path'])
    
    # Create violations directory
    os.makedirs(CONFIG['violation_save_path'], exist_ok=True)
    
    # Initialize variables
    object_y_hist = defaultdict(list)
    saved_ids = set()
    violation_timers = {}
    number_of_violations = 0
    
    # Get video properties
    fps = cap.get(cv.CAP_PROP_FPS)
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    
    start_time = time.time()
    frame_count = 0
    
    # Calculate flash duration
    flash_duration = int(fps/CONFIG['frame_skip'] * 2)  # Flash for 2 seconds
    
    # Setup output video
    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    output_fps = fps / CONFIG['frame_skip']
    out = cv.VideoWriter(CONFIG['output_path'], fourcc, output_fps, CONFIG['output_resolution'])
    
    print(f"\n🎬 Starting video processing...")
    print(f"   - Frame skip: {CONFIG['frame_skip']}")
    print(f"   - Red light starts at: {CONFIG['red_light_start_time']} seconds")
    print(f"   - Detection line at Y: {CONFIG['line_y_threshold']}")
    print(f"   - Output resolution: {CONFIG['output_resolution']}")
    
    try:
        frame_count = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        frame_number = 0
        while cap.isOpened() and frame_number < frame_count:
            ret, frame = cap.read()
            if not ret:
                break
            # ... your processing ...
            frame_number += 1

            frame_count += 1
            if frame_count % CONFIG['frame_skip'] != 0:
                continue

            # Resize frames
            frame_resized = cv.resize(frame, CONFIG['output_resolution'])

            # Track vehicles
            results = model.track(
                frame_resized, 
                persist=True, 
                classes=CONFIG['classes_to_detect'],
                conf=CONFIG['confidence_threshold']
            )

            # Plot model results
            annotated_frame = results[0].plot()

            # Draw detection zone
            cv.line(annotated_frame, (10, 300), (844, 315), (0, 0, 255), thickness=2)
            cv.line(annotated_frame, (844, 0), (844, 315), (0, 0, 255), thickness=2)
            cv.line(annotated_frame, (10, 0), (10, 300), (0, 0, 255), thickness=2)

            # Check for violations
            if is_red_light(cap):
                if results[0].boxes.id is not None:
                    for box in results[0].boxes:
                        vehicle_id = int(box.id)
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        start_y = y2 - 20

                        object_y_hist[vehicle_id].append(start_y)
                        
                        if len(object_y_hist[vehicle_id]) >= 2:
                            prev_y = object_y_hist[vehicle_id][-2]
                            curr_y = object_y_hist[vehicle_id][-1]

                            # Check if line crossed
                            if (prev_y < CONFIG['line_y_threshold'] and 
                                curr_y >= CONFIG['line_y_threshold'] and 
                                vehicle_id not in saved_ids):
                                
                                number_of_violations += 1
                                violation_timers[vehicle_id] = 0
                                save_violation_image(frame_resized, box.xyxy[0], vehicle_id, number_of_violations)
                                saved_ids.add(vehicle_id)

                        # Display flash graphics
                        if should_flash_vehicle(vehicle_id, violation_timers, flash_duration):
                            cv.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
                            cv.putText(annotated_frame, "VIOLATION!", (x2-80, y2+25), 
                                      cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            
            # Display Graphics
            draw_traffic_light(annotated_frame, is_red_light(cap))
            
            # Draw stats box
            cv.rectangle(annotated_frame, (5, 4), (275, 65), (0, 0, 0), 2)
            cv.rectangle(annotated_frame, (5, 4), (275, 65), (255, 255, 255), -1)
            
            active_vehicles = len(results[0].boxes) if results[0].boxes.id is not None else 0
            cv.putText(annotated_frame, f"Active Vehicles: {active_vehicles}", 
                      (25, 20), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv.putText(annotated_frame, f"Violations: {number_of_violations}", 
                      (25, 40), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            light_status = "RED" if is_red_light(cap) else "GREEN"
            light_color = (0, 0, 255) if is_red_light(cap) else (0, 255, 0)
            cv.putText(annotated_frame, f"Light: {light_status}", 
                      (25, 60), cv.FONT_HERSHEY_SIMPLEX, 0.6, light_color, 2)

            # Save and display frame
            out.write(annotated_frame)
            cv.imshow("Vehicle Detection", annotated_frame)

            if cv.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\n⏹ Processing stopped by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
    finally:
        # Cleanup
        cap.release()
        out.release()
        cv.destroyAllWindows()
        
        # Save results
        processing_time = time.time() - start_time
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'total_violations': number_of_violations,
            'processing_time': processing_time,
            'total_frames': frame_count,
            'config': CONFIG
        }
        
        with open('detection_results.json', 'w') as f:
            serializable_results = recursive_convert(results)
            json.dump(serializable_results, f, indent=2)
        
        # Print summary
        print("\n📊 Processing Summary:")
        print(f"   - Total violations detected: {number_of_violations}")
        print(f"   - Processing time: {processing_time:.2f} seconds")
        print(f"   - Frames processed: {frame_count}")
        print(f"   - Processing FPS: {frame_count/processing_time:.1f}")
        print(f"   - Output video: {CONFIG['output_path']}")
        print(f"   - Violation images: {CONFIG['violation_save_path']}/")
        print(f"   - Results saved: detection_results.json")

if __name__ == "__main__":
    main()
