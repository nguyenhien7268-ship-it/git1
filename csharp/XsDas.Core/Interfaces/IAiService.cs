namespace XsDas.Core.Interfaces;

/// <summary>
/// Service interface for AI inference operations using ONNX Runtime.
/// Provides methods to load models and make predictions.
/// </summary>
public interface IAiService
{
    /// <summary>
    /// Load an ONNX model from file
    /// </summary>
    /// <param name="modelPath">Path to .onnx model file</param>
    void LoadModel(string modelPath);

    /// <summary>
    /// Predict using the loaded model
    /// </summary>
    /// <param name="features">Input features as float array</param>
    /// <returns>Prediction result (probability or class)</returns>
    float[] Predict(float[] features);

    /// <summary>
    /// Predict with probabilities for classification models
    /// </summary>
    /// <param name="features">Input features as float array</param>
    /// <returns>Class probabilities</returns>
    float[] PredictProbability(float[] features);

    /// <summary>
    /// Check if a model is currently loaded
    /// </summary>
    bool IsModelLoaded { get; }

    /// <summary>
    /// Get the number of input features required by the model
    /// </summary>
    int InputFeatureCount { get; }
}
