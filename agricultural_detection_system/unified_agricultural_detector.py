"""
Unified Real-Time Agricultural Detection System
Combines:
1. Weed Detection (YOLO)
2. Pest Detection (YOLO)
3. Disease Classification (TensorFlow)
4. Water Stress Detection (from YOLO)

Real-time processing for drone video streams
"""

import cv2
import numpy as np
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
from datetime import datetime

from ultralytics import YOLO
from plant_disease_classifier import PlantDiseaseClassifier


class UnifiedAgriculturalDetector:
    """Unified system for real-time agricultural monitoring"""
    
    def __init__(self,
                 weed_model_path: str,
                 pest_model_path: str,
                 disease_model_path: str,
                 disease_class_names: Optional[List[str]] = None,
                 conf_threshold: float = 0.25,
                 plant_detector_model: Optional[str] = None):
        """
        Initialize unified agricultural detector
        
        Args:
            weed_model_path: Path to weed detection YOLO model
            pest_model_path: Path to pest detection YOLO model
            disease_model_path: Path to disease classification TensorFlow model
            disease_class_names: List of disease class names
            conf_threshold: Confidence threshold for detections
            plant_detector_model: Path to plant detection YOLO model (if None, uses pest model to detect plants)
        """
        print("🚁 Initializing Unified Agricultural Detection System...")
        
        # Load models
        print("  📥 Loading weed detection model...")
        self.weed_model = YOLO(weed_model_path)
        
        print("  📥 Loading pest detection model...")
        self.pest_model = YOLO(pest_model_path)
        
        # Plant detector for disease classification (detects individual plants/leaves)
        if plant_detector_model:
            print("  📥 Loading plant detection model...")
            self.plant_detector = YOLO(plant_detector_model)
        else:
            # Use pest model as plant detector (it can detect plants/crops)
            print("  📥 Using pest model for plant detection...")
            self.plant_detector = self.pest_model
        
        # Disease classifier is optional
        if disease_model_path and os.path.exists(disease_model_path):
            print("  📥 Loading disease classification model...")
            self.disease_classifier = PlantDiseaseClassifier(
                disease_model_path,
                class_names=disease_class_names
            )
        else:
            print("  ⚠️  Disease model not available - skipping disease classification")
            self.disease_classifier = None
        
        self.conf_threshold = conf_threshold
        
        # Detection colors
        self.colors = {
            'weed': (255, 20, 147),      # Deep pink
            'pest': (255, 165, 0),        # Orange
            'disease': (255, 0, 0),       # Red
            'water_stress': (139, 69, 19), # Brown
            'healthy': (0, 255, 0)        # Green
        }
        
        print("✅ All models loaded successfully!")
    
    def detect_all(self, image: np.ndarray) -> Dict:
        """
        Run all detection models on a single image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with all detections
        """
        # Save temporary image for disease classifier
        temp_path = "temp_detection.jpg"
        cv2.imwrite(temp_path, image)
        
        results = {
            'weeds': [],
            'pests': [],
            'diseases': [],
            'water_stress': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Weed Detection
        weed_results = self.weed_model.predict(
            source=image,
            conf=self.conf_threshold,
            verbose=False
        )
        if weed_results[0].boxes is not None:
            for box in weed_results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                conf = float(box.conf[0].cpu().numpy())
                results['weeds'].append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': conf
                })
        
        # 2. Pest Detection
        pest_results = self.pest_model.predict(
            source=image,
            conf=self.conf_threshold,
            verbose=False
        )
        if pest_results[0].boxes is not None:
            for box in pest_results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                results['pests'].append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': conf,
                    'class_id': cls_id
                })
        
        # 3. Disease Classification (on individual detected plants/leaves)
        # First detect plants, then classify each one
        if self.disease_classifier:
            try:
                # Detect plants/leaves in the image
                plant_results = self.plant_detector.predict(
                    source=image,
                    conf=self.conf_threshold * 0.5,  # Lower threshold for plant detection
                    verbose=False
                )
                
                if plant_results[0].boxes is not None and len(plant_results[0].boxes) > 0:
                    # Classify each detected plant
                    h, w = image.shape[:2]
                    temp_dir = "temp_plant_crops"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    for idx, box in enumerate(plant_results[0].boxes):
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        
                        # Add padding around the detected plant
                        padding = 10
                        x1 = max(0, x1 - padding)
                        y1 = max(0, y1 - padding)
                        x2 = min(w, x2 + padding)
                        y2 = min(h, y2 + padding)
                        
                        # Crop the plant region
                        plant_crop = image[y1:y2, x1:x2]
                        
                        if plant_crop.size == 0:
                            continue
                        
                        # Save crop temporarily
                        crop_path = os.path.join(temp_dir, f"plant_{idx}.jpg")
                        cv2.imwrite(crop_path, plant_crop)
                        
                        try:
                            # Classify the disease for this plant
                            disease_label, disease_conf = self.disease_classifier.predict(crop_path)
                            
                            results['diseases'].append({
                                'label': disease_label,
                                'confidence': disease_conf,
                                'bbox': [x1, y1, x2, y2],
                                'plant_id': idx
                            })
                        except Exception as e:
                            print(f"⚠️  Disease classification error for plant {idx}: {e}")
                        finally:
                            # Clean up crop file
                            if os.path.exists(crop_path):
                                os.remove(crop_path)
                    
                    # Clean up temp directory
                    try:
                        os.rmdir(temp_dir)
                    except:
                        pass
                else:
                    # If no plants detected, try classifying the whole image
                    print("⚠️  No plants detected, classifying whole image...")
                    disease_label, disease_conf = self.disease_classifier.predict(temp_path)
                    results['diseases'].append({
                        'label': disease_label,
                        'confidence': disease_conf,
                        'bbox': [0, 0, image.shape[1], image.shape[0]]
                    })
                    
            except Exception as e:
                print(f"⚠️  Disease classification error: {e}")
                import traceback
                traceback.print_exc()
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return results
    
    def draw_detections(self, image: np.ndarray, detections: Dict) -> np.ndarray:
        """
        Draw all detections on image
        
        Args:
            image: Input image
            detections: Detection results dictionary
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        # Draw weeds
        for weed in detections['weeds']:
            x1, y1, x2, y2 = weed['bbox']
            conf = weed['confidence']
            cv2.rectangle(annotated, (x1, y1), (x2, y2), self.colors['weed'], 2)
            label = f"Weed: {conf:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['weed'], 2)
        
        # Draw pests
        for pest in detections['pests']:
            x1, y1, x2, y2 = pest['bbox']
            conf = pest['confidence']
            cv2.rectangle(annotated, (x1, y1), (x2, y2), self.colors['pest'], 2)
            label = f"Pest: {conf:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['pest'], 2)
        
        # Draw diseases (on individual plants)
        for disease in detections['diseases']:
            x1, y1, x2, y2 = disease['bbox']
            label_text = disease['label']
            conf = disease['confidence']
            plant_id = disease.get('plant_id', '')
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), self.colors['disease'], 2)
            
            # Format label (shorten if too long)
            if len(label_text) > 30:
                label_text = label_text[:27] + "..."
            
            # Add plant ID if available
            if plant_id != '':
                label = f"Plant #{plant_id}: {label_text}"
            else:
                label = f"{label_text}"
            
            label_with_conf = f"{label} ({conf:.2f})"
            
            # Draw label with background
            (text_width, text_height), baseline = cv2.getTextSize(
                label_with_conf, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            cv2.rectangle(annotated, (x1, y1 - text_height - 10), 
                         (x1 + text_width, y1), self.colors['disease'], -1)
            cv2.putText(annotated, label_with_conf, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated
    
    def process_live_video(self,
                           source: int = 0,
                           show_display: bool = True,
                           save_video: bool = False,
                           output_path: str = "live_output.mp4",
                           save_json: bool = True,
                           json_interval: int = 30) -> None:
        """
        Process live video stream in real-time
        
        Args:
            source: Video source (0 for webcam, or path/URL for RTSP/HTTP stream)
            show_display: Whether to show live video window
            save_video: Whether to save the annotated video
            output_path: Path to save video (if save_video=True)
            save_json: Whether to save detections as JSON
            json_interval: Save JSON every N frames
        """
        # Open video source
        if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
            source = int(source)
            print(f"📹 Opening webcam/camera {source}...")
        else:
            print(f"📹 Opening video source: {source}")
        
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video source: {source}")
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        
        print(f"✅ Video stream opened: {width}x{height} @ {fps} FPS")
        print("Press 'q' to quit, 's' to save screenshot")
        
        # Setup video writer if saving
        video_writer = None
        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            print(f"💾 Recording to: {output_path}")
        
        # FPS tracking
        frame_count = 0
        fps_counter = 0
        fps_start_time = time.time()
        current_fps = 0
        
        # Detection storage
        all_detections = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️  Failed to read frame. Retrying...")
                    continue
                
                # Run all detections
                detections = self.detect_all(frame)
                
                # Draw detections
                annotated_frame = self.draw_detections(frame, detections)
                
                # Calculate FPS
                fps_counter += 1
                if fps_counter % 30 == 0:
                    fps_end_time = time.time()
                    current_fps = 30 / (fps_end_time - fps_start_time)
                    fps_start_time = fps_end_time
                
                # Draw FPS and detection counts
                info_text = [
                    f"FPS: {current_fps:.1f}",
                    f"Weeds: {len(detections['weeds'])}",
                    f"Pests: {len(detections['pests'])}",
                    f"Diseases: {len(detections['diseases'])}"
                ]
                
                y_offset = 30
                for text in info_text:
                    cv2.putText(annotated_frame, text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    y_offset += 30
                
                # Save frame if recording
                if video_writer:
                    video_writer.write(annotated_frame)
                
                # Store detections
                if frame_count % json_interval == 0:
                    all_detections.append({
                        'frame': frame_count,
                        'timestamp': detections['timestamp'],
                        'detections': detections
                    })
                
                # Display frame
                if show_display:
                    cv2.imshow("Unified Agricultural Detection", annotated_frame)
                    
                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n🛑 Stopping live video processing...")
                        break
                    elif key == ord('s'):
                        screenshot_path = f"screenshot_{frame_count}.jpg"
                        cv2.imwrite(screenshot_path, annotated_frame)
                        print(f"📸 Screenshot saved: {screenshot_path}")
                
                frame_count += 1
                
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        finally:
            cap.release()
            if video_writer:
                video_writer.release()
                print(f"💾 Video saved to: {output_path}")
            if show_display:
                cv2.destroyAllWindows()
            
            # Save JSON if requested
            if save_json and all_detections:
                json_path = f"detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_path, 'w') as f:
                    json.dump({
                        'total_frames': frame_count,
                        'detections': all_detections
                    }, f, indent=2)
                print(f"📄 Detections saved to: {json_path}")
            
            print(f"✅ Processed {frame_count} frames")
    
    def process_image(self,
                     image_path: str,
                     output_path: Optional[str] = None) -> Dict:
        """
        Process a single image
        
        Args:
            image_path: Path to input image
            output_path: Path to save annotated image
            
        Returns:
            Detection results dictionary
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Run detections
        detections = self.detect_all(image)
        
        # Draw detections
        annotated = self.draw_detections(image, detections)
        
        # Save if requested
        if output_path is None:
            base_name = Path(image_path).stem
            output_path = f"{base_name}_detected.jpg"
        
        cv2.imwrite(output_path, annotated)
        print(f"✅ Saved annotated image to: {output_path}")
        
        return {
            'detections': detections,
            'annotated_image_path': output_path
        }
    
    def calculate_area_coverage(self, detections: Dict, frame_shape: Tuple[int, int]) -> Dict:
        """
        Calculate pixel area coverage for good crop, bad crop, and weeds
        
        Args:
            detections: Detection results dictionary
            frame_shape: Tuple of (height, width) of the frame
            
        Returns:
            Dictionary with area coverage statistics
        """
        height, width = frame_shape[:2]
        total_pixels = height * width
        
        # Create masks for each category
        good_crop_mask = np.zeros((height, width), dtype=np.uint8)
        bad_crop_mask = np.zeros((height, width), dtype=np.uint8)
        weed_mask = np.zeros((height, width), dtype=np.uint8)
        
        # Fill masks based on bounding boxes
        for disease in detections['diseases']:
            x1, y1, x2, y2 = disease['bbox']
            label = disease['label'].lower()
            
            # Check if healthy or diseased
            if 'healthy' in label:
                good_crop_mask[y1:y2, x1:x2] = 255
            else:
                bad_crop_mask[y1:y2, x1:x2] = 255
        
        for weed in detections['weeds']:
            x1, y1, x2, y2 = weed['bbox']
            weed_mask[y1:y2, x1:x2] = 255
        
        # Calculate pixel counts
        good_pixels = np.sum(good_crop_mask > 0)
        bad_pixels = np.sum(bad_crop_mask > 0)
        weed_pixels = np.sum(weed_mask > 0)
        
        # Calculate percentages
        good_percentage = (good_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        bad_percentage = (bad_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        weed_percentage = (weed_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        # Remaining area (unclassified/background)
        remaining_pixels = total_pixels - (good_pixels + bad_pixels + weed_pixels)
        remaining_percentage = (remaining_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        return {
            'total_pixels': int(total_pixels),
            'good_crop_pixels': int(good_pixels),
            'bad_crop_pixels': int(bad_pixels),
            'weed_pixels': int(weed_pixels),
            'remaining_pixels': int(remaining_pixels),
            'good_crop_percentage': float(good_percentage),
            'bad_crop_percentage': float(bad_percentage),
            'weed_percentage': float(weed_percentage),
            'remaining_percentage': float(remaining_percentage)
        }
    
    def estimate_yield(self, area_stats: Dict, detections: Dict, 
                      base_yield_per_acre: float = 150.0) -> Dict:
        """
        Estimate crop yield based on area coverage and health status
        
        Args:
            area_stats: Area coverage statistics from calculate_area_coverage
            detections: Detection results dictionary
            base_yield_per_acre: Base yield expectation in bushels/acre (default: 150)
            
        Returns:
            Dictionary with yield estimation
        """
        # Calculate health factor based on good vs bad crop ratio
        total_crop_area = area_stats['good_crop_percentage'] + area_stats['bad_crop_percentage']
        
        if total_crop_area > 0:
            health_factor = area_stats['good_crop_percentage'] / total_crop_area
        else:
            health_factor = 0.0
        
        # Weed impact factor (weeds reduce yield)
        weed_impact = max(0.0, 1.0 - (area_stats['weed_percentage'] / 100.0) * 0.3)  # Up to 30% reduction
        
        # Pest impact (each pest reduces yield slightly)
        pest_count = len(detections['pests'])
        pest_impact = max(0.0, 1.0 - (pest_count * 0.01))  # 1% reduction per pest, max 50%
        pest_impact = min(0.5, pest_impact)  # Cap at 50% reduction
        
        # Disease severity impact
        disease_count = len([d for d in detections['diseases'] if 'healthy' not in d['label'].lower()])
        disease_impact = max(0.0, 1.0 - (disease_count * 0.02))  # 2% reduction per diseased plant
        disease_impact = min(0.4, disease_impact)  # Cap at 40% reduction
        
        # Combined yield factor
        yield_factor = health_factor * weed_impact * pest_impact * disease_impact
        
        # Estimated yield
        estimated_yield = base_yield_per_acre * yield_factor
        
        # Yield percentage (relative to base)
        yield_percentage = (estimated_yield / base_yield_per_acre) * 100
        
        return {
            'base_yield_per_acre': float(base_yield_per_acre),
            'estimated_yield_per_acre': float(estimated_yield),
            'yield_percentage': float(yield_percentage),
            'health_factor': float(health_factor),
            'weed_impact': float(weed_impact),
            'pest_impact': float(pest_impact),
            'disease_impact': float(disease_impact),
            'overall_yield_factor': float(yield_factor)
        }
    
    def get_curated_images(self, all_frame_data: List[Dict], top_n: int = 5) -> Dict:
        """
        Select best/worst frames for curated display
        
        Args:
            all_frame_data: List of dictionaries with 'frame', 'detections', 'area_stats', 'frame_image'
            top_n: Number of top frames to select for each category
            
        Returns:
            Dictionary with curated frame indices and data
        """
        if not all_frame_data:
            return {
                'worst_infected': [],
                'most_weeds': [],
                'healthiest': []
            }
        
        # Sort frames by severity metrics
        worst_infected = sorted(
            all_frame_data,
            key=lambda x: (
                len([d for d in x['detections']['diseases'] if 'healthy' not in d.get('label', '').lower()]),
                -x.get('area_stats', {}).get('good_crop_percentage', 0)
            ),
            reverse=True
        )[:top_n]
        
        most_weeds = sorted(
            all_frame_data,
            key=lambda x: (
                len(x['detections']['weeds']),
                x.get('area_stats', {}).get('weed_percentage', 0)
            ),
            reverse=True
        )[:top_n]
        
        healthiest = sorted(
            all_frame_data,
            key=lambda x: (
                x.get('area_stats', {}).get('good_crop_percentage', 0),
                -len([d for d in x['detections']['diseases'] if 'healthy' not in d.get('label', '').lower()]),
                -len(x['detections']['weeds'])
            ),
            reverse=True
        )[:top_n]
        
        return {
            'worst_infected': worst_infected,
            'most_weeds': most_weeds,
            'healthiest': healthiest
        }
    
    def process_video_file(self,
                          video_path: str,
                          output_dir: str = "drone_analysis",
                          frame_skip: int = 1,
                          save_annotated_video: bool = True,
                          save_curated_images: bool = True) -> Dict:
        """
        Process drone video file with complete analysis
        
        Args:
            video_path: Path to input video file
            output_dir: Directory to save all outputs
            frame_skip: Process every Nth frame (1 = all frames)
            save_annotated_video: Whether to save annotated video
            save_curated_images: Whether to save curated images
            
        Returns:
            Dictionary with complete analysis results
        """
        os.makedirs(output_dir, exist_ok=True)
        base_name = Path(video_path).stem
        
        print(f"🚁 Processing drone video: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"📹 Video: {width}x{height} @ {fps} FPS, {total_frames} frames")
        
        # Setup video writer
        video_writer = None
        if save_annotated_video:
            output_video_path = os.path.join(output_dir, f"{base_name}_annotated.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
            print(f"💾 Saving annotated video to: {output_video_path}")
        
        # Process frames
        all_frame_data = []
        frame_count = 0
        processed_frames = 0
        
        # Accumulate statistics
        total_good_area = 0.0
        total_bad_area = 0.0
        total_weed_area = 0.0
        total_yield = 0.0
        
        print("\n🔄 Processing frames...")
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames if needed
            if frame_count % frame_skip != 0:
                frame_count += 1
                continue
            
            # Run all detections
            detections = self.detect_all(frame)
            
            # Calculate area coverage
            area_stats = self.calculate_area_coverage(detections, (height, width))
            
            # Estimate yield for this frame
            yield_stats = self.estimate_yield(area_stats, detections)
            
            # Accumulate statistics
            total_good_area += area_stats['good_crop_percentage']
            total_bad_area += area_stats['bad_crop_percentage']
            total_weed_area += area_stats['weed_percentage']
            total_yield += yield_stats['estimated_yield_per_acre']
            
            # Draw detections on frame
            annotated_frame = self.draw_detections(frame, detections)
            
            # Add statistics overlay
            stats_text = [
                f"Frame: {frame_count}/{total_frames}",
                f"Good Crop: {area_stats['good_crop_percentage']:.1f}%",
                f"Bad Crop: {area_stats['bad_crop_percentage']:.1f}%",
                f"Weeds: {area_stats['weed_percentage']:.1f}%",
                f"Est. Yield: {yield_stats['yield_percentage']:.1f}%"
            ]
            
            y_offset = 30
            for text in stats_text:
                cv2.putText(annotated_frame, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 25
            
            # Save annotated frame to video
            if video_writer:
                video_writer.write(annotated_frame)
            
            # Store frame data for curation
            all_frame_data.append({
                'frame_number': frame_count,
                'frame': frame.copy(),
                'annotated_frame': annotated_frame.copy(),
                'detections': detections,
                'area_stats': area_stats,
                'yield_stats': yield_stats
            })
            
            processed_frames += 1
            
            # Progress update
            if processed_frames % 30 == 0:
                elapsed = time.time() - start_time
                fps_actual = processed_frames / elapsed
                remaining = (total_frames - frame_count) / (fps_actual * frame_skip) if fps_actual > 0 else 0
                print(f"  Processed {processed_frames} frames ({processed_frames * 100 / (total_frames // frame_skip):.1f}%) - "
                      f"ETA: {remaining:.1f}s")
            
            frame_count += 1
        
        cap.release()
        if video_writer:
            video_writer.release()
            print(f"✅ Annotated video saved")
        
        # Calculate averages
        avg_good = total_good_area / processed_frames if processed_frames > 0 else 0
        avg_bad = total_bad_area / processed_frames if processed_frames > 0 else 0
        avg_weed = total_weed_area / processed_frames if processed_frames > 0 else 0
        avg_yield = total_yield / processed_frames if processed_frames > 0 else 0
        
        # Get curated images
        print("\n📸 Selecting curated images...")
        curated = self.get_curated_images(all_frame_data, top_n=5)
        
        # Save curated images
        curated_dir = os.path.join(output_dir, "curated_images")
        os.makedirs(curated_dir, exist_ok=True)
        
        if save_curated_images:
            for i, frame_data in enumerate(curated['worst_infected']):
                path = os.path.join(curated_dir, f"worst_infected_{i+1}_frame_{frame_data['frame_number']}.jpg")
                cv2.imwrite(path, frame_data['annotated_frame'])
            
            for i, frame_data in enumerate(curated['most_weeds']):
                path = os.path.join(curated_dir, f"most_weeds_{i+1}_frame_{frame_data['frame_number']}.jpg")
                cv2.imwrite(path, frame_data['annotated_frame'])
            
            for i, frame_data in enumerate(curated['healthiest']):
                path = os.path.join(curated_dir, f"healthiest_{i+1}_frame_{frame_data['frame_number']}.jpg")
                cv2.imwrite(path, frame_data['annotated_frame'])
            
            print(f"✅ Saved {len(curated['worst_infected']) + len(curated['most_weeds']) + len(curated['healthiest'])} curated images")
        
        # Generate summary report
        report = {
            'video_path': video_path,
            'video_info': {
                'width': width,
                'height': height,
                'fps': fps,
                'total_frames': total_frames,
                'processed_frames': processed_frames
            },
            'area_coverage': {
                'good_crop_percentage': float(avg_good),
                'bad_crop_percentage': float(avg_bad),
                'weed_percentage': float(avg_weed),
                'remaining_percentage': float(100 - avg_good - avg_bad - avg_weed)
            },
            'yield_estimation': {
                'average_yield_per_acre': float(avg_yield),
                'yield_percentage': float((avg_yield / 150.0) * 100) if avg_yield > 0 else 0,
                'base_yield_per_acre': 150.0
            },
            'curated_images': {
                'worst_infected_count': len(curated['worst_infected']),
                'most_weeds_count': len(curated['most_weeds']),
                'healthiest_count': len(curated['healthiest']),
                'curated_dir': curated_dir
            },
            'detection_summary': {
                'total_weeds_detected': sum(len(f['detections']['weeds']) for f in all_frame_data),
                'total_pests_detected': sum(len(f['detections']['pests']) for f in all_frame_data),
                'total_diseases_detected': sum(len(f['detections']['diseases']) for f in all_frame_data),
                'avg_weeds_per_frame': sum(len(f['detections']['weeds']) for f in all_frame_data) / processed_frames if processed_frames > 0 else 0,
                'avg_pests_per_frame': sum(len(f['detections']['pests']) for f in all_frame_data) / processed_frames if processed_frames > 0 else 0,
                'avg_diseases_per_frame': sum(len(f['detections']['diseases']) for f in all_frame_data) / processed_frames if processed_frames > 0 else 0
            },
            'output_files': {
                'annotated_video': os.path.join(output_dir, f"{base_name}_annotated.mp4") if save_annotated_video else None,
                'curated_images_dir': curated_dir,
                'report_json': os.path.join(output_dir, f"{base_name}_report.json")
            }
        }
        
        # Save report as JSON
        report_path = report['output_files']['report_json']
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Analysis Complete!")
        print(f"   Good Crop: {avg_good:.2f}%")
        print(f"   Bad Crop: {avg_bad:.2f}%")
        print(f"   Weeds: {avg_weed:.2f}%")
        print(f"   Estimated Yield: {avg_yield:.2f} bushels/acre ({report['yield_estimation']['yield_percentage']:.1f}% of base)")
        print(f"\n📄 Full report saved to: {report_path}")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description='Unified Real-Time Agricultural Detection System'
    )
    parser.add_argument(
        '--weed-model',
        type=str,
        required=True,
        help='Path to weed detection YOLO model (.pt file)'
    )
    parser.add_argument(
        '--pest-model',
        type=str,
        required=True,
        help='Path to pest detection YOLO model (.pt file)'
    )
    parser.add_argument(
        '--disease-model',
        type=str,
        required=True,
        help='Path to disease classification TensorFlow model directory'
    )
    parser.add_argument(
        '--image',
        type=str,
        help='Path to input image (for single image processing)'
    )
    parser.add_argument(
        '--video',
        type=str,
        help='Path to video file (for complete drone video analysis)'
    )
    parser.add_argument(
        '--source',
        type=str,
        default='0',
        help='Video source: camera index (0, 1, 2...) or RTSP/HTTP URL (for live processing)'
    )
    parser.add_argument(
        '--frame-skip',
        type=int,
        default=1,
        help='Process every Nth frame for video analysis (default: 1 = all frames)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='drone_analysis',
        help='Output directory for video analysis results (default: drone_analysis)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for annotated image/video'
    )
    parser.add_argument(
        '--classes',
        type=str,
        default='plant_village_classes.txt',
        help='Path to disease class names file or comma-separated list (default: plant_village_classes.txt)'
    )
    parser.add_argument(
        '--plant-detector',
        type=str,
        default=None,
        help='Path to plant detection YOLO model (if None, uses pest model)'
    )
    parser.add_argument(
        '--conf',
        type=float,
        default=0.25,
        help='Confidence threshold (default: 0.25)'
    )
    parser.add_argument(
        '--save-video',
        action='store_true',
        help='Save live video to file'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Hide display window'
    )
    
    args = parser.parse_args()
    
    # Load class names if provided
    disease_class_names = None
    if args.classes:
        if os.path.isfile(args.classes):
            with open(args.classes, 'r') as f:
                disease_class_names = [line.strip() for line in f.readlines()]
        else:
            disease_class_names = [name.strip() for name in args.classes.split(',')]
    
    # Initialize detector
    detector = UnifiedAgriculturalDetector(
        weed_model_path=args.weed_model,
        pest_model_path=args.pest_model,
        disease_model_path=args.disease_model,
        disease_class_names=disease_class_names,
        conf_threshold=args.conf,
        plant_detector_model=args.plant_detector
    )
    
    # Process image, video file, or live video
    if args.image:
        result = detector.process_image(args.image, args.output)
        print(f"\n📊 Detection Summary:")
        print(f"   Weeds: {len(result['detections']['weeds'])}")
        print(f"   Pests: {len(result['detections']['pests'])}")
        print(f"   Diseases: {len(result['detections']['diseases'])}")
    elif args.video:
        # Process video file with complete analysis
        report = detector.process_video_file(
            video_path=args.video,
            output_dir=args.output_dir,
            frame_skip=args.frame_skip,
            save_annotated_video=True,
            save_curated_images=True
        )
        print(f"\n✅ Video analysis complete! Check {args.output_dir} for results.")
    else:
        # Parse source
        try:
            if args.source.isdigit():
                source = int(args.source)
            else:
                source = args.source
        except:
            source = 0
        
        output_path = args.output or "live_output.mp4"
        
        detector.process_live_video(
            source=source,
            show_display=not args.no_display,
            save_video=args.save_video,
            output_path=output_path
        )


if __name__ == "__main__":
    main()

