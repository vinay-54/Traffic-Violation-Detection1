#!/usr/bin/env python3
"""
Demo script to test the Red Light Violation Detection System
"""

import os
import sys
import time
from datetime import datetime

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
def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing package imports...")
    
    try:
        import ultralytics
        print("✅ ultralytics imported successfully")
    except ImportError as e:
        print(f"❌ ultralytics import failed: {e}")
        return False
    
    try:
        import cv2
        print("✅ opencv-python imported successfully")
    except ImportError as e:
        print(f"❌ opencv-python import failed: {e}")
        return False
    
    try:
        import streamlit
        print("✅ streamlit imported successfully")
    except ImportError as e:
        print(f"❌ streamlit import failed: {e}")
        return False
    
    try:
        import numpy
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    try:
        import pandas
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import plotly
        print("✅ plotly imported successfully")
    except ImportError as e:
        print(f"❌ plotly import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ pillow imported successfully")
    except ImportError as e:
        print(f"❌ pillow import failed: {e}")
        return False
    
    return True

def test_yolo_model():
    """Test YOLO model loading"""
    print("\n🔍 Testing YOLO model loading...")
    
    try:
        from ultralytics import YOLO
        
        # Check if model files exist
        model_files = ['yolov8n.pt', 'best.pt']
        available_models = []
        
        for model in model_files:
            if os.path.exists(model):
                available_models.append(model)
                print(f"✅ Found model: {model}")
            else:
                print(f"⚠️  Model not found: {model}")
        
        if not available_models:
            print("❌ No YOLO model files found!")
            return False
        
        # Try to load the first available model
        model_path = available_models[0]
        print(f"🔄 Loading model: {model_path}")
        
        model = YOLO(model_path)
        print("✅ YOLO model loaded successfully!")
        
        # Test basic model info
        print(f"   - Model type: {type(model).__name__}")
        print(f"   - Model path: {model_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ YOLO model loading failed: {e}")
        return False

def test_enhanced_detector():
    """Test enhanced detector initialization"""
    print("\n🔍 Testing enhanced detector...")
    
    try:
        from enhanced_detector import RedLightViolationDetector
        
        # Test with default configuration
        detector = RedLightViolationDetector()
        print("✅ Enhanced detector initialized successfully!")
        
        # Test configuration
        print(f"   - Frame skip: {detector.config['frame_skip']}")
        print(f"   - Confidence threshold: {detector.config['confidence_threshold']}")
        print(f"   - Red light start time: {detector.config['red_light_start_time']}")
        print(f"   - Line Y threshold: {detector.config['line_y_threshold']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced detector test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    print("\n🔍 Testing utility functions...")
    
    try:
        from utils import get_system_info, validate_video_file
        
        # Test system info
        system_info = get_system_info()
        print("✅ System info retrieved successfully!")
        print(f"   - Platform: {system_info['platform']}")
        print(f"   - Python version: {system_info['python_version']}")
        print(f"   - CPU count: {system_info['cpu_count']}")
        print(f"   - Memory available: {system_info['memory_available_gb']} GB")
        print(f"   - OpenCV version: {system_info['opencv_version']}")
        
        # Test video validation (with non-existent file)
        is_valid, message = validate_video_file("non_existent_video.mp4")
        print(f"✅ Video validation test: {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Utility functions test failed: {e}")
        return False

def test_config():
    """Test configuration system"""
    print("\n🔍 Testing configuration system...")
    
    try:
        from config import get_config, validate_config, DEFAULT_CONFIG
        
        # Test default configuration
        config = get_config('default')
        print("✅ Configuration system working!")
        print(f"   - Frame skip: {config['frame_skip']}")
        print(f"   - Confidence threshold: {config['confidence_threshold']}")
        print(f"   - Output resolution: {config['output_resolution']}")
        
        # Test configuration validation
        errors = validate_config(config)
        if not errors:
            print("✅ Configuration validation passed!")
        else:
            print(f"⚠️  Configuration validation warnings: {errors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration system test failed: {e}")
        return False

def create_sample_data():
    """Create sample data for demonstration"""
    print("\n📁 Creating sample directories and files...")
    
    # Create directories
    directories = ['violations', 'results', 'charts']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create sample results file
    sample_results = {
        'timestamp': datetime.now().isoformat(),
        'total_violations': 5,
        'processing_time': 45.2,
        'total_frames': 1500,
        'config': {
            'frame_skip': 5,
            'confidence_threshold': 0.5,
            'red_light_start_time': 12
        }
    }
    
    import json
    with open('detection_results.json', 'w') as f:
        serializable_results = recursive_convert(sample_results)
        json.dump(serializable_results, f, indent=2)
    
    print("✅ Created sample detection results file")
    return True

def main():
    """Main demo function"""
    print("🚦 Red Light Violation Detection System - Demo")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Package import test failed!")
        return
    
    # Test YOLO model
    if not test_yolo_model():
        print("\n❌ YOLO model test failed!")
        return
    
    # Test enhanced detector
    if not test_enhanced_detector():
        print("\n❌ Enhanced detector test failed!")
        return
    
    # Test utilities
    if not test_utils():
        print("\n❌ Utility functions test failed!")
        return
    
    # Test configuration
    if not test_config():
        print("\n❌ Configuration system test failed!")
        return
    
    # Create sample data
    create_sample_data()
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! System is ready to use.")
    print("\n📋 Next steps:")
    print("1. Add a traffic video file (e.g., 'Traffic_Video.mp4')")
    print("2. Run: python main.py")
    print("3. Or run: streamlit run app.py")
    print("4. Or run: python run_app.py")
    print("\n📁 Available files:")
    print("   - main.py: Command line interface")
    print("   - app.py: Streamlit web interface")
    print("   - enhanced_detector.py: Advanced detection engine")
    print("   - config.py: Configuration management")
    print("   - utils.py: Utility functions")
    print("\n🚀 Your enhanced Red Light Violation Detection System is ready!")

if __name__ == "__main__":
    main()
