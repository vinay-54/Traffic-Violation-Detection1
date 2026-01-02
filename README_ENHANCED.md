# 🚦 Enhanced Red Light Violation Detection System

A comprehensive, AI-powered traffic monitoring system that detects red light violations using YOLO object detection and provides a beautiful Streamlit web interface for real-time monitoring and analysis.

## ✨ Enhanced Features

### 🎯 **Core Detection System**
- **Advanced YOLO Integration**: Support for multiple YOLO models (YOLOv8n, YOLOv8s, YOLOv8m, custom)
- **Real-time Vehicle Tracking**: Persistent object tracking across frames
- **Intelligent Violation Detection**: Precise detection of vehicles crossing stop lines during red lights
- **Multi-class Detection**: Detects cars, trucks, buses, motorcycles, and other vehicles

### 🖥️ **Modern Web Interface**
- **Beautiful Streamlit UI**: Professional, responsive web interface
- **Real-time Statistics**: Live monitoring of active vehicles and violations
- **Interactive Configuration**: Easy parameter tuning through sidebar controls
- **Progress Tracking**: Real-time processing progress with visual feedback
- **Results Visualization**: Interactive charts and graphs for data analysis

### 📊 **Advanced Analytics**
- **Violation Timeline Charts**: Visual representation of violations over time
- **Performance Metrics**: Processing speed, detection accuracy, and efficiency scores
- **Export Capabilities**: Download results as JSON, CSV, or annotated videos
- **Violation Gallery**: Browse and analyze captured violation images
- **Statistical Reports**: Comprehensive violation analysis and reporting

### 🔧 **Enhanced Configuration**
- **Flexible Parameters**: Adjustable detection thresholds, frame rates, and processing settings
- **Model Selection**: Choose from different YOLO models based on speed/accuracy needs
- **Custom Detection Zones**: Configurable stop line positions and detection areas
- **Advanced Settings**: Fine-tune flash duration, output resolution, and more

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd Red-Light-Violation-Detection-main

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Web Application

```bash
# Start the Streamlit app
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### 3. Command Line Usage

```bash
# Run the enhanced detector directly
python enhanced_detector.py

# Or use the original script
python main.py
```

## 📁 Project Structure

```
Red-Light-Violation-Detection-main/
├── 📄 app.py                          # Main Streamlit web application
├── 📄 enhanced_detector.py            # Enhanced detection engine
├── 📄 main.py                         # Original detection script
├── 📄 config.py                       # Configuration management
├── 📄 utils.py                        # Utility functions and analytics
├── 📄 requirements.txt                # Python dependencies
├── 📄 README_ENHANCED.md              # This enhanced documentation
├── 📄 README.md                       # Original documentation
├── 🎯 yolov8n.pt                      # YOLO model weights
├── 🎯 best.pt                         # Custom trained model (if available)
├── 📊 violations/                     # Saved violation images
├── 📊 results/                        # Processing results and reports
└── 📊 charts/                         # Generated analytics charts
```

## 🎛️ Configuration Options

### Detection Parameters
- **Frame Skip**: Process every Nth frame (1-10, default: 5)
- **Confidence Threshold**: Minimum detection confidence (0.1-1.0, default: 0.5)
- **Red Light Start Time**: When red light begins in video (seconds)
- **Detection Line Position**: Y-coordinate of stop line (200-400, default: 310)

### Advanced Settings
- **Flash Duration**: How long to highlight violations (30-120 frames)
- **Output Resolution**: Video output dimensions
- **Model Selection**: Choose YOLO model variant
- **Processing Speed**: Balance between speed and accuracy

## 📊 Analytics & Reporting

### Real-time Statistics
- Active vehicle count
- Total violations detected
- Processing time and FPS
- Traffic light status

### Data Export
- **JSON Reports**: Complete detection results with metadata
- **CSV Reports**: Tabular violation data for analysis
- **Annotated Videos**: Processed videos with detection overlays
- **Violation Images**: Cropped images of violating vehicles

### Visualization Features
- Interactive violation timeline charts
- Hourly and daily violation distributions
- Vehicle frequency analysis
- Performance metrics dashboard

## 🔧 Advanced Usage

### Custom Model Integration

```python
from enhanced_detector import RedLightViolationDetector

# Initialize with custom model
detector = RedLightViolationDetector(
    model_path='path/to/your/model.pt',
    config={
        'confidence_threshold': 0.6,
        'frame_skip': 3,
        'red_light_start_time': 15
    }
)

# Process video
results = detector.process_video('input_video.mp4', 'output_video.mp4')
```

### Data Analysis

```python
from utils import load_violation_data, create_violation_summary

# Load and analyze results
data = load_violation_data('detection_results.json')
summary = create_violation_summary(data['violations'])

# Generate charts
from utils import generate_violation_charts
chart_paths = generate_violation_charts(data['violations'])
```

### Configuration Management

```python
from config import get_config, save_config

# Get default configuration
config = get_config('default')

# Modify settings
config['confidence_threshold'] = 0.7
config['frame_skip'] = 3

# Save custom configuration
save_config(config, 'my_config.json')
```

## 🎨 Web Interface Features

### Main Dashboard
- **Video Upload**: Drag-and-drop video file upload
- **Real-time Processing**: Live video processing with progress tracking
- **Configuration Panel**: Easy parameter adjustment
- **Results Display**: Comprehensive results with download options

### Analytics Dashboard
- **Violation Timeline**: Interactive chart showing violations over time
- **Performance Metrics**: Processing speed and efficiency indicators
- **Violation Gallery**: Browse captured violation images
- **Export Tools**: Download results in various formats

### Configuration Panel
- **Model Selection**: Choose from available YOLO models
- **Detection Parameters**: Adjust sensitivity and timing
- **Advanced Settings**: Fine-tune processing options
- **Theme Selection**: Choose UI appearance

## 📈 Performance Optimization

### Speed vs Accuracy Trade-offs
- **YOLOv8n**: Fastest processing, moderate accuracy
- **YOLOv8s**: Balanced speed and accuracy
- **YOLOv8m**: Highest accuracy, slower processing
- **Custom Models**: Optimized for specific use cases

### Processing Optimization
- **Frame Skipping**: Reduce processing load
- **Resolution Scaling**: Lower resolution for faster processing
- **Confidence Thresholds**: Adjust detection sensitivity
- **Batch Processing**: Process multiple videos efficiently

## 🔍 Troubleshooting

### Common Issues

**Model Loading Errors**
```bash
# Ensure model file exists
ls -la *.pt

# Check model compatibility
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

**Video Processing Issues**
```python
from utils import validate_video_file
is_valid, message = validate_video_file('your_video.mp4')
print(message)
```

**Performance Issues**
```python
from utils import get_system_info
info = get_system_info()
print(f"Available memory: {info['memory_available_gb']} GB")
```

### Performance Tips
- Use YOLOv8n for real-time processing
- Reduce frame skip for higher accuracy
- Lower video resolution for faster processing
- Close other applications to free up memory

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. For commercial use, please ensure compliance with local traffic monitoring regulations.

## 🙏 Acknowledgments

- **YOLO**: Ultralytics for the excellent object detection framework
- **Streamlit**: For the amazing web app framework
- **OpenCV**: For computer vision capabilities
- **Original Dataset**: Roboflow for the vehicle detection dataset

## 📞 Support

For questions, issues, or feature requests:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

---

**🚦 Drive safely and respect traffic signals! 🚦**
