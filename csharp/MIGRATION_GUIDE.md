# Migration Guide: Python to C# (.NET 8)

## Overview

This document provides detailed guidance for completing the migration from Python to C#. It covers the logic that has been ported, remaining work, and how to verify accuracy.

## Completed Components

### 1. Core Models ✅

| Python File | C# File | Status | Notes |
|-------------|---------|--------|-------|
| `logic/models.py::Candidate` | `XsDas.Core/Models/BridgeCandidate.cs` | ✅ Complete | All properties ported |
| Database Bridge schema | `XsDas.Core/Models/Bridge.cs` | ✅ Complete | Includes performance metrics |
| DuLieu_AI table | `XsDas.Core/Models/LotteryResult.cs` | ✅ Complete | GetAllLotos() ported |

### 2. Utility Functions ✅

| Python Function | C# Method | Status |
|-----------------|-----------|--------|
| `utils.py::BONG_DUONG_V30` | `LotteryUtils.GetBongDuong()` | ✅ Complete |
| `utils.py::taoSTL_V30_Bong()` | `LotteryUtils.CreateStlWithShadow()` | ✅ Complete |
| `utils.py::checkHitSet_V30_K2N()` | `LotteryUtils.CheckHitSet()` | ✅ Complete |
| `utils.py::getAllLoto_V30()` | `LotteryResult.GetAllLotos()` | ✅ Complete |
| `common_utils.py::normalize_bridge_name()` | `LotteryUtils.NormalizeBridgeName()` | ✅ Complete |
| `common_utils.py::calculate_strict_performance()` | `LotteryUtils.CalculateStrictPerformance()` | ✅ Complete |

### 3. Database Layer ✅

| Python Module | C# Implementation | Status |
|---------------|-------------------|--------|
| `db_manager.py::ManagedBridges` | `LotteryDbContext` | ✅ Complete |
| `data_repository.py` | `BridgeRepository`, `LotteryResultRepository` | ✅ Complete |

### 4. Infrastructure Services ✅

| Python Module | C# Service | Status | Performance |
|---------------|------------|--------|-------------|
| `lo_bridge_scanner.py` | `ScannerService` | ⚠️ Partial | 3-5x faster with Parallel.ForEach |
| `de_analytics.py` | `DeAnalysisService` | ⚠️ Partial | Structure ready, logic needs completion |
| `bridge_manager_core.py::auto_manage_bridges()` | `BridgeBackgroundService` | ✅ Complete | Runs as IHostedService |

## Remaining Work

### Priority 1: Complete Bridge Scanning Logic

#### Fixed Bridges (15 total)

**Status**: 1/15 implemented

**Implementation Guide**:
```csharp
// Pattern for each fixed bridge
private List<BridgeCandidate> ScanFixedBridgeXX(List<LotteryResult> data, int depth)
{
    var candidates = new List<BridgeCandidate>();
    var recentData = data.Take(depth).Reverse().ToList();
    var results = new List<bool>();
    var stl = "N/A";
    
    foreach (var result in recentData)
    {
        // 1. Extract required prizes
        // 2. Apply bridge algorithm
        // 3. Generate prediction (STL)
        // 4. Check if prediction hits
        results.Add(hit);
    }
    
    // 5. Calculate performance metrics
    var metrics = LotteryUtils.CalculateStrictPerformance(results);
    
    // 6. Create candidate if meets threshold
    if (metrics.Streak >= _minStreak)
    {
        candidates.Add(new BridgeCandidate { /* ... */ });
    }
    
    return candidates;
}
```

**Remaining Bridges**:
- [ ] Bridge 02: G6.2+G7.3 → `getCau2_VT1_V30_V5`
- [ ] Bridge 03: Đuôi GĐB+G1 → `getCau3_VT2_V30_V5`
- [ ] Bridge 04: GĐB Sát Đuôi → `getCau4_VT3_V30_V5`
- [ ] Bridge 05: Đầu G7.0+Đuôi G7.3 → `getCau5_TDB1_V30_V5`
- [ ] Bridge 06: G7.1+G7.2 → `getCau6_VT5_V30_V5`
- [ ] Bridge 07-15: See `lo_bridge_scanner.py::LO_BRIDGE_MAP`

### Priority 2: V17 Shadow Bridges

**Python Source**: `bridges_v16.py::getAllPositions_V17_Shadow()`

**C# Target**: `ScannerService.ScanV17ShadowBridges()`

**Complexity**: High - requires position matrix (214 positions)

