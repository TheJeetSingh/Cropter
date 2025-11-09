# YOLOv8 Agricultural Crop Detection System

A comprehensive YOLOv8-based system for agricultural crop detection, disease identification, weed detection, and field analysis.

## Features

### Core Detection Capabilities

✅ **1. Crop Health Issues**
   - Disease detection (diseased crops)
   - Nutrient deficiency identification
   - Health severity assessment

✅ **2. Pest Infestations**
   - Pest damage detection
   - Active pest presence identification
   - Infestation level assessment

✅ **3. Irrigation Problems**
   - Dry crop detection (water stress)
   - Dry soil area identification
   - Overwatering detection

✅ **4. Weed Growth**
   - Individual weed detection
   - Weed infestation identification
   - Infestation level assessment

### Additional Features

- ✅ **Crop Detection**: Draw bounding boxes around crops
- ✅ **Comprehensive Analysis**: Complete field health assessment
- ✅ **Heat Map Generation**: Visualize problem areas with heat maps
- ✅ **Video Processing**: Process drone videos frame by frame
- ✅ **JSON Export**: Export detections in backend-friendly format
- ✅ **Actionable Recommendations**: AI-generated recommendations for each issue

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **For GPU support (optional but recommended):**
```bash
# Install PyTorch with CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Quick Start

### 1. Download Dataset

**Option A: From Roboflow**
```bash
# List recommended datasets
python download_dataset.py --source list

# Download from Roboflow (requires API key)
python download_dataset.py --source roboflow \
    --workspace roboflow-jvuqo \
    --project weed-detection-in-soybean-crop \
    --version 1 \
    --api-key YOUR_ROBOFLOW_API_KEY
```

**Option B: From Kaggle**
```bash
# First, set up Kaggle API:
# 1. Go to https://www.kaggle.com/settings
# 2. Download kaggle.json
# 3. Place it in ~/.kaggle/kaggle.json

# Download dataset
python download_dataset.py --source kaggle \
    --kaggle-dataset abdallahalidev/plantvillage-dataset \
    --output dataset
```

### 2. Organize Dataset

Organize the downloaded dataset into YOLO format:
```bash
python organize_dataset.py --input dataset --output dataset_organized
```

This will:
- Split images into train/val/test (70%/15%/15%)
- Create proper directory structure
- Generate `dataset.yaml` file

### 3. Train the Model

Train YOLOv8 on your dataset:
```bash
python yolov8.py --mode train \
    --data dataset_organized/dataset.yaml \
    --epochs 100 \
    --batch 16
```

Training will take 2-3 hours depending on your hardware. The best model will be saved at:
`runs/detect/agricultural_crop_detection/weights/best.pt`

### 4. Test the Model

Test the trained model on test images:
```bash
python yolov8.py --mode test \
    --model runs/detect/agricultural_crop_detection/weights/best.pt \
    --test-dir dataset_organized/images/test \
    --output outputs
```

### 5. Run Inference

**Single Image:**
```bash
python yolov8.py --mode complete \
    --model runs/detect/agricultural_crop_detection/weights/best.pt \
    --image path/to/image.jpg \
    --output outputs
```

**Video Processing:**
```bash
python yolov8.py --mode video \
    --model runs/detect/agricultural_crop_detection/weights/best.pt \
    --video path/to/drone_video.mp4 \
    --output outputs \
    --frame-skip 1
```

## Usage Examples

### Complete Image Analysis
```python
from yolov8 import AgriculturalYOLO

# Initialize model
model = AgriculturalYOLO(model_path='runs/detect/agricultural_crop_detection/weights/best.pt')

# Process image with full analysis
result = model.process_image_complete('field_image.jpg', output_dir='outputs')

# Access results
print(f"Found {len(result['detections'])} objects")
print(f"Health score: {result['analysis']['health_score']}%")
```

### Video Processing
```python
# Process drone video
result = model.process_video(
    'drone_video.mp4',
    output_dir='outputs',
    frame_skip=1  # Process every frame
)

# Detections are saved as JSON
# Access frame-by-frame detections
for frame_data in result['frame_detections']:
    print(f"Frame {frame_data['frame_number']}: {len(frame_data['detections'])} detections")
```

### Export Detections as JSON
```python
# Save detections in backend-friendly format
model.save_detections_json(
    detections=result['detections'],
    output_path='detections.json',
    metadata={'field_id': 'field_001', 'date': '2024-01-15'}
)
```

## Dataset Structure

After organization, your dataset should look like:
```
dataset_organized/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── dataset.yaml
```

## Recommended Datasets

1. **Plant Village** (Kaggle)
   - Large collection of plant disease images
   - Dataset: `abdallahalidev/plantvillage-dataset`

2. **Weed Detection in Soybean Crop** (Roboflow)
   - Workspace: `roboflow-jvuqo`
   - Project: `weed-detection-in-soybean-crop`

3. **New Plant Diseases Dataset** (Kaggle)
   - Dataset: `vipoooool/new-plant-diseases-dataset`

## Output Files

When processing images/videos, the system generates:

- `*_annotated.jpg/mp4`: Images/video with bounding boxes
- `*_heatmap_all.jpg`: Heat map of all detections
- `*_heatmap_weeds.jpg`: Heat map of weed detections
- `*_heatmap_diseases.jpg`: Heat map of disease detections
- `*_dry_soil.jpg`: Highlighted dry soil areas
- `*_detections.json`: JSON file with all detections
- `*_analysis.json`: Analysis report

## JSON Output Format

```json
{
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95,
      "class_id": 0,
      "class_name": "healthy_crop"
    }
  ],
  "total_count": 10,
  "class_summary": {
    "healthy_crop": {
      "count": 5,
      "avg_confidence": 0.92
    }
  },
  "metadata": {}
}
```

## Class Definitions

### Crop Health Issues
- `healthy_crop`: Healthy, growing crops (baseline)
- `diseased_crop`: Crops with visible diseases
- `nutrient_deficiency`: Crops showing nutrient deficiency signs

### Pest Infestations
- `pest_damage`: Crops damaged by pests (visible damage)
- `pest_presence`: Active pests detected

### Irrigation Problems
- `dry_crop`: Crops showing signs of drought/water stress
- `dry_soil`: Areas with dry soil conditions
- `overwatered`: Areas showing overwatering signs

### Weed Growth
- `weed`: Individual weed plants
- `weed_infestation`: Dense weed areas/infestations

### Optimal Conditions
- `optimal_growth`: Areas with optimal growing conditions

## Troubleshooting

**Issue: CUDA out of memory**
- Reduce batch size: `--batch 8` or `--batch 4`
- Use smaller image size: Add `imgsz=416` in training

**Issue: No detections found**
- Lower confidence threshold: `--conf 0.1`
- Check if model was trained on similar data

**Issue: Dataset not found**
- Ensure dataset is organized correctly
- Check `dataset.yaml` paths are correct

## License

This project is open source. Please check individual dataset licenses when downloading.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

