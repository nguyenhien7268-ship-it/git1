#!/usr/bin/env python3
"""
Convert XGBoost .joblib model to ONNX format for C# inference

This script converts the Python machine learning model to ONNX format
so it can be used with Microsoft.ML.OnnxRuntime in C#.

Requirements:
    pip install xgboost scikit-learn joblib skl2onnx onnx onnxruntime

Usage:
    python convert_model_to_onnx.py
"""

import sys
import os
import joblib
import numpy as np
from pathlib import Path

try:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    import onnx
    import onnxruntime as rt
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Please install: pip install skl2onnx onnx onnxruntime")
    sys.exit(1)


def find_model_file():
    """Find the .joblib model file in the project"""
    # Check common locations
    search_paths = [
        "../logic/ml_model_files/xgb_model.joblib",
        "../logic/ml_model_files/model.joblib",
        "../data/xgb_model.joblib",
        "../xgb_model.joblib",
    ]
    
    for path in search_paths:
        full_path = Path(__file__).parent / path
        if full_path.exists():
            return full_path
    
    # If not found, search recursively
    project_root = Path(__file__).parent.parent
    for file_path in project_root.rglob("*.joblib"):
        if "xgb" in file_path.name.lower() or "model" in file_path.name.lower():
            return file_path
    
    return None


def convert_to_onnx(model_path, output_path):
    """Convert the model to ONNX format"""
    print(f"Loading model from: {model_path}")
    
    try:
        # Load the model
        model = joblib.load(model_path)
        print(f"Model type: {type(model)}")
        
        # Define input shape (14 features for V7.7)
        # F1-F12 from original model + F13 (hit_in_last_3_days) + F14 (change_in_gan)
        n_features = 14
        initial_type = [('float_input', FloatTensorType([None, n_features]))]
        
        # Convert to ONNX
        print(f"Converting to ONNX format (input shape: [None, {n_features}])...")
        onnx_model = convert_sklearn(
            model,
            initial_types=initial_type,
            target_opset=12,  # Compatible with OnnxRuntime 1.18
            options={'zipmap': False}  # Disable zipmap for simpler output
        )
        
        # Save ONNX model
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        onnx.save_model(onnx_model, str(output_path))
        print(f"✅ Model saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size / 1024:.2f} KB")
        
        # Validate the model
        print("\nValidating ONNX model...")
        onnx.checker.check_model(onnx_model)
        print("✅ Model is valid")
        
        # Test inference
        print("\nTesting inference...")
        test_input = np.random.rand(1, n_features).astype(np.float32)
        
        # Test with ONNX Runtime
        sess = rt.InferenceSession(str(output_path))
        input_name = sess.get_inputs()[0].name
        output_name = sess.get_outputs()[0].name
        
        onnx_pred = sess.run([output_name], {input_name: test_input})
        print(f"✅ Inference successful")
        print(f"   Input shape: {test_input.shape}")
        print(f"   Output shape: {onnx_pred[0].shape}")
        print(f"   Sample prediction: {onnx_pred[0][0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main conversion workflow"""
    print("=" * 70)
    print("XS-DAS Model Converter: .joblib → ONNX")
    print("=" * 70)
    print()
    
    # Find model file
    model_path = find_model_file()
    
    if model_path is None:
        print("❌ Error: Could not find .joblib model file")
        print("\nSearched in:")
        print("  - logic/ml_model_files/")
        print("  - data/")
        print("  - Project root")
        print("\nPlease ensure the model file exists or specify the path manually.")
        return 1
    
    # Set output path
    output_path = Path(__file__).parent / "XsDas.Infrastructure" / "Data" / "xgb_model.onnx"
    
    # Convert
    success = convert_to_onnx(model_path, output_path)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ Conversion Complete!")
        print("=" * 70)
        print(f"\nONNX Model Location: {output_path}")
        print("\nNext Steps:")
        print("1. The ONNX model is ready to use in C#")
        print("2. Implement AiService.cs to load and use the model")
        print("3. Use Microsoft.ML.OnnxRuntime for inference")
        print("\nExample C# usage:")
        print("""
    using Microsoft.ML.OnnxRuntime;
    using Microsoft.ML.OnnxRuntime.Tensors;
    
    var session = new InferenceSession("xgb_model.onnx");
    var inputData = new float[] { /* 14 features */ };
    var tensor = new DenseTensor<float>(inputData, new[] { 1, 14 });
    var inputs = new List<NamedOnnxValue> { 
        NamedOnnxValue.CreateFromTensor("float_input", tensor) 
    };
    var results = session.Run(inputs);
        """)
        return 0
    else:
        print("\n❌ Conversion failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