**Implementation Steps**:
1. Port `getAllPositions_V17_Shadow()` to generate 214-position matrix
2. Port `getPositionName_V17_Shadow()` for position naming
3. Implement position-based scanning logic:
```csharp
private List<BridgeCandidate> ScanV17ShadowBridges(List<LotteryResult> data)
{
    // 1. Preprocess data into position matrix (214 cols x N rows)
    var matrix = PreprocessDataToMatrix(data);
    
    // 2. Scan all position pairs (214 * 213 / 2 = 22,791 combinations)
    var candidates = new ConcurrentBag<BridgeCandidate>();
    
    Parallel.For(0, 214, pos1 =>
    {
        for (int pos2 = pos1 + 1; pos2 < 214; pos2++)
        {
            var candidate = ScanPositionPair(matrix, pos1, pos2);
            if (candidate != null)
                candidates.Add(candidate);
        }
    });
    
    return candidates.ToList();
}
```

### Priority 3: DE Bridge Scanning

**Python Source**: `de_bridge_scanner.py::DeBridgeScanner`

**C# Target**: New `DeBridgeScanner` class

**Implementation**:
```csharp
public class DeBridgeScanner
{
    // Module 1: Bạc Nhớ (Memory Patterns)
    private List<BridgeCandidate> ScanMemoryPattern(List<LotteryResult> data) { }
    
    // Module 2: Position-based (Vị trí)
    private List<BridgeCandidate> ScanPositionBridges(List<LotteryResult> data) { }
    
    // Module 3: Dynamic Offset (K-param)
    private List<BridgeCandidate> ScanDynamicBridges(List<LotteryResult> data) { }
    
    // Module 4: Set-based (Bộ số)
    private List<BridgeCandidate> ScanSetBridges(List<LotteryResult> data) { }
}
```

### Priority 4: Complete DE Analytics

**Python Source**: `de_analytics.py`

**Key Functions to Port**:
```python
# Python
def compute_touch_metrics(touches, all_data, window_n=30):
    # Calculate:
    # - Total count
    # - Max consecutive
    # - Covers last N
    # - Rate percent
    pass

def calculate_number_scores(all_data, config):
    # Tiered scoring:
    # - Tier 1: Bộ Ưu Tiên (Priority Sets)
    # - Tier 2: Chạm Tỷ Lệ (Touch Rate)
    # - Tier 3: Chạm Thông (Touch Through)
    pass
```

**C# Implementation**:
```csharp
// Already structured in DeAnalysisService.cs
// Need to complete:
private Dictionary<string, double> CalculatePrioritySetScores(List<LotteryResult> results)
{
    // Port from de_analytics.py lines 200-350
    // Implement Bộ Ưu Tiên logic with bonuses
}

private Dictionary<string, double> CalculateTouchRateScores(List<LotteryResult> results)
{
    // Port compute_touch_metrics logic
}
```

### Priority 5: AI Integration

**Python Source**: `ml_model.py`, `ai_feature_extractor.py`

**C# Target**: New `AiService` class

**Implementation**:
```csharp
using Microsoft.ML.OnnxRuntime;

public class AiService
{
    private InferenceSession _session;
    
    public AiService(string modelPath)
    {
        _session = new InferenceSession(modelPath);
    }
    
    public async Task<float[]> PredictAsync(float[] features)
    {
        // 1. Create input tensor
        var inputMeta = _session.InputMetadata;
        var tensor = new DenseTensor<float>(features, new[] { 1, features.Length });
        
        // 2. Run inference
        var inputs = new List<NamedOnnxValue>
        {
            NamedOnnxValue.CreateFromTensor("input", tensor)
        };
        
        using var results = _session.Run(inputs);
        
        // 3. Extract output
        var output = results.First().AsEnumerable<float>().ToArray();
        return output;
    }
}
```

### Priority 6: Python Runner Service

**Purpose**: Call Python scripts for model retraining

**Implementation**:
```csharp
using System.Diagnostics;

public class PythonRunnerService
{
    public async Task<string> RunPythonScriptAsync(string scriptPath, string arguments)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = "python",
            Arguments = $"{scriptPath} {arguments}",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        
        using var process = new Process { StartInfo = startInfo };
        process.Start();
        
        var output = await process.StandardOutput.ReadToEndAsync();
        var error = await process.StandardError.ReadToEndAsync();
        
        await process.WaitForExitAsync();
        
        if (process.ExitCode != 0)
            throw new Exception($"Python script failed: {error}");
        
        return output;
    }
}
```

