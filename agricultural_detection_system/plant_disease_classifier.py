"""
Plant Disease Recognition Model with Label Overlay
Handles TensorFlow SavedModel format for disease classification
Takes one plant image → outputs text label → overlays on image
"""

import cv2
import numpy as np
import os
from pathlib import Path
from typing import Optional, Tuple, List
import argparse

# Try importing TensorFlow
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow not available. Install with: pip install tensorflow")


class PlantDiseaseClassifier:
    """Class to load and run plant disease classification models"""
    
    def __init__(self, model_path: str, class_names: Optional[List[str]] = None):
        """
        Initialize the plant disease classifier
        
        Args:
            model_path: Path to TensorFlow SavedModel directory
            class_names: List of class names (disease labels). If None, will try to infer.
        """
        self.model_path = model_path
        self.class_names = class_names
        self.model = None
        self.input_size = (224, 224)  # Default, will be updated based on model
        
        # Load the model
        self._load_model()
    
    def _load_model(self):
        """Load TensorFlow SavedModel"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow required. Install: pip install tensorflow")
        
        print(f"📥 Loading TensorFlow SavedModel: {self.model_path}")
        
        # Check if it's a SavedModel directory
        if os.path.isdir(self.model_path):
            self.model = tf.saved_model.load(self.model_path)
            print("✅ Model loaded successfully")
        else:
            raise ValueError(f"Model path must be a directory containing SavedModel: {self.model_path}")
    
    def preprocess_image(self, image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess image for model input
        
        Args:
            image_path: Path to input image
            
        Returns:
            Tuple of (preprocessed_image, original_image)
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Resize to model input size
        image_resized = cv2.resize(image, self.input_size)
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1] range
        image_normalized = image_rgb.astype(np.float32) / 255.0
        
        # Add batch dimension
        image_batch = np.expand_dims(image_normalized, axis=0)
        
        return image_batch, image  # Return both preprocessed and original
    
    def predict(self, image_path: str) -> Tuple[str, float]:
        """
        Predict disease from plant image
        
        Args:
            image_path: Path to plant image
            
        Returns:
            Tuple of (disease_label, confidence)
        """
        # Preprocess image
        image_batch, original_image = self.preprocess_image(image_path)
        
        # Run inference
        try:
            # Try different signature names
            if hasattr(self.model, 'signatures'):
                # Try serving_default signature
                infer = self.model.signatures.get('serving_default', None)
                if infer is None:
                    # Get first available signature
                    infer = list(self.model.signatures.values())[0]
                
                # Convert to tensor
                input_tensor = tf.constant(image_batch)
                predictions = infer(input_tensor)
                
                # Extract output (handle different output formats)
                output_key = list(predictions.keys())[0]
                output = predictions[output_key].numpy()[0]
            else:
                # Direct call
                predictions = self.model(image_batch)
                if hasattr(predictions, 'numpy'):
                    output = predictions.numpy()[0]
                else:
                    output = predictions[0]
        except Exception as e:
            print(f"⚠️  Error during inference: {e}")
            # Try direct call
            input_tensor = tf.constant(image_batch)
            predictions = self.model(input_tensor)
            if hasattr(predictions, 'numpy'):
                output = predictions.numpy()[0]
            else:
                output = predictions[0]
        
        # Get predicted class
        class_idx = np.argmax(output)
        confidence = float(output[class_idx])
        
        # Get class name
        if self.class_names and class_idx < len(self.class_names):
            label = self.class_names[class_idx]
        else:
            label = f"Class_{class_idx}"
        
        return label, confidence
    
    def overlay_label_on_image(self, 
                               image_path: str, 
                               label: str, 
                               confidence: float,
                               output_path: Optional[str] = None,
                               font_scale: float = 1.0,
                               thickness: int = 2) -> np.ndarray:
        """
        Overlay disease label on plant image
        
        Args:
            image_path: Path to original image
            label: Disease label text
            confidence: Confidence score
            output_path: Path to save annotated image (optional)
            font_scale: Font size multiplier
            thickness: Text thickness
            
        Returns:
            Annotated image as numpy array
        """
        # Read original image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Create a copy for annotation
        annotated = image.copy()
        
        # Calculate text size and position
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"{label}"
        confidence_text = f"Confidence: {confidence:.2%}"
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )
        (conf_width, conf_height), _ = cv2.getTextSize(
            confidence_text, font, font_scale * 0.7, thickness
        )
        
        # Position text at top-left with padding
        padding = 20
        text_x = padding
        text_y = padding + text_height
        
        # Draw semi-transparent background for text
        overlay = annotated.copy()
        cv2.rectangle(
            overlay,
            (text_x - 10, text_y - text_height - 10),
            (text_x + max(text_width, conf_width) + 10, text_y + conf_height + 20),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)
        
        # Choose color based on confidence
        if confidence > 0.7:
            color = (0, 255, 0)  # Green for high confidence
        elif confidence > 0.5:
            color = (0, 165, 255)  # Orange for medium confidence
        else:
            color = (0, 0, 255)  # Red for low confidence
        
        # Draw main label
        cv2.putText(
            annotated,
            text,
            (text_x, text_y),
            font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA
        )
        
        # Draw confidence score
        cv2.putText(
            annotated,
            confidence_text,
            (text_x, text_y + conf_height + 15),
            font,
            font_scale * 0.7,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(output_path, annotated)
            print(f"✅ Saved annotated image to: {output_path}")
        
        return annotated


def main():
    parser = argparse.ArgumentParser(
        description='Plant Disease Recognition with Label Overlay'
    )
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to TensorFlow SavedModel directory'
    )
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Path to plant image'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for annotated image (default: adds _labeled to input name)'
    )
    parser.add_argument(
        '--classes',
        type=str,
        default=None,
        help='Path to text file with class names (one per line) or comma-separated list'
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Display the annotated image'
    )
    
    args = parser.parse_args()
    
    # Load class names if provided
    class_names = None
    if args.classes:
        if os.path.isfile(args.classes):
            # Read from file
            with open(args.classes, 'r') as f:
                class_names = [line.strip() for line in f.readlines()]
        else:
            # Comma-separated list
            class_names = [name.strip() for name in args.classes.split(',')]
    
    # Initialize classifier
    print("🌱 Initializing Plant Disease Classifier...")
    classifier = PlantDiseaseClassifier(args.model, class_names=class_names)
    
    # Run prediction
    print(f"🔍 Analyzing image: {args.image}")
    label, confidence = classifier.predict(args.image)
    
    print(f"\n📊 Prediction Results:")
    print(f"   Disease: {label}")
    print(f"   Confidence: {confidence:.2%}")
    
    # Overlay label on image
    if args.output is None:
        base_name = Path(args.image).stem
        output_path = f"{base_name}_labeled.jpg"
    else:
        output_path = args.output
    
    annotated_image = classifier.overlay_label_on_image(
        args.image,
        label,
        confidence,
        output_path=output_path
    )
    
    # Display if requested
    if args.show:
        cv2.imshow('Plant Disease Recognition', annotated_image)
        print("\nPress any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

