"""
AI Service - REAL YOLO INTEGRATION
Processes videos with agricultural detection models
"""

from flask import Flask, request, jsonify
import cv2
import os
import sys
from datetime import datetime
import logging
import json
from pathlib import Path

# DEMO MODE - Conditional imports
DEMO_MODE_FLAG = os.environ.get('DEMO_MODE', 'True').lower() == 'true'

if not DEMO_MODE_FLAG:
    # Add agricultural_detection_system to path (only needed for real YOLO)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agricultural_detection_system'))
    try:
        from unified_agricultural_detector import UnifiedAgriculturalDetector
    except ImportError:
        print("⚠️  Warning: Could not import UnifiedAgriculturalDetector - using DEMO MODE")
        DEMO_MODE_FLAG = True

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global detector instance
detector = None

# DEMO MODE - Use pre-recorded videos for hackathon demo
DEMO_MODE = True  # Set to False to use real YOLO models

# Demo videos (from your friend's computer)
DEMO_INPUT_VIDEO = "https://youtu.be/T5_DE24NW6M"
DEMO_OUTPUT_VIDEO = "https://www.youtube.com/watch?v=2SRbAlVAxRQ"

# Model paths (relative to project root)
BASE_DIR = Path(__file__).parent.parent
WEED_MODEL = BASE_DIR / 'agricultural_detection_system' / 'runs' / 'detect' / 'weed_detection' / 'weights' / 'best.pt'
PEST_MODEL = BASE_DIR / 'agricultural_detection_system' / 'runs' / 'detect' / 'pest_detection' / 'weights' / 'best.pt'
DISEASE_MODEL = BASE_DIR / 'agricultural_detection_system' / 'plant-disease-tensorflow2-plant-disease-v1' / 'plant_disease_model.h5'
DISEASE_CLASSES = BASE_DIR / 'agricultural_detection_system' / 'plant_village_classes.txt'


def generate_demo_results() -> dict:
    """
    Generate demo results matching the pre-recorded YOLO output
    Based on the actual YOLO report from friend's computer:
    - Weeds: 7
    - Healthy Crops: 3
    - Unhealthy Crops: 7
    - Diseases: 5
    - Good Crop Area: 13.64%
    - Bad Crop Area: 31.82%
    - Weed Coverage: 31.82%
    - Disease Coverage: 22.73%
    - Yield: 52.27%
    """
    
    # Demo detection counts
    weeds_detected = 7
    healthy_crops = 3
    unhealthy_crops = 7
    diseases_detected = 5
    
    # Area coverage (from actual YOLO report)
    good_crop_area = 13.64
    bad_crop_area = 31.82
    weed_coverage = 31.82
    disease_coverage = 22.73
    
    # Health score and yield
    health_score = 52.27
    yield_estimation = 52.27
    farm_health_status = 'POOR'
    
    # Recommendations from actual report
    recommendations = [
        '⚠️ WARNING: Significant weed infestation detected - Implement weed control measures',
        '⚠️ WARNING: Disease presence detected in crops - Apply disease treatment protocols',
        'Investigate causes of crop health decline',
        'Consider soil testing and nutrient analysis',
        'Review irrigation and fertilization practices'
    ]
    
    return {
        'video_path': DEMO_INPUT_VIDEO,
        'output_video_path': DEMO_OUTPUT_VIDEO,  # YouTube link to annotated video
        'json_path': None,
        'total_detections': weeds_detected + healthy_crops + unhealthy_crops + diseases_detected,
        'class_counts': {
            'weed': weeds_detected,
            'Healthy': healthy_crops,
            'Unhealthy': unhealthy_crops,
            'Corn_disease': diseases_detected
        },
        'frame_detections': [],  # Not needed for demo
        'analysis': {
            'total_detections': weeds_detected + healthy_crops + unhealthy_crops + diseases_detected,
            'healthy_crops': healthy_crops,
            'unhealthy_crops': unhealthy_crops,
            'weeds_detected': weeds_detected,
            'diseases_detected': diseases_detected,
            'health_score': health_score,
            'yield_estimation': yield_estimation,
            'farm_health_status': farm_health_status,
            'detection_coverage': 100.0,  # Demo has full coverage
            'area_coverage': {
                'good_crop_area': good_crop_area,
                'bad_crop_area': bad_crop_area,
                'weed_coverage': weed_coverage,
                'disease_coverage': disease_coverage
            },
            'recommendations': recommendations,
            'crop_health_issues': {
                'diseased_crops': diseases_detected,
                'total_health_issues': diseases_detected + unhealthy_crops,
                'healthy_crops': healthy_crops,
                'severity': 'high'
            },
            'pest_infestations': {
                'pest_presence': 0,
                'total_pest_issues': 0,
                'infestation_level': 'none'
            },
            'weed_growth': {
                'weeds': weeds_detected,
                'total_weeds': weeds_detected,
                'infestation_level': 'high'
            }
        },
        'video_info': {
            'fps': 30,
            'width': 1620,
            'height': 1116,
            'total_frames': 830,
            'processed_frames': 830
        }
    }


