using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;
using XsDas.Core.Interfaces;

namespace XsDas.Infrastructure.Services;

/// <summary>
/// AI service implementation using ONNX Runtime for model inference.
/// Supports loading .onnx models converted from scikit-learn.
/// </summary>
public class AiService : IAiService, IDisposable
{
    private InferenceSession? _session;
    private string? _inputName;
    private string? _outputName;
    private int _inputFeatureCount;

    public bool IsModelLoaded => _session != null;
    public int InputFeatureCount => _inputFeatureCount;

    /// <summary>
    /// Load an ONNX model from the specified path
    /// </summary>
    public void LoadModel(string modelPath)
    {
        if (!File.Exists(modelPath))
        {
            throw new FileNotFoundException($"Model file not found: {modelPath}");
        }

        try
        {
            // Dispose existing session if any
            _session?.Dispose();

            // Create new inference session
            _session = new InferenceSession(modelPath);

            // Get input metadata
            var inputMeta = _session.InputMetadata.First();
            _inputName = inputMeta.Key;
            
            // Get input dimensions (assuming shape [batch_size, n_features])
            var inputShape = inputMeta.Value.Dimensions;
            _inputFeatureCount = inputShape.Length > 1 ? inputShape[1] : inputShape[0];

            // Get output metadata
            _outputName = _session.OutputMetadata.First().Key;

            Console.WriteLine($"Model loaded successfully:");
            Console.WriteLine($"  Input: {_inputName}, Features: {_inputFeatureCount}");
            Console.WriteLine($"  Output: {_outputName}");
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Failed to load model: {ex.Message}", ex);
        }
    }

    /// <summary>
    /// Make a prediction using the loaded model
    /// </summary>
    public float[] Predict(float[] features)
    {
        if (!IsModelLoaded)
        {
            throw new InvalidOperationException("No model loaded. Call LoadModel() first.");
        }

        if (features.Length != _inputFeatureCount)
        {
            throw new ArgumentException(
                $"Feature count mismatch. Expected {_inputFeatureCount}, got {features.Length}");
        }

        try
        {
            // Create input tensor (shape: [1, n_features])
            var inputTensor = new DenseTensor<float>(features, new[] { 1, _inputFeatureCount });

            // Create input container
            var inputs = new List<NamedOnnxValue>
            {
                NamedOnnxValue.CreateFromTensor(_inputName!, inputTensor)
            };

            // Run inference
            using var results = _session!.Run(inputs);
            
            // Get output
            var output = results.First().AsEnumerable<float>().ToArray();
            return output;
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Prediction failed: {ex.Message}", ex);
        }
    }

    /// <summary>
    /// Make a prediction with probabilities (for classification models)
    /// </summary>
    public float[] PredictProbability(float[] features)
    {
        // For many models, this is the same as Predict
        // Override in derived classes if needed
        return Predict(features);
    }

    /// <summary>
    /// Dispose of the inference session
    /// </summary>
    public void Dispose()
    {
        _session?.Dispose();
        _session = null;
    }
}
