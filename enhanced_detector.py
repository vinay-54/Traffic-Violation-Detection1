import os
import cv2 as cv
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from collections import defaultdict
import time
import json
from typing import Dict, List, Tuple, Optional
import logging

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
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedLightViolationDetector:
    """
    Enhanced Red Light Violation Detection System - FIXED VERSION
    """
    
    def __init__(self, model_path: str = 'yolov8n.pt', config: Dict = None):
        """
        Initialize the detector with model and configuration
        
        Args:
            model_path: Path to YOLO model weights
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.model = self._load_model(model_path)
        self.violations = []
        self.violation_timers = {}
        self.object_y_hist = defaultdict(list)
        self.saved_ids = set()
        self.frame_count = 0
        self.start_time = time.time()
        
        # Check if tracking is available
        try:
            import lap
            self.tracking_available = True
            logger.info("✅ Tracking module (lap) available - full functionality enabled")
        except ImportError:
            self.tracking_available = False
            logger.warning("⚠️ Tracking module (lap) not available - using detection-only mode")
            logger.info("💡 Install lap>=0.5.12 for full tracking functionality")
        
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'frame_skip': 5,
            'line_y_threshold': 310,
            'red_light_start_time': 12,
            'flash_duration_frames': 60,
            'confidence_threshold': 0.5,
            'classes_to_detect': [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12],
            'output_resolution': (854, 480),
            'violation_save_path': 'violations'
        }
    
    def _load_model(self, model_path: str) -> YOLO:
        """Load YOLO model with error handling"""
        try:
            if not os.path.exists(model_path):
                logger.warning(f"Model {model_path} not found, using default YOLOv8n")
                model_path = 'yolov8n.pt'
            
            model = YOLO(model_path)
            logger.info(f"Model loaded successfully: {model_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def is_red_light(self, cap: cv.VideoCapture) -> bool:
        """
        Check if traffic light is red based on video timestamp
        
        Args:
            cap: Video capture object
            
        Returns:
            bool: True if red light is active
        """
        try:
            current_pos_ms = cap.get(cv.CAP_PROP_POS_MSEC)
            current_pos_seconds = current_pos_ms / 1000.0
            red_light_start_time = self.config.get('red_light_start_time', 12)
            return current_pos_seconds > red_light_start_time
        except Exception as e:
            logger.error(f"Error checking red light status: {e}")
            return False
    
    def draw_traffic_light(self, frame: np.ndarray, is_red: bool) -> np.ndarray:
        """
        Draw traffic light indicator on frame
        
        Args:
            frame: Input frame
            is_red: Whether red light is active
            
        Returns:
            np.ndarray: Frame with traffic light indicator
        """
        height, width = frame.shape[:2]
        
        # Draw traffic light background
        cv.rectangle(frame, (width - 80, 10), (width - 10, 80), (0, 0, 0), -1)
        cv.rectangle(frame, (width - 80, 10), (width - 10, 80), (255, 255, 255), 2)
        
        # Draw appropriate light
        if is_red:
            cv.circle(frame, (width - 45, 45), 20, (0, 0, 255), -1)  # Red light
            cv.putText(frame, "RED", (width - 70, 95), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv.circle(frame, (width - 45, 45), 20, (0, 255, 0), -1)  # Green light
            cv.putText(frame, "GREEN", (width - 75, 95), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame
    
    def should_flash_vehicle(self, vehicle_id: int) -> bool:
        """Check if vehicle should flash (violation indicator)"""
        if vehicle_id in self.violation_timers:
            self.violation_timers[vehicle_id] += 1
            flash_duration = self.config.get('flash_duration_frames', 60)
            if self.violation_timers[vehicle_id] < flash_duration:
                return True
            else:
                del self.violation_timers[vehicle_id]
        return False
    
    def save_violation_image(self, frame: np.ndarray, bbox: List[float], vehicle_id: int):
        """Save violation screenshot"""
        try:
            # Create violations directory if it doesn't exist
            violations_dir = self.config.get('violation_save_path', 'violations')
            os.makedirs(violations_dir, exist_ok=True)
            
            # Extract bounding box coordinates
            x1, y1, x2, y2 = map(int, bbox)
            
            # Add padding to the bounding box
            padding = 20
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(frame.shape[1], x2 + padding)
            y2 = min(frame.shape[0], y2 + padding)
            
            # Crop the violation area
            violation_img = frame[y1:y2, x1:x2]
            
            # Save the image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = f"violation_{vehicle_id}_{timestamp}.jpg"
            filepath = os.path.join(violations_dir, filename)
            
            cv.imwrite(filepath, violation_img)
            logger.info(f"Violation screenshot saved: {filepath}")
            
            # Add to violations list
            self.violations.append({
                'vehicle_id': vehicle_id,
                'timestamp': timestamp,
                'bbox': bbox,
                'image_path': filepath
            })
            
        except Exception as e:
            logger.error(f"Error saving violation image: {e}")
    
    def process_frame(self, frame: np.ndarray, cap: cv.VideoCapture) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame for vehicle detection and violation analysis
        
        Args:
            frame: Input frame
            cap: Video capture object
            
        Returns:
            Tuple[np.ndarray, Dict]: Processed frame and statistics
        """
        # Resize frame for processing
        output_resolution = self.config.get('output_resolution', (854, 480))
        frame_resized = cv.resize(frame, output_resolution)
        
        # Run detection with fallback for configuration
        classes_to_detect = self.config.get('classes_to_detect', [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12])
        confidence_threshold = self.config.get('confidence_threshold', 0.5)
        
        if self.tracking_available:
            # Use tracking if available
            results = self.model.track(
                frame_resized, 
                persist=True, 
                classes=classes_to_detect,
                conf=confidence_threshold
            )
        else:
            # Use detection-only mode
            results = self.model(
                frame_resized,
                classes=classes_to_detect,
                conf=confidence_threshold
            )
        
        # Get annotated frame
        annotated_frame = results[0].plot()
        
        # Draw detection zone
        cv.line(annotated_frame, (10, 300), (844, 315), (0, 0, 255), thickness=2)
        cv.line(annotated_frame, (844, 0), (844, 315), (0, 0, 255), thickness=2)
        cv.line(annotated_frame, (10, 0), (10, 300), (0, 0, 255), thickness=2)
        
        # Check for violations
        is_red = self.is_red_light(cap)
        active_vehicles = 0
        
        # Handle both tracking and detection modes
        if is_red and hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
            # Tracking mode - use vehicle IDs
            for box in results[0].boxes:
                vehicle_id = int(box.id)
                active_vehicles += 1
                
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                start_y = y2 - 20
                
                self.object_y_hist[vehicle_id].append(start_y)
                
                if len(self.object_y_hist[vehicle_id]) >= 2:
                    prev_y = self.object_y_hist[vehicle_id][-2]
                    curr_y = self.object_y_hist[vehicle_id][-1]
                    
                    # Check if line crossed
                    line_y_threshold = self.config.get('line_y_threshold', 310)
                    if (prev_y < line_y_threshold and 
                        curr_y >= line_y_threshold and 
                        vehicle_id not in self.saved_ids):
                        
                        self.violation_timers[vehicle_id] = 0
                        self.save_violation_image(frame_resized, box.xyxy[0], vehicle_id)
                        self.saved_ids.add(vehicle_id)
                
                # Flash violation indicator
                if self.should_flash_vehicle(vehicle_id):
                    cv.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
                    cv.putText(annotated_frame, "VIOLATION!", (x2-80, y2+25), 
                              cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            # Detection-only mode - count all detected vehicles
            if is_red and results[0].boxes is not None:
                for box in results[0].boxes:
                    active_vehicles += 1
                    # Draw bounding box for all detected vehicles
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw traffic light and stats
        annotated_frame = self.draw_traffic_light(annotated_frame, is_red)
        
        # Draw stats box
        cv.rectangle(annotated_frame, (5, 4), (275, 65), (0, 0, 0), 2)
        cv.rectangle(annotated_frame, (5, 4), (275, 65), (255, 255, 255), -1)
        
        cv.putText(annotated_frame, f"Active Vehicles: {active_vehicles}", 
                  (25, 20), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv.putText(annotated_frame, f"Violations: {len(self.violations)}", 
                  (25, 40), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv.putText(annotated_frame, f"Light: {'RED' if is_red else 'GREEN'}", 
                  (25, 60), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255) if is_red else (0, 255, 0), 2)
        
        return annotated_frame, {
            'active_vehicles': active_vehicles,
            'violations': len(self.violations),
            'is_red_light': is_red,
            'frame_count': self.frame_count
        }
    
    def process_video(self, video_path: str, output_path: str = None) -> Dict:
        """
        Process entire video file - FIXED VERSION
        
        Args:
            video_path: Path to input video
            output_path: Path for output video (optional)
            
        Returns:
            Dict: Processing results and statistics
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cap = cv.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv.CAP_PROP_FPS)
        width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Input video: {fps:.1f} FPS, {width}x{height}, {total_frames} frames")
        
        # Setup output video - FIXED VERSION
        out = None
        processed_frame_count = 0
        
        if output_path:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Use H.264 codec for better compatibility
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
            frame_skip = self.config.get('frame_skip', 5)
            output_fps = max(1, fps / frame_skip)  # Ensure FPS is at least 1
            output_resolution = self.config.get('output_resolution', (854, 480))
            
            logger.info(f"Creating output video: {output_path}")
            logger.info(f"Output settings: {output_fps:.1f} FPS, {output_resolution}")
            
            out = cv.VideoWriter(output_path, fourcc, output_fps, output_resolution)
            
            # Verify video writer is initialized
            if not out.isOpened():
                logger.error(f"Failed to initialize video writer for: {output_path}")
                raise RuntimeError(f"Could not create output video: {output_path}")
            else:
                logger.info(f"✅ Video writer initialized successfully: {output_path}")
        
        self.frame_count = 0
        processing_stats = []
        
        logger.info(f"Starting video processing: {video_path}")
        
        try:
            frame_count = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
            frame_number = 0
            while cap.isOpened() and frame_number < frame_count:
                ret, frame = cap.read()
                if not ret:
                    break
                # ... your processing ...
                frame_number += 1
                
                self.frame_count += 1
                frame_skip = self.config.get('frame_skip', 5)
                
                # Only process every nth frame based on frame_skip
                if self.frame_count % frame_skip != 0:
                    continue
                
                # Process frame
                processed_frame, stats = self.process_frame(frame, cap)
                processing_stats.append(stats)
                processed_frame_count += 1
                
                # Save output frame - FIXED VERSION
                if out and processed_frame is not None:
                    # Ensure frame is the correct size and format
                    if processed_frame.shape[:2] != output_resolution[::-1]:
                        processed_frame = cv.resize(processed_frame, output_resolution)
                    
                    # Ensure frame is in BGR format
                    if len(processed_frame.shape) == 3 and processed_frame.shape[2] == 3:
                        out.write(processed_frame)
                        if processed_frame_count % 10 == 0:  # Log every 10 frames
                            logger.debug(f"Wrote frame {processed_frame_count} to output video")
                    else:
                        logger.warning(f"Invalid frame format at frame {processed_frame_count}")
                
                # Log progress
                if self.frame_count % (frame_skip * 10) == 0:
                    progress = (self.frame_count / total_frames) * 100
                    logger.info(f"Processing progress: {progress:.1f}% ({self.frame_count}/{total_frames} frames)")
                    
        except Exception as e:
            logger.error(f"Error during video processing: {e}")
            raise
        finally:
            cap.release()
            if out:
                out.release()
                logger.info(f"✅ Video writer released. Processed {processed_frame_count} frames.")
                logger.info(f"✅ Output video saved: {output_path}")
        
        # Save results
        self.save_results()
        
        return {
            'total_frames': self.frame_count,
            'processed_frames': processed_frame_count,
            'total_violations': len(self.violations),
            'processing_time': time.time() - self.start_time,
            'stats': processing_stats,
            'output_path': output_path
        }
    
    def save_results(self, output_file: str = 'detection_results.json'):
        """Save detection results to JSON file"""
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'total_violations': len(self.violations),
                'violations': self.violations,
                'config': self.config
            }
            
            with open(output_file, 'w') as f:
                serializable_results = recursive_convert(results)
                json.dump(serializable_results, f, indent=2)
            
            logger.info(f"Results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def get_statistics(self) -> Dict:
        """Get current detection statistics"""
        return {
            'total_violations': len(self.violations),
            'active_vehicles': len(self.object_y_hist),
            'processing_time': time.time() - self.start_time,
            'frame_count': self.frame_count
        }
    
    def _get_class_name(self, class_id: int) -> str:
        """Get human-readable class name from class ID"""
        class_names = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
            5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
            10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter'
        }
        return class_names.get(class_id, f'class_{class_id}')


def main():
    """Main function for standalone execution"""
    # Example usage
    detector = RedLightViolationDetector()
    
    try:
        # Process video
        results = detector.process_video(
            video_path="CCTV Footage.mp4",
            output_path="Annotated_Video.mp4"
        )
        
        print(f"Processing completed!")
        print(f"Total violations: {results['total_violations']}")
        print(f"Processing time: {results['processing_time']:.2f} seconds")
        print(f"Output video: {results['output_path']}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()