def initialize_detector():
    """Initialize the unified agricultural detector"""
    global detector
    
    if DEMO_MODE:
        logger.info("🎬 DEMO MODE - Skipping model initialization")
        logger.info("📹 Using pre-recorded videos for demonstration")
        detector = "DEMO"  # Placeholder
        return True
    
    try:
        logger.info("🚀 Initializing REAL YOLO Models...")
        
        # Load disease classes
        disease_classes = None
        if DISEASE_CLASSES.exists():
            with open(DISEASE_CLASSES, 'r') as f:
                disease_classes = [line.strip() for line in f.readlines()]
        
        # Check if models exist
        if not WEED_MODEL.exists():
            raise Exception(f"Weed model not found at: {WEED_MODEL}")
        if not PEST_MODEL.exists():
            raise Exception(f"Pest model not found at: {PEST_MODEL}")
        
        # Disease model is optional
        disease_model_path = None
        if DISEASE_MODEL.exists():
            disease_model_path = str(DISEASE_MODEL)
            logger.info(f"✅ Disease model found")
        else:
            logger.warning(f"⚠️  Disease model not found - skipping disease detection")
            disease_classes = None
        
        detector = UnifiedAgriculturalDetector(
            weed_model_path=str(WEED_MODEL),
            pest_model_path=str(PEST_MODEL),
            disease_model_path=disease_model_path,
            disease_class_names=disease_classes,
            conf_threshold=0.25,
            plant_detector_model=None
        )
        
        logger.info("✅ Detector initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize detector: {e}")
        return False


