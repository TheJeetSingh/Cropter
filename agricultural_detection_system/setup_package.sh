#!/bin/bash
# Setup script for Integrated Agricultural Detection System

echo "🚁 Setting up Integrated Agricultural Detection System"
echo "======================================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt || { echo "❌ Failed to install dependencies"; exit 1; }

# Verify models exist
echo ""
echo "🔍 Verifying models..."
MODELS_OK=true

if [ ! -f "runs/detect/weed_detection/weights/best.pt" ]; then
    echo "⚠️  Warning: Weed model not found"
    MODELS_OK=false
else
    echo "✅ Weed model found"
fi

if [ ! -f "runs/detect/pest_detection/weights/best.pt" ]; then
    echo "⚠️  Warning: Pest model not found"
    MODELS_OK=false
else
    echo "✅ Pest model found"
fi

if [ ! -d "plant-disease-tensorflow2-plant-disease-v1" ]; then
    echo "⚠️  Warning: Disease model not found"
    MODELS_OK=false
else
    echo "✅ Disease model found"
fi

if [ ! -f "plant_village_classes.txt" ]; then
    echo "⚠️  Warning: Class names file not found"
    MODELS_OK=false
else
    echo "✅ Class names file found"
fi

echo ""
if [ "$MODELS_OK" = true ]; then
    echo "✅ Setup complete! All models verified."
    echo ""
    echo "🚀 Quick start:"
    echo "   python3 run_integrated_system.py --image test.jpg --output result.jpg"
else
    echo "⚠️  Setup complete, but some models are missing."
    echo "   Please ensure all model files are in place before running."
fi

echo ""
echo "======================================================"

