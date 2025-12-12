#!/usr/bin/env python3
"""
Convert scikit-learn .joblib models to ONNX format for C# inference.

Requirements:
    pip install scikit-learn joblib skl2onnx onnx onnxruntime

Usage:
    python convert_joblib_to_onnx.py <input.joblib> <output.onnx>
"""

import sys
import os
import joblib
import numpy as np
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


def convert_model(joblib_path, onnx_path):
    print(f"Loading model from: {joblib_path}")
    model = joblib.load(joblib_path)
    print(f"Model type: {type(model).__name__}")
    
    n_features = model.n_features_in_ if hasattr(model, 'n_features_in_') else 10
    print(f"Number of features: {n_features}")
    
    initial_type = [('float_input', FloatTensorType([None, n_features]))]
    
    print(f"Converting to ONNX...")
    onnx_model = convert_sklearn(model, initial_types=initial_type, target_opset=12)
    
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())
    
    print(f"✓ Converted: {onnx_path}")
    print(f"  Size: {os.path.getsize(onnx_path) / 1024:.2f} KB")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_joblib_to_onnx.py <input.joblib> <output.onnx>")
        sys.exit(1)
    
    joblib_path, onnx_path = sys.argv[1], sys.argv[2]
    
    if not os.path.exists(joblib_path):
        print(f"Error: File not found: {joblib_path}")
        sys.exit(1)
    
    output_dir = os.path.dirname(onnx_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if convert_model(joblib_path, onnx_path):
        print("\n✓ Conversion complete!")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