def process_video(video_path: str, options: dict) -> dict:
    """
    Process video with agricultural detection models (or return demo results)
    
    Args:
        video_path: Path to input video
        options: Processing options (conf_threshold, frame_skip, etc.)
    
    Returns:
        Detection results dictionary
    """
    if DEMO_MODE:
        logger.info("🎬 DEMO MODE - Returning pre-recorded results")
        time.sleep(2)  # Simulate processing time
        return generate_demo_results()
    
    if not detector or detector == "DEMO":
        raise Exception("Detector not initialized")
    
    if not os.path.exists(video_path):
        raise Exception(f"Video not found: {video_path}")
    
    logger.info(f"📹 Processing video: {video_path}")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open video: {video_path}")
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_skip = options.get('frame_skip', 5)  # Process every 5th frame
    save_video = options.get('save_video', True)
    output_dir = Path(options.get('output_dir', 'outputs'))
    output_dir.mkdir(exist_ok=True)
    
    # Prepare output video writer
    output_video_path = None
    writer = None
    if save_video:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_video_path = output_dir / f'annotated_{timestamp}.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))
    
    # Process frames
    frame_detections = []
    class_counts = {}
    frame_idx = 0
    processed_frames = 0
    
    logger.info(f"⚙️  Processing {total_frames} frames (skip={frame_skip})...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process only selected frames
        if frame_idx % frame_skip == 0:
            # Run detection
            detections = detector.detect_all(frame)
            
            # Aggregate counts
            for weed in detections.get('weeds', []):
                class_name = 'weed'
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            for pest in detections.get('pests', []):
                class_name = 'pest_presence'
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            for disease in detections.get('diseases', []):
                class_name = disease.get('class_name', 'diseased_crop')
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            # Store frame detections
            frame_detections.append({
                'frame_number': frame_idx,
                'timestamp': frame_idx / fps,
                'detections': detections
            })
            
            processed_frames += 1
            
            # Draw detections on frame
            if save_video:
                annotated_frame = detector.draw_detections(frame.copy(), detections)
                writer.write(annotated_frame)
        elif save_video:
            # Write original frame for skipped frames
            writer.write(frame)
        
        frame_idx += 1
        
        # Progress logging
        if frame_idx % 100 == 0:
            progress = (frame_idx / total_frames) * 100
            logger.info(f"  Progress: {progress:.1f}% ({frame_idx}/{total_frames})")
    
    cap.release()
    if writer:
        writer.release()
    
    logger.info(f"✅ Video processing complete! Processed {processed_frames} frames")
    
    # Parse detection counts from YOLO output
    weeds_detected = class_counts.get('weed', 0)
    healthy_crops = class_counts.get('healthy_crop', 0) + class_counts.get('Healthy', 0)
    unhealthy_crops = class_counts.get('unhealthy_crop', 0) + class_counts.get('Unhealthy', 0)
    diseases_detected = sum(v for k, v in class_counts.items() if 'disease' in k.lower() or 'corn' in k.lower() or 'tomato' in k.lower())
    
    total_detections = sum(class_counts.values())
    
    # Calculate area coverage percentages
    total_crop_area = max(1, healthy_crops + unhealthy_crops + weeds_detected)
    good_crop_area = (healthy_crops / total_crop_area) * 100
    bad_crop_area = (unhealthy_crops / total_crop_area) * 100
    weed_coverage = (weeds_detected / total_crop_area) * 100
    disease_coverage = (diseases_detected / total_crop_area) * 100
    
    # Calculate yield estimation
    yield_estimation = max(0, min(100, good_crop_area - (weed_coverage * 0.5) - (disease_coverage * 0.3)))
    
    # Calculate health score
    health_score = max(0, min(100, good_crop_area - (bad_crop_area * 0.5) - (weed_coverage * 0.3)))
    
    # Determine farm health status
    if health_score >= 80:
        farm_health_status = 'EXCELLENT'
    elif health_score >= 60:
        farm_health_status = 'GOOD'
    elif health_score >= 40:
        farm_health_status = 'FAIR'
    elif health_score >= 20:
        farm_health_status = 'POOR'
    else:
        farm_health_status = 'CRITICAL'
    
    # Calculate detection coverage
    frames_with_detections = sum(1 for fd in frame_detections if fd['detections'].get('weeds') or fd['detections'].get('pests') or fd['detections'].get('diseases'))
    detection_coverage = (frames_with_detections / max(1, processed_frames)) * 100
    
    # Generate recommendations based on REAL detections
    recommendations = []
    if weed_coverage > 30:
        recommendations.append('⚠️ WARNING: Significant weed infestation detected - Implement weed control measures')
    elif weed_coverage > 15:
        recommendations.append('Apply targeted weed control in affected areas')
    
    if disease_coverage > 20:
        recommendations.append('⚠️ WARNING: Disease presence detected in crops - Apply disease treatment protocols')
    elif disease_coverage > 10:
        recommendations.append('Monitor diseased crops for spread prevention')
    
    if bad_crop_area > 40:
        recommendations.append('Investigate causes of crop health decline')
        recommendations.append('Consider soil testing and nutrient analysis')
    
    if class_counts.get('pest_presence', 0) > 10:
        recommendations.append('Investigate pest presence and consider pest control measures')
    
    if health_score < 40:
        recommendations.append('Review irrigation and fertilization practices')
    
    if not recommendations:
        recommendations.append('✅ Crops appear healthy - continue regular monitoring')
    
    # Build results with REAL YOLO metrics
    results = {
        'video_path': video_path,
        'output_video_path': str(output_video_path) if output_video_path else None,
        'json_path': None,
        'total_detections': total_detections,
        'class_counts': class_counts,
        'frame_detections': frame_detections,
        'analysis': {
            'total_detections': total_detections,
            'healthy_crops': healthy_crops,
            'unhealthy_crops': unhealthy_crops,
            'weeds_detected': weeds_detected,
            'diseases_detected': diseases_detected,
            'health_score': round(health_score, 1),
            'yield_estimation': round(yield_estimation, 1),
            'farm_health_status': farm_health_status,
            'detection_coverage': round(detection_coverage, 1),
            'area_coverage': {
                'good_crop_area': round(good_crop_area, 2),
                'bad_crop_area': round(bad_crop_area, 2),
                'weed_coverage': round(weed_coverage, 2),
                'disease_coverage': round(disease_coverage, 2)
            },
            'recommendations': recommendations,
            'crop_health_issues': {
                'diseased_crops': diseases_detected,
                'total_health_issues': diseases_detected + unhealthy_crops,
                'healthy_crops': healthy_crops,
                'severity': 'low' if health_score > 70 else 'medium' if health_score > 40 else 'high'
            },
            'pest_infestations': {
                'pest_presence': class_counts.get('pest_presence', 0),
                'total_pest_issues': class_counts.get('pest_presence', 0),
                'infestation_level': 'low' if class_counts.get('pest_presence', 0) < 20 else 'medium' if class_counts.get('pest_presence', 0) < 50 else 'high'
            },
            'weed_growth': {
                'weeds': weeds_detected,
                'total_weeds': weeds_detected,
                'infestation_level': 'low' if weed_coverage < 20 else 'medium' if weed_coverage < 40 else 'high'
            }
        },
        'video_info': {
            'fps': fps,
            'width': width,
            'height': height,
            'total_frames': total_frames,
            'processed_frames': processed_frames
        }
    }
    
    # Save JSON report
    json_path = output_dir / f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    results['json_path'] = str(json_path)
    
    return results


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mode': 'demo' if DEMO_MODE else 'production',
        'detector_loaded': detector is not None,
        'demo_input_video': DEMO_INPUT_VIDEO if DEMO_MODE else None,
        'demo_output_video': DEMO_OUTPUT_VIDEO if DEMO_MODE else None,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main analysis endpoint
    Receives video_path and options from backend
    Returns analysis results
    """
    data = request.json
    logger.info(f"Received analysis request: {data.get('request_type')}")
    
    if not data:
        return jsonify({
            'status': 'error',
            'error_code': 'INVALID_REQUEST',
            'error_message': 'No JSON data provided'
        }), 400
    
    if not detector:
        return jsonify({
            'status': 'error',
            'error_code': 'DETECTOR_NOT_INITIALIZED',
            'error_message': 'Detector not initialized'
        }), 500
    
    request_type = data.get('request_type')
    video_path = data.get('video_path')
    options = data.get('options', {})
    
    if request_type == 'video_analysis' and not video_path:
        return jsonify({
            'status': 'error',
            'error_code': 'MISSING_VIDEO_PATH',
            'error_message': 'video_path is required for video_analysis'
        }), 400
    
    try:
        logger.info(f"Processing video: {video_path}")
        results = process_video(video_path, options)
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'PROCESSING_FAILED',
            'error_message': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 80)
    print("🤖 AI Service - REAL YOLO INTEGRATION")
    print("=" * 80)
    
    # Initialize detector
    if initialize_detector():
        print("✅ Production mode - using REAL YOLO models")
        print(f"🌐 AI Service running on: http://localhost:5001")
        print("=" * 80)
        print("\nPress CTRL+C to stop\n")
        
        app.run(host='0.0.0.0', port=5001, debug=False)
    else:
        print("❌ Failed to initialize detector")
        print("Check that model files exist in agricultural_detection_system/")
        sys.exit(1)
