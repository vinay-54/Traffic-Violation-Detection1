"""
Configuration file for Red Light Violation Detection System
"""

# Default configuration
DEFAULT_CONFIG = {
    # Detection parameters
    'frame_skip': 5,
    'confidence_threshold': 0.5,
    'red_light_start_time': 12,
    'line_y_threshold': 310,
    'flash_duration_frames': 60,
    
    # Model parameters
    'classes_to_detect': [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12],  # Vehicle classes
    'model_path': 'yolov8n.pt',
    
    # Video parameters
    'output_resolution': (854, 480),
    'output_fps': 30,
    
    # File paths
    'violation_save_path': 'violations',
    'results_save_path': 'results',
    
    # Processing parameters
    'max_violations_per_vehicle': 1,
    'save_violation_images': True,
    'save_annotated_video': True,
    
    # UI parameters
    'enable_realtime_display': True,
    'show_traffic_light': True,
    'show_statistics': True,
}

# Model configurations
MODEL_CONFIGS = {
    'yolov8n': {
        'path': 'yolov8n.pt',
        'description': 'YOLOv8 Nano - Fast and lightweight',
        'speed': 'fast',
        'accuracy': 'medium'
    },
    'yolov8s': {
        'path': 'yolov8s.pt',
        'description': 'YOLOv8 Small - Balanced speed and accuracy',
        'speed': 'medium',
        'accuracy': 'high'
    },
    'yolov8m': {
        'path': 'yolov8m.pt',
        'description': 'YOLOv8 Medium - High accuracy',
        'speed': 'slow',
        'accuracy': 'very_high'
    },
    'custom': {
        'path': 'best.pt',
        'description': 'Custom trained model',
        'speed': 'medium',
        'accuracy': 'high'
    }
}

# Vehicle classes for detection
VEHICLE_CLASSES = {
    0: 'person',
    1: 'bicycle',
    2: 'car',
    3: 'motorcycle',
    4: 'airplane',
    5: 'bus',
    7: 'truck',
    8: 'boat',
    9: 'traffic light',
    10: 'fire hydrant',
    11: 'stop sign',
    12: 'parking meter'
}

# Traffic light states
TRAFFIC_LIGHT_STATES = {
    'red': {
        'color': (0, 0, 255),
        'name': 'Red Light',
        'description': 'Stop - No vehicles should cross'
    },
    'green': {
        'color': (0, 255, 0),
        'name': 'Green Light',
        'description': 'Go - Vehicles can proceed'
    },
    'yellow': {
        'color': (0, 255, 255),
        'name': 'Yellow Light',
        'description': 'Caution - Prepare to stop'
    }
}

# Violation types
VIOLATION_TYPES = {
    'red_light_violation': {
        'name': 'Red Light Violation',
        'description': 'Vehicle crossed stop line during red light',
        'severity': 'high',
        'penalty': 'Fine and points'
    },
    'speeding': {
        'name': 'Speeding',
        'description': 'Vehicle exceeding speed limit',
        'severity': 'medium',
        'penalty': 'Fine'
    },
    'illegal_parking': {
        'name': 'Illegal Parking',
        'description': 'Vehicle parked in restricted area',
        'severity': 'low',
        'penalty': 'Fine'
    }
}

# UI themes
UI_THEMES = {
    'default': {
        'primary_color': '#FF4B4B',
        'secondary_color': '#667eea',
        'success_color': '#56ab2f',
        'warning_color': '#ff6b6b',
        'background_color': '#f0f2f6',
        'text_color': '#262730'
    },
    'dark': {
        'primary_color': '#FF6B6B',
        'secondary_color': '#4ECDC4',
        'success_color': '#45B7D1',
        'warning_color': '#FFA07A',
        'background_color': '#1E1E1E',
        'text_color': '#FFFFFF'
    },
    'professional': {
        'primary_color': '#2C3E50',
        'secondary_color': '#34495E',
        'success_color': '#27AE60',
        'warning_color': '#E74C3C',
        'background_color': '#ECF0F1',
        'text_color': '#2C3E50'
    }
}

def get_config(config_name='default'):
    """Get configuration by name"""
    if config_name == 'default':
        return DEFAULT_CONFIG.copy()
    elif config_name in MODEL_CONFIGS:
        config = DEFAULT_CONFIG.copy()
        config.update(MODEL_CONFIGS[config_name])
        return config
    else:
        raise ValueError(f"Unknown configuration: {config_name}")

def validate_config(config):
    """Validate configuration parameters"""
    errors = []
    
    # Check required parameters
    required_params = ['frame_skip', 'confidence_threshold', 'red_light_start_time']
    for param in required_params:
        if param not in config:
            errors.append(f"Missing required parameter: {param}")
    
    # Validate parameter ranges
    if 'frame_skip' in config and (config['frame_skip'] < 1 or config['frame_skip'] > 20):
        errors.append("frame_skip must be between 1 and 20")
    
    if 'confidence_threshold' in config and (config['confidence_threshold'] < 0.1 or config['confidence_threshold'] > 1.0):
        errors.append("confidence_threshold must be between 0.1 and 1.0")
    
    if 'red_light_start_time' in config and config['red_light_start_time'] < 0:
        errors.append("red_light_start_time must be non-negative")
    
    return errors

def save_config(config, filename='config.json'):
    """Save configuration to file"""
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

    serializable_config = recursive_convert(config)
    with open(filename, 'w') as f:
        json.dump(serializable_config, f, indent=2)

def load_config(filename='config.json'):
    """Load configuration from file"""
    import json
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_CONFIG.copy()
