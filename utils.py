"""
Utility functions for Red Light Violation Detection System
"""

import os
import json
import pandas as pd
import numpy as np
import cv2
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def load_violation_data(results_file: str = 'detection_results.json') -> Dict:
    """
    Load violation data from JSON file
    
    Args:
        results_file: Path to results JSON file
        
    Returns:
        Dict: Loaded violation data
    """
    try:
        with open(results_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Results file not found: {results_file}")
        return {}
    except json.JSONDecodeError:
        print(f"Invalid JSON in results file: {results_file}")
        return {}

def create_violation_summary(violations: List[Dict]) -> Dict:
    """
    Create summary statistics from violations
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        Dict: Summary statistics
    """
    if not violations:
        return {}
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(violations)
    
    # Parse timestamps
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    
    summary = {
        'total_violations': len(violations),
        'unique_vehicles': df['vehicle_id'].nunique(),
        'date_range': {
            'start': df['datetime'].min().isoformat(),
            'end': df['datetime'].max().isoformat()
        },
        'hourly_distribution': df['hour'].value_counts().sort_index().to_dict(),
        'daily_distribution': df['date'].value_counts().sort_index().to_dict(),
        'vehicle_frequency': df['vehicle_id'].value_counts().to_dict()
    }
    
    return summary

def generate_violation_charts(violations: List[Dict], save_path: str = 'charts') -> List[str]:
    """
    Generate visualization charts for violations
    
    Args:
        violations: List of violation dictionaries
        save_path: Directory to save charts
        
    Returns:
        List[str]: Paths to saved chart files
    """
    if not violations:
        return []
    
    os.makedirs(save_path, exist_ok=True)
    df = pd.DataFrame(violations)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    
    chart_paths = []
    
    # 1. Hourly violation distribution
    plt.figure(figsize=(12, 6))
    hourly_counts = df['hour'].value_counts().sort_index()
    plt.bar(hourly_counts.index, hourly_counts.values, color='red', alpha=0.7)
    plt.title('Violations by Hour of Day', fontsize=16, fontweight='bold')
    plt.xlabel('Hour of Day')
    plt.ylabel('Number of Violations')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    hourly_chart_path = os.path.join(save_path, 'hourly_violations.png')
    plt.savefig(hourly_chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(hourly_chart_path)
    
    # 2. Daily violation trend
    plt.figure(figsize=(12, 6))
    daily_counts = df['date'].value_counts().sort_index()
    plt.plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, markersize=6)
    plt.title('Daily Violation Trend', fontsize=16, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Number of Violations')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    daily_chart_path = os.path.join(save_path, 'daily_trend.png')
    plt.savefig(daily_chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(daily_chart_path)
    
    # 3. Vehicle violation frequency
    plt.figure(figsize=(12, 6))
    vehicle_counts = df['vehicle_id'].value_counts().head(20)
    plt.barh(range(len(vehicle_counts)), vehicle_counts.values, color='orange', alpha=0.7)
    plt.yticks(range(len(vehicle_counts)), [f'Vehicle {vid}' for vid in vehicle_counts.index])
    plt.title('Top 20 Vehicles by Violation Count', fontsize=16, fontweight='bold')
    plt.xlabel('Number of Violations')
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    vehicle_chart_path = os.path.join(save_path, 'vehicle_frequency.png')
    plt.savefig(vehicle_chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(vehicle_chart_path)
    
    return chart_paths

def create_interactive_dashboard(violations: List[Dict]) -> go.Figure:
    """
    Create interactive Plotly dashboard
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        go.Figure: Interactive dashboard figure
    """
    if not violations:
        return go.Figure()
    
    df = pd.DataFrame(violations)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Hourly Violations', 'Daily Trend', 'Vehicle Frequency', 'Violation Timeline'),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # 1. Hourly violations
    hourly_counts = df['hour'].value_counts().sort_index()
    fig.add_trace(
        go.Bar(x=hourly_counts.index, y=hourly_counts.values, name='Hourly Violations'),
        row=1, col=1
    )
    
    # 2. Daily trend
    daily_counts = df['date'].value_counts().sort_index()
    fig.add_trace(
        go.Scatter(x=daily_counts.index, y=daily_counts.values, mode='lines+markers', name='Daily Trend'),
        row=1, col=2
    )
    
    # 3. Vehicle frequency (top 10)
    vehicle_counts = df['vehicle_id'].value_counts().head(10)
    fig.add_trace(
        go.Bar(x=[f'Vehicle {vid}' for vid in vehicle_counts.index], 
               y=vehicle_counts.values, name='Vehicle Frequency'),
        row=2, col=1
    )
    
    # 4. Violation timeline
    fig.add_trace(
        go.Scatter(x=df['datetime'], y=range(len(df)), mode='markers', name='Violations'),
        row=2, col=2
    )
    
    fig.update_layout(
        title_text="Red Light Violation Analysis Dashboard",
        height=800,
        showlegend=False
    )
    
    return fig

def analyze_video_performance(results: Dict) -> Dict:
    """
    Analyze video processing performance
    
    Args:
        results: Processing results dictionary
        
    Returns:
        Dict: Performance analysis
    """
    if not results:
        return {}
    
    total_frames = results.get('total_frames', 0)
    processing_time = results.get('processing_time', 0)
    total_violations = results.get('total_violations', 0)
    
    if processing_time <= 0:
        return {}
    
    fps = total_frames / processing_time
    violations_per_minute = (total_violations / processing_time) * 60
    
    performance = {
        'total_frames': total_frames,
        'processing_time_seconds': processing_time,
        'processing_fps': fps,
        'total_violations': total_violations,
        'violations_per_minute': violations_per_minute,
        'efficiency_score': min(fps / 30, 1.0),  # Normalize to 30 FPS
        'detection_rate': total_violations / max(total_frames, 1) * 100
    }
    
    return performance

def export_violation_report(violations: List[Dict], output_file: str = 'violation_report.csv') -> str:
    """
    Export violations to CSV report
    
    Args:
        violations: List of violation dictionaries
        output_file: Output CSV file path
        
    Returns:
        str: Path to exported file
    """
    if not violations:
        return ""
    
    df = pd.DataFrame(violations)
    
    # Add additional columns
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['time'] = df['datetime'].dt.time
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.day_name()
    
    # Reorder columns
    columns = ['vehicle_id', 'datetime', 'date', 'time', 'hour', 'day_of_week', 'timestamp', 'image_path']
    df = df[columns]
    
    # Export to CSV
    df.to_csv(output_file, index=False)
    return output_file

def create_violation_gallery(violations_dir: str, output_html: str = 'violation_gallery.html') -> str:
    """
    Create HTML gallery of violation images
    
    Args:
        violations_dir: Directory containing violation images
        output_html: Output HTML file path
        
    Returns:
        str: Path to generated HTML file
    """
    if not os.path.exists(violations_dir):
        return ""
    
    violation_images = [f for f in os.listdir(violations_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    if not violation_images:
        return ""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Red Light Violation Gallery</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .header { text-align: center; color: #d32f2f; margin-bottom: 30px; }
            .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
            .violation-card { background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .violation-card img { width: 100%; height: 200px; object-fit: cover; border-radius: 5px; }
            .violation-info { margin-top: 10px; }
            .timestamp { color: #666; font-size: 0.9em; }
            .vehicle-id { font-weight: bold; color: #d32f2f; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚦 Red Light Violation Gallery</h1>
            <p>Total Violations: {count}</p>
        </div>
        <div class="gallery">
    """.format(count=len(violation_images))
    
    for img_file in sorted(violation_images):
        # Extract vehicle ID and timestamp from filename
        parts = img_file.replace('.jpg', '').replace('.png', '').split('_')
        vehicle_id = parts[1] if len(parts) > 1 else 'Unknown'
        timestamp = parts[2] if len(parts) > 2 else 'Unknown'
        
        img_path = os.path.join(violations_dir, img_file)
        html_content += f"""
            <div class="violation-card">
                <img src="{img_path}" alt="Violation {img_file}">
                <div class="violation-info">
                    <div class="vehicle-id">Vehicle ID: {vehicle_id}</div>
                    <div class="timestamp">Timestamp: {timestamp}</div>
                </div>
            </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open(output_html, 'w') as f:
        f.write(html_content)
    
    return output_html

def validate_video_file(video_path: str) -> Tuple[bool, str]:
    """
    Validate video file format and properties
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not os.path.exists(video_path):
        return False, "Video file does not exist"
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False, "Could not open video file"
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    
    if fps <= 0:
        return False, "Invalid FPS value"
    
    if frame_count <= 0:
        return False, "Invalid frame count"
    
    if width <= 0 or height <= 0:
        return False, "Invalid video dimensions"
    
    return True, f"Valid video: {width}x{height}, {fps:.1f} FPS, {frame_count} frames"

def get_system_info() -> Dict:
    """
    Get system information for performance monitoring
    
    Returns:
        Dict: System information
    """
    import platform
    import psutil
    
    info = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
        'opencv_version': cv2.__version__
    }
    
    return info
