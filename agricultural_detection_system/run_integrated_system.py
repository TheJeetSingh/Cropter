#!/usr/bin/env python3
"""
Integrated Agricultural Detection System
Combines Weed Detection, Pest Detection, and Disease Classification
Ready-to-use script for drone video analysis
"""

import argparse
import os
import sys
from pathlib import Path

from unified_agricultural_detector import UnifiedAgriculturalDetector


def main():
    parser = argparse.ArgumentParser(
        description='Integrated Agricultural Detection System - Weed + Pest + Disease',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single image
  python run_integrated_system.py --image test.jpg --output result.jpg

  # Process a video file (drone footage)
  python run_integrated_system.py --video drone_footage.mp4 --output-dir analysis_results

  # Live video stream (webcam)
  python run_integrated_system.py --live --source 0

  # Process video with area calculation and curated images
  python run_integrated_system.py --video farm_video.mp4 --output-dir results --frame-skip 5
        """
    )
    
    # Model paths (defaults to trained models)
    parser.add_argument('--weed-model', type=str,
                       default='runs/detect/weed_detection/weights/best.pt',
                       help='Path to weed detection YOLO model')
    parser.add_argument('--pest-model', type=str,
                       default='runs/detect/pest_detection/weights/best.pt',
                       help='Path to pest detection YOLO model')
    parser.add_argument('--disease-model', type=str,
                       default='plant-disease-tensorflow2-plant-disease-v1',
                       help='Path to disease classification TensorFlow model directory')
    parser.add_argument('--classes', type=str,
                       default='plant_village_classes.txt',
                       help='Path to disease class names file')
    parser.add_argument('--plant-detector', type=str, default=None,
                       help='Path to plant detection YOLO model (if None, uses pest model)')
    
    # Input/Output
    parser.add_argument('--image', type=str, help='Path to input image')
    parser.add_argument('--video', type=str, help='Path to input video file')
    parser.add_argument('--live', action='store_true', help='Process live video stream')
    parser.add_argument('--source', type=int, default=0, help='Video source (0 for webcam)')
    parser.add_argument('--output', type=str, default='output.jpg', help='Output image path')
    parser.add_argument('--output-dir', type=str, default='drone_analysis',
                       help='Output directory for video analysis')
    
    # Processing options
    parser.add_argument('--conf', type=float, default=0.25,
                       help='Confidence threshold (0.0-1.0)')
    parser.add_argument('--frame-skip', type=int, default=1,
                       help='Process every Nth frame for video (default: 1 = all frames)')
    parser.add_argument('--no-display', action='store_true',
                       help='Don\'t show live display window')
    parser.add_argument('--save-video', action='store_true',
                       help='Save annotated video output')
    
    args = parser.parse_args()
    
    # Validate model paths
    if not os.path.exists(args.weed_model):
        print(f"❌ Error: Weed model not found: {args.weed_model}")
        sys.exit(1)
    
    if not os.path.exists(args.pest_model):
        print(f"❌ Error: Pest model not found: {args.pest_model}")
        sys.exit(1)
    
    if not os.path.exists(args.disease_model):
        print(f"❌ Error: Disease model not found: {args.disease_model}")
        sys.exit(1)
    
    if not os.path.exists(args.classes):
        print(f"⚠️  Warning: Class names file not found: {args.classes}")
        disease_classes = None
    else:
        with open(args.classes, 'r') as f:
            disease_classes = [line.strip() for line in f.readlines() if line.strip()]
        print(f"✅ Loaded {len(disease_classes)} disease classes")
    
    # Initialize detector
    print("\n" + "="*60)
    print("🚁 INTEGRATED AGRICULTURAL DETECTION SYSTEM")
    print("="*60)
    print(f"🌿 Weed Model: {args.weed_model}")
    print(f"🐛 Pest Model: {args.pest_model}")
    print(f"🌱 Disease Model: {args.disease_model}")
    print("="*60 + "\n")
    
    try:
        detector = UnifiedAgriculturalDetector(
            weed_model_path=args.weed_model,
            pest_model_path=args.pest_model,
            disease_model_path=args.disease_model,
            disease_class_names=disease_classes,
            conf_threshold=args.conf,
            plant_detector_model=args.plant_detector
        )
        
        # Process based on input type
        if args.video:
            # Video file processing with full analysis
            print(f"📹 Processing video: {args.video}")
            print(f"   Output directory: {args.output_dir}")
            print(f"   Frame skip: {args.frame_skip}\n")
            
            report = detector.process_video_file(
                video_path=args.video,
                output_dir=args.output_dir,
                frame_skip=args.frame_skip,
                save_annotated_video=True,
                save_curated_images=True
            )
            
            print("\n" + "="*60)
            print("✅ VIDEO ANALYSIS COMPLETE")
            print("="*60)
            print(f"📊 Area Coverage:")
            print(f"   Good Crop: {report['area_stats']['good_crop_pct']:.1f}%")
            print(f"   Bad Crop: {report['area_stats']['bad_crop_pct']:.1f}%")
            print(f"   Weeds: {report['area_stats']['weed_pct']:.1f}%")
            print(f"\n🌾 Yield Estimation: {report['yield_estimation']['estimated_yield_pct']:.1f}%")
            print(f"\n📁 Results saved to: {args.output_dir}")
            print("="*60)
            
        elif args.live:
            # Live video stream
            print("📹 Starting live video processing...")
            print("   Press 'q' to quit, 's' to save screenshot\n")
            
            detector.process_live_video(
                source=args.source,
                conf_threshold=args.conf,
                show_display=not args.no_display,
                save_video=args.save_video,
                output_path=args.output if args.save_video else "live_output.mp4"
            )
            
        elif args.image:
            # Single image processing
            print(f"🖼️  Processing image: {args.image}")
            
            result = detector.process_image(args.image, args.output)
            
            print("\n" + "="*60)
            print("✅ DETECTION RESULTS")
            print("="*60)
            print(f"🌿 Weeds detected: {len(result['detections']['weeds'])}")
            print(f"🐛 Pests detected: {len(result['detections']['pests'])}")
            print(f"🌱 Diseases detected: {len(result['detections']['diseases'])}")
            print(f"\n📁 Annotated image saved to: {result['annotated_image_path']}")
            print("="*60)
            
        else:
            parser.print_help()
            print("\n❌ Error: Must specify --image, --video, or --live")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

