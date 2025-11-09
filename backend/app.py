"""
Agricultural Analysis Backend
Connects Frontend → Backend → AI Service

Flask server that receives video uploads from the frontend,
forwards them to the AI service, and returns results.
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import requests
import time
from datetime import datetime
from phase_2_flight_path_generator import FlightPathGenerator
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend connection

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# AI Service configuration
AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:5001')

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if AI service is available
        ai_response = requests.get(f'{AI_SERVICE_URL}/health', timeout=5)
        ai_status = 'connected' if ai_response.status_code == 200 else 'disconnected'
    except:
        ai_status = 'disconnected'
    
    return jsonify({
        'status': 'healthy',
        'ai_service': ai_status,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """
    Main endpoint for video upload and analysis
    
    Expects:
        - video: File (required)
        - options: JSON string (optional)
        - metadata: JSON string (optional)
    
    Returns:
        AnalysisResponse JSON
    """
    logger.info("Received upload request")
    
    # Check if video file is present
    if 'video' not in request.files:
        logger.error("No video file in request")
        return jsonify({
            'status': 'error',
            'error_code': 'NO_FILE',
            'error_message': 'No video file provided'
        }), 400
    
    file = request.files['video']
    
    # Check if file has a name
    if file.filename == '':
        logger.error("Empty filename")
        return jsonify({
            'status': 'error',
            'error_code': 'EMPTY_FILENAME',
            'error_message': 'No file selected'
        }), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({
            'status': 'error',
            'error_code': 'INVALID_FILE_TYPE',
            'error_message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # Secure the filename and save
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        logger.info(f"Saving file to: {filepath}")
        file.save(filepath)
        
        # Get absolute path
        abs_filepath = os.path.abspath(filepath)
        
        # Parse options and metadata
        options = {}
        metadata = {}
        
        if 'options' in request.form:
            try:
                options = json.loads(request.form['options'])
                logger.info(f"Options: {options}")
            except json.JSONDecodeError:
                logger.warning("Failed to parse options JSON")
        
        if 'metadata' in request.form:
            try:
                metadata = json.loads(request.form['metadata'])
                logger.info(f"Metadata: {metadata}")
            except json.JSONDecodeError:
                logger.warning("Failed to parse metadata JSON")
        
        # Prepare request for AI service
        ai_request = {
            'request_type': 'video_analysis',
            'video_path': abs_filepath,
            'options': {
                'conf_threshold': options.get('conf_threshold', 0.25),
                'frame_skip': options.get('frame_skip', 1),
                'save_video': options.get('save_video', True),
                'save_json': options.get('save_json', True),
                'output_dir': os.path.abspath(app.config['OUTPUT_FOLDER'])
            },
            'metadata': metadata
        }
        
        logger.info(f"Sending request to AI service: {AI_SERVICE_URL}/analyze")
        
        # Send to AI service
        start_time = time.time()
        ai_response = requests.post(
            f'{AI_SERVICE_URL}/analyze',
            json=ai_request,
            timeout=600  # 10 minute timeout for processing
        )
        processing_time = time.time() - start_time
        
        if ai_response.status_code != 200:
            logger.error(f"AI service error: {ai_response.status_code}")
            return jsonify({
                'status': 'error',
                'error_code': 'AI_SERVICE_ERROR',
                'error_message': f'AI service returned error: {ai_response.status_code}',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        # Get results from AI service
        ai_results = ai_response.json()
        logger.info(f"AI service processing completed in {processing_time:.2f}s")
        
        # Format response for frontend
        response = {
            'status': 'success',
            'request_id': f"{timestamp}_{unique_filename}",
            'processing_time': processing_time,
            'results': ai_results.get('results', ai_results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
    
    except requests.RequestException as e:
        logger.error(f"AI service communication error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error_code': 'AI_SERVICE_UNAVAILABLE',
            'error_message': 'Unable to communicate with AI service',
            'timestamp': datetime.utcnow().isoformat()
        }), 503
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'INTERNAL_ERROR',
            'error_message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/status/<request_id>', methods=['GET'])
def check_status(request_id):
    """
    Check the status of an analysis request
    (For future async processing implementation)
    """
    return jsonify({
        'status': 'error',
        'error_code': 'NOT_IMPLEMENTED',
        'error_message': 'Async status checking not yet implemented'
    }), 501


@app.route('/outputs/<path:filename>', methods=['GET'])
def serve_output(filename):
    """Serve output files (videos, images, JSON)"""
    try:
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error_code': 'FILE_NOT_FOUND',
            'error_message': 'Output file not found'
        }), 404


@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    """Serve uploaded files"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error_code': 'FILE_NOT_FOUND',
            'error_message': 'Upload file not found'
        }), 404


@app.route('/api/generate-flight-path', methods=['POST'])
def generate_flight_path():
    """
    Generate flight path from field configuration (Phase 2)
    
    Expected JSON:
    {
        "field_config": {...},  # From Phase 1
        "altitude_m": 2.0,
        "overlap_pct": 0.3
    }
    
    Returns:
    {
        "success": true,
        "waypoints": [...],
        "total_waypoints": 45,
        "total_distance_m": 156.5,
        "estimated_battery_pct": 35,
        "estimated_duration_sec": 420,
        "coverage_area_sqm": 2000
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        field_config = data.get('field_config')
        altitude_m = data.get('altitude_m', 2.0)
        overlap_pct = data.get('overlap_pct', 0.3)
        
        if not field_config:
            return jsonify({'success': False, 'error': 'No field configuration provided'}), 400
        
        logger.info(f"Generating flight path: altitude={altitude_m}m, overlap={overlap_pct*100}%")
        
        # Generate flight path
        generator = FlightPathGenerator()
        mission = generator.generate_grid_pattern(
            field_config=field_config,
            altitude_m=altitude_m,
            overlap_pct=overlap_pct,
            optimize_for_battery=True
        )
        
        if not mission.get('success'):
            return jsonify(mission), 400
        
        logger.info(f"Flight path generated: {mission['total_waypoints']} waypoints, {mission['total_distance_m']}m")
        
        return jsonify(mission), 200
        
    except Exception as e:
        logger.error(f"Flight path generation error: {e}")
        return jsonify({
            'success': False,
            'error': f'Flight path generation failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Agricultural Analysis Backend Server")
    print("=" * 80)
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"📁 Output folder: {os.path.abspath(OUTPUT_FOLDER)}")
    print(f"🤖 AI Service URL: {AI_SERVICE_URL}")
    print(f"🌐 Backend running on: http://localhost:5000")
    print("=" * 80)
    print("\nWaiting for frontend video uploads...")
    print("Press CTRL+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)


