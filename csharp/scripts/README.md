# C# Migration Scripts

Utility scripts for the C# migration project.

## convert_joblib_to_onnx.py

Converts scikit-learn models (saved as `.joblib`) to ONNX format for C# inference.

### Requirements

```bash
pip install scikit-learn joblib skl2onnx onnx onnxruntime
```

### Usage

```bash
# Convert a single model
python convert_joblib_to_onnx.py input_model.joblib output_model.onnx

# Example with lottery prediction model
python convert_joblib_to_onnx.py loto_predictor.joblib loto_predictor.onnx
```

### Features

- ✅ Automatic feature count detection
- ✅ ONNX opset 12 (widely compatible)
- ✅ Model verification after conversion
- ✅ File size reporting
- ✅ Error handling and validation

### Output

The script will:
1. Load the joblib model
2. Detect input feature count
3. Convert to ONNX format (opset 12)
4. Save the .onnx file
5. Verify the conversion with test inference
6. Report file size and metadata

### Using in C#

After conversion, use the ONNX model in C#:

```csharp
using XsDas.Infrastructure.Services;

// Create AI service
var aiService = new AiService();

// Load the converted model
aiService.LoadModel("loto_predictor.onnx");

// Prepare features (must match model's feature count)
var features = new float[] { 1.0f, 2.0f, 3.0f, /* ... */ };

// Make prediction
var prediction = aiService.Predict(features);
Console.WriteLine($"Prediction: {prediction[0]}");
```

### Troubleshooting

**Issue:** "Model type not supported"
- **Solution:** Ensure model is a scikit-learn estimator (RandomForest, LogisticRegression, etc.)

**Issue:** "Feature count mismatch"
- **Solution:** Check `model.n_features_in_` matches your data

**Issue:** "ONNX Runtime error"
- **Solution:** Install onnxruntime: `pip install onnxruntime`

### Supported Models

- Random Forest (Classifier/Regressor)
- Logistic Regression
- Linear Regression
- Decision Trees
- Gradient Boosting
- SVM
- And most scikit-learn estimators

### Model Testing

The script automatically tests the converted model with dummy data to ensure it works correctly before you use it in production.

## Notes

- Always verify converted models with test data before production use
- Keep original `.joblib` files as backups
- ONNX models are typically larger than joblib files
- Conversion may take a few seconds for large models