## Verification Process

### 1. Unit Testing

Create tests to verify ported logic matches Python:

```csharp
[Fact]
public void TestBongDuongMatches Python()
{
    // Test all mappings
    Assert.Equal('5', LotteryUtils.GetBongDuong('0'));
    Assert.Equal('6', LotteryUtils.GetBongDuong('1'));
    // ... all 10 mappings
}

[Fact]
public void TestStlGenerationMatchesPython()
{
    var result = LotteryUtils.CreateStlWithShadow(1, 2);
    Assert.Equal(new[] { "12", "21" }, result);
    
    result = LotteryUtils.CreateStlWithShadow(3, 3);
    Assert.Equal(new[] { "33", "88" }, result); // 3's shadow is 8
}
```

### 2. Integration Testing

Compare outputs with Python on same input data:

```csharp
[Fact]
public async Task ScannerOutputMatchesPythonAsync()
{
    // 1. Load test data
    var testData = LoadTestLotteryData();
    
    // 2. Run C# scanner
    var scanner = new ScannerService(mockRepo);
    var result = await scanner.ScanBridgesAsync(testData);
    
    // 3. Load Python output
    var pythonOutput = LoadPythonScanResult("test_scan_output.json");
    
    // 4. Compare
    Assert.Equal(pythonOutput.Count, result.Candidates.Count);
    foreach (var (expected, actual) in pythonOutput.Zip(result.Candidates))
    {
        Assert.Equal(expected.Name, actual.Name);
        Assert.Equal(expected.Streak, actual.Streak, tolerance: 0);
        Assert.Equal(expected.WinRate, actual.GetPrimaryRate(), tolerance: 0.1);
    }
}
```

### 3. Performance Benchmarking

```csharp
[Fact]
public void ScannerPerformanceBenchmark()
{
    var testData = LoadLargeDataset(1000); // 1000 lottery results
    var scanner = new ScannerService(mockRepo);
    
    var sw = Stopwatch.StartNew();
    var result = await scanner.ScanBridgesAsync(testData);
    sw.Stop();
    
    // Python takes ~5 seconds for same dataset
    // C# should be < 1.5 seconds (3x+ faster)
    Assert.True(sw.ElapsedMilliseconds < 1500, 
        $"Scanning took {sw.ElapsedMilliseconds}ms (expected < 1500ms)");
}
```

## Common Patterns

### Python List Comprehension → LINQ

```python
# Python
lotos = [loto for loto in getAllLotos(row) if loto and len(loto) == 2]
```

```csharp
// C#
var lotos = GetAllLotos(row)
    .Where(loto => !string.IsNullOrEmpty(loto) && loto.Length == 2)
    .ToList();
```

### Python Dict → C# Dictionary

```python
# Python
bridge_map = {
    "LO_FIXED_01": getCau1_STL_P5_V30_V5,
    "LO_FIXED_02": getCau2_VT1_V30_V5
}
```

```csharp
// C#
var bridgeMap = new Dictionary<string, Func<List<LotteryResult>, int, List<BridgeCandidate>>>
{
    ["LO_FIXED_01"] = ScanFixedBridge01,
    ["LO_FIXED_02"] = ScanFixedBridge02
};
```

### Python Try/Except → C# Try/Catch

```python
# Python
try:
    value = int(string_val)
except (ValueError, TypeError):
    value = 0
```

```csharp
// C#
int value;
if (!int.TryParse(stringVal, out value))
    value = 0;
```

## Next Steps

1. **Week 1**: Complete remaining fixed bridges (14 bridges)
2. **Week 2**: Port V17 shadow bridge scanning
3. **Week 3**: Port DE bridge scanning modules
4. **Week 4**: Complete DE analytics and tiered scoring
5. **Week 5**: AI integration and Python runner
6. **Week 6**: Testing and validation

## Resources

- [C# Coding Conventions](https://docs.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [Entity Framework Core Documentation](https://docs.microsoft.com/en-us/ef/core/)
- [WPF Tutorial](https://docs.microsoft.com/en-us/dotnet/desktop/wpf/)
- [MVVM Pattern in WPF](https://docs.microsoft.com/en-us/archive/msdn-magazine/2009/february/patterns-wpf-apps-with-the-model-view-viewmodel-design-pattern)

## Support

For questions about the migration, refer to:
- Python source code comments
- This migration guide
- C# XML documentation in the codebase
