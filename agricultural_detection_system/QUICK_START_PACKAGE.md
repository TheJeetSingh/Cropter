# 🚀 Quick Start Guide - Integrated Agricultural Detection System

## 📦 Package Contents

✅ **All 3 trained models included:**
- Weed Detection Model (41.5% mAP50)
- Pest Detection Model (38.7% mAP50)
- Disease Classification Model (38 classes)

✅ **Complete integration scripts**
✅ **Backend API for web integration**
✅ **Ready-to-use examples**

## ⚡ 3-Step Setup

### Step 1: Extract Package
```bash
unzip agricultural_detection_system.zip
cd agricultural_detection_system
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

Or use the setup script:
```bash
chmod +x setup_package.sh
./setup_package.sh
```

### Step 3: Run!
```bash
# Test on an image
python run_integrated_system.py --image test.jpg --output result.jpg

# Or process a video
python run_integrated_system.py --video drone_footage.mp4 --output-dir results
```

## 🎯 What It Does

1. **Detects Weeds** - Identifies weed locations in drone imagery
2. **Detects Pests** - Finds 9 types of agricultural pests
3. **Classifies Diseases** - Identifies 38 plant diseases
4. **Calculates Areas** - Good crop vs bad crop vs weeds percentage
5. **Estimates Yield** - Predicts crop yield based on health

## 📊 Example Output

When processing a video, you'll get:
- `annotated_video.mp4` - Video with all detections marked
- `summary_report.json` - Complete analysis with statistics
- `curated_images/` - Best/worst frames automatically selected
- Area coverage percentages
- Yield estimation

## 🔧 Common Commands

```bash
# Single image
python run_integrated_system.py --image field.jpg --output result.jpg

# Video with full analysis
python run_integrated_system.py --video video.mp4 --output-dir analysis

# Live webcam
python run_integrated_system.py --live --source 0

# Adjust confidence threshold
python run_integrated_system.py --image test.jpg --conf 0.3
```

## 📞 Need Help?

See `PACKAGE_README.md` for detailed documentation.

---

**Ready to analyze your agricultural imagery! 🚁🌾**

