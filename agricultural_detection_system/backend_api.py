"""
Backend API for Farm Health Report Generation
Phase 4: Backend Processing
- AI analysis (YOLO)
- Detect: pests, diseases, water stress, weeds
- Generate detailed farm health report
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import base64
from io import BytesIO
from PIL import Image

from unified_agricultural_detector import UnifiedAgriculturalDetector

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Global detector instance
detector = None


def initialize_detector(weed_model: str, pest_model: str, disease_model: str, 
                        disease_classes: List[str] = None, plant_detector: str = None):
    """Initialize the unified detector"""
    global detector
    detector = UnifiedAgriculturalDetector(
        weed_model_path=weed_model,
        pest_model_path=pest_model,
        disease_model_path=disease_model,
        disease_class_names=disease_classes,
        conf_threshold=0.25,
        plant_detector_model=plant_detector
    )
    print("✅ Detector initialized")


def generate_farm_health_report(detections: Dict, image_path: str = None) -> Dict:
    """
    Generate comprehensive farm health report from detections
    
    Args:
        detections: Detection results dictionary
        image_path: Optional path to analyzed image
        
    Returns:
        Detailed farm health report
    """
    # Analyze detections
    weed_count = len(detections.get('weeds', []))
    pest_count = len(detections.get('pests', []))
    disease_count = len(detections.get('diseases', []))
    
    # Calculate severity levels
    weed_severity = 'none'
    if weed_count > 15:
        weed_severity = 'high'
    elif weed_count > 8:
        weed_severity = 'medium'
    elif weed_count > 0:
        weed_severity = 'low'
    
    pest_severity = 'none'
    if pest_count > 10:
        pest_severity = 'high'
    elif pest_count > 5:
        pest_severity = 'medium'
    elif pest_count > 0:
        pest_severity = 'low'
    
    disease_severity = 'none'
    disease_labels = []
    if disease_count > 0:
        for disease in detections.get('diseases', []):
            disease_labels.append({
                'name': disease.get('label', 'Unknown'),
                'confidence': disease.get('confidence', 0.0)
            })
        # Check if any disease has high confidence
        max_disease_conf = max([d.get('confidence', 0.0) for d in disease_labels]) if disease_labels else 0.0
        if max_disease_conf > 0.7:
            disease_severity = 'high'
        elif max_disease_conf > 0.5:
            disease_severity = 'medium'
        else:
            disease_severity = 'low'
    
    # Calculate overall health score (0-100)
    health_score = 100
    if weed_severity == 'high':
        health_score -= 30
    elif weed_severity == 'medium':
        health_score -= 15
    elif weed_severity == 'low':
        health_score -= 5
    
    if pest_severity == 'high':
        health_score -= 30
    elif pest_severity == 'medium':
        health_score -= 15
    elif pest_severity == 'low':
        health_score -= 5
    
    if disease_severity == 'high':
        health_score -= 30
    elif disease_severity == 'medium':
        health_score -= 15
    elif disease_severity == 'low':
        health_score -= 5
    
    health_score = max(0, health_score)
    
    # Generate recommendations
    recommendations = []
    
    if weed_severity == 'high':
        recommendations.append({
            'priority': 'high',
            'category': 'weed_control',
            'action': 'Immediate weed control required. Consider mechanical or chemical weed management.',
            'urgency': 'urgent'
        })
    elif weed_severity == 'medium':
        recommendations.append({
            'priority': 'medium',
            'category': 'weed_control',
            'action': 'Moderate weed growth detected. Plan weed control measures.',
            'urgency': 'moderate'
        })
    
    if pest_severity == 'high':
        recommendations.append({
            'priority': 'high',
            'category': 'pest_control',
            'action': 'Severe pest infestation detected. Immediate pest control required.',
            'urgency': 'urgent'
        })
    elif pest_severity == 'medium':
        recommendations.append({
            'priority': 'medium',
            'category': 'pest_control',
            'action': 'Moderate pest activity detected. Monitor closely and consider treatment.',
            'urgency': 'moderate'
        })
    
    if disease_severity == 'high':
        recommendations.append({
            'priority': 'high',
            'category': 'disease_management',
            'action': 'Disease detected with high confidence. Apply appropriate treatment immediately.',
            'urgency': 'urgent'
        })
    elif disease_severity == 'medium':
        recommendations.append({
            'priority': 'medium',
            'category': 'disease_management',
            'action': 'Possible disease detected. Monitor and consider preventive treatment.',
            'urgency': 'moderate'
        })
    
    if health_score > 80:
        recommendations.append({
            'priority': 'low',
            'category': 'maintenance',
            'action': 'Field condition is good. Maintain current practices.',
            'urgency': 'low'
        })
    
    # Build report
    report = {
        'timestamp': datetime.now().isoformat(),
        'image_path': image_path,
        'overall_health_score': health_score,
        'health_status': 'good' if health_score > 70 else 'fair' if health_score > 50 else 'poor',
        
        'detections': {
            'weeds': {
                'count': weed_count,
                'severity': weed_severity,
                'detections': detections.get('weeds', [])
            },
            'pests': {
                'count': pest_count,
                'severity': pest_severity,
                'detections': detections.get('pests', [])
            },
            'diseases': {
                'count': disease_count,
                'severity': disease_severity,
                'detections': disease_labels
            },
            'water_stress': {
                'count': len(detections.get('water_stress', [])),
                'severity': 'none',  # Can be enhanced
                'detections': detections.get('water_stress', [])
            }
        },
        
        'recommendations': recommendations,
        
        'summary': {
            'total_issues': weed_count + pest_count + disease_count,
            'critical_issues': len([r for r in recommendations if r['priority'] == 'high']),
            'moderate_issues': len([r for r in recommendations if r['priority'] == 'medium']),
            'action_required': len([r for r in recommendations if r['urgency'] == 'urgent'])
        }
    }
    
    return report


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'detector_loaded': detector is not None
    })


@app.route('/analyze/image', methods=['POST'])
def analyze_image():
    """
    Analyze an image and generate farm health report
    
    Request:
        - image: Base64 encoded image or image file
        - OR image_path: Path to image file on server
    
    Response:
        - Farm health report with detections and recommendations
    """
    if detector is None:
        return jsonify({'error': 'Detector not initialized'}), 500
    
    try:
        # Handle image upload
        if 'image' in request.files:
            # File upload
            file = request.files['image']
            image_bytes = file.read()
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif 'image' in request.json:
            # Base64 encoded image
            image_data = request.json['image']
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif 'image_path' in request.json:
            # Path to image file
            image_path = request.json['image_path']
            image = cv2.imread(image_path)
            if image is None:
                return jsonify({'error': f'Could not load image: {image_path}'}), 400
        else:
            return jsonify({'error': 'No image provided'}), 400
        
        # Run detections
        detections = detector.detect_all(image)
        
        # Generate report
        report = generate_farm_health_report(detections)
        
        # Optionally save annotated image
        if 'save_annotated' in request.json and request.json['save_annotated']:
            annotated = detector.draw_detections(image, detections)
            output_path = f"outputs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            os.makedirs('outputs', exist_ok=True)
            cv2.imwrite(output_path, annotated)
            report['annotated_image_path'] = output_path
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    """
    Analyze multiple images and generate combined report
    
    Request:
        - images: List of image paths or base64 encoded images
    
    Response:
        - Combined farm health report
    """
    if detector is None:
        return jsonify({'error': 'Detector not initialized'}), 500
    
    try:
        data = request.json
        image_paths = data.get('images', [])
        
        all_detections = {
            'weeds': [],
            'pests': [],
            'diseases': [],
            'water_stress': []
        }
        
        for img_path in image_paths:
            image = cv2.imread(img_path)
            if image is not None:
                detections = detector.detect_all(image)
                all_detections['weeds'].extend(detections.get('weeds', []))
                all_detections['pests'].extend(detections.get('pests', []))
                all_detections['diseases'].extend(detections.get('diseases', []))
                all_detections['water_stress'].extend(detections.get('water_stress', []))
        
        # Generate combined report
        report = generate_farm_health_report(all_detections)
        report['images_analyzed'] = len(image_paths)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/report/generate', methods=['POST'])
def generate_report():
    """
    Generate detailed farm health report from detection data
    
    Request:
        - detections: Detection results dictionary
    
    Response:
        - Detailed farm health report
    """
    try:
        data = request.json
        detections = data.get('detections', {})
        
        report = generate_farm_health_report(detections)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Farm Health Backend API')
    parser.add_argument('--weed-model', type=str, required=True,
                       help='Path to weed detection YOLO model')
    parser.add_argument('--pest-model', type=str, required=True,
                       help='Path to pest detection YOLO model')
    parser.add_argument('--disease-model', type=str, required=True,
                       help='Path to disease classification TensorFlow model')
    parser.add_argument('--classes', type=str, default='plant_village_classes.txt',
                       help='Path to disease class names file (default: plant_village_classes.txt)')
    parser.add_argument('--plant-detector', type=str, default=None,
                       help='Path to plant detection YOLO model (if None, uses pest model)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    
    args = parser.parse_args()
    
    # Load class names if provided
    disease_classes = None
    if args.classes and os.path.isfile(args.classes):
        with open(args.classes, 'r') as f:
            disease_classes = [line.strip() for line in f.readlines()]
    
    # Initialize detector
    print("🚀 Initializing Backend API...")
    initialize_detector(
        weed_model=args.weed_model,
        pest_model=args.pest_model,
        disease_model=args.disease_model,
        disease_classes=disease_classes,
        plant_detector=args.plant_detector
    )
    
    print(f"🌐 Starting API server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)

