# C# Migration Guide

## Migration Strategy

This guide explains the migration approach from Python to C# .NET 8 WPF.

## Architecture Mapping

### Python → C# Project Structure

```
Python (Original)              →  C# (.NET 8)
─────────────────────────────────────────────────────────────
logic/                         →  XsDas.Core/
├── utils.py                   →  Utils/LotteryUtils.cs
├── models.py                  →  Models/
├── db_manager.py              →  Infrastructure/Data/
└── bridges/                   →  Infrastructure/Services/

ui/                            →  XsDas.App/
├── ui_main_window.py          →  Views/MainWindow.xaml
├── ui_dashboard.py            →  Views/DashboardView.xaml
└── ui_*.py                    →  Views/*.xaml

tests/                         →  XsDas.Core.Tests/
└── test_*.py                  →  *Tests.cs
```

### Technology Mapping

| Python | C# Equivalent | Notes |
|--------|--------------|-------|
| SQLite3 | EF Core + SQLite | ORM-based, type-safe |
| Tkinter | WPF | Modern, hardware-accelerated UI |
| pandas | LINQ | Integrated into C# |
| numpy | LINQ + Math | Built-in or System.Numerics |
| scikit-learn (joblib) | ML.NET or ONNX | Model conversion required |
| unittest/pytest | xUnit | Industry standard for .NET |

## Phase-by-Phase Migration

### Phase 1: Foundation ✅ COMPLETED

**Duration**: 2 days  
**Status**: ✅ Complete

**What was done:**
1. Created Clean Architecture solution
2. Set up EF Core with SQLite
3. Defined entity models (LotteryResult, ManagedBridge, DuLieuAi)
4. Implemented LotteryDbContext with column mappings
5. Created generic Repository pattern
6. Ported core utilities (LotteryUtils)
7. Wrote 57 comprehensive unit tests

**Verification:**
```bash
cd csharp
dotnet build
dotnet test
# All 57 tests passing ✅
```

### Phase 2: Core Logic (Current)

**Duration**: 3-4 days  
**Status**: 🚧 In Progress

**Tasks:**
1. Port 15 classic bridge scanners from `bridges_classic.py`
2. Implement `ScannerService.cs` with async methods
3. Create backtesting engine
4. Port analytics functions
5. Write integration tests

**Python files to port:**
- `logic/bridges/bridges_classic.py` (15 fixed bridges)
- `logic/backtester_core.py` (core backtesting logic)
- `logic/analytics.py` (statistical analysis)

**Key considerations:**
- Use `Parallel.ForEach` for performance (3-5x speedup)
- Async/await for database operations
- LINQ for data transformations
- Strong typing throughout

### Phase 3: AI Integration

**Duration**: 2-3 days  
**Status**: ⏳ Planned

**Tasks:**
1. Convert `.joblib` models to `.onnx` format
   ```python
   # Python conversion script
   import skl2onnx
   from skl2onnx import convert_sklearn
   from skl2onnx.common.data_types import FloatTensorType
   
   # Load model
   model = joblib.load('loto_model.joblib')
   
   # Convert to ONNX
   initial_type = [('float_input', FloatTensorType([None, n_features]))]
   onnx_model = convert_sklearn(model, initial_types=initial_type)
   
   # Save
   with open('loto_model.onnx', 'wb') as f:
       f.write(onnx_model.SerializeToString())
   ```

2. Implement `AiService.cs` with OnnxRuntime
   ```csharp
   public class AiService
   {
       private readonly InferenceSession _session;
       
       public AiService(string modelPath)
       {
           _session = new InferenceSession(modelPath);
       }
       
       public async Task<float[]> PredictAsync(float[] features)
       {
           var inputs = new List<NamedOnnxValue>
           {
               NamedOnnxValue.CreateFromTensor("input", 
                   new DenseTensor<float>(features, new[] { 1, features.Length }))
           };
           
           using var results = _session.Run(inputs);
           return results.First().AsTensor<float>().ToArray();
       }
   }
   ```

3. Port feature extraction logic
4. Test model accuracy vs Python

### Phase 4: UI Development

**Duration**: 4-5 days  
**Status**: ⏳ Planned

**Tasks:**
1. Set up Material Design theme
2. Create MainWindow layout
3. Implement Dashboard with DataGrid
4. Build Scanner view
5. Create Bridge Manager
6. Add Settings dialog
7. Implement ViewModels with MVVM

**MVVM Pattern:**
```csharp
// ViewModel example
public partial class DashboardViewModel : ObservableObject
{
    private readonly IRepository<ManagedBridge> _bridgeRepo;
    
    [ObservableProperty]
    private ObservableCollection<BridgeViewModel> _bridges;
    
    [RelayCommand]
    private async Task LoadBridgesAsync()
    {
        var bridges = await _bridgeRepo.GetAllAsync();
        Bridges = new ObservableCollection<BridgeViewModel>(
            bridges.Select(b => new BridgeViewModel(b))
        );
    }
}
```

### Phase 5: Finalization

**Duration**: 2-3 days  
**Status**: ⏳ Planned

**Tasks:**
1. Implement auto-pruning background service
   ```csharp
   public class BridgePruningService : BackgroundService
   {
       protected override async Task ExecuteAsync(CancellationToken stoppingToken)
       {
           while (!stoppingToken.IsCancellationRequested)
           {
               await PruneBadBridgesAsync();
               await Task.Delay(TimeSpan.FromHours(1), stoppingToken);
           }
       }
   }
   ```

2. Add progress indicators and spinners
3. Performance optimization
4. Integration tests
5. User documentation

## Code Conversion Patterns

### 1. Database Queries

**Python:**
```python
cursor.execute("SELECT * FROM ManagedBridges WHERE is_enabled = 1")
bridges = cursor.fetchall()
```

**C#:**
```csharp
var bridges = await _context.ManagedBridges
    .Where(b => b.IsEnabled)
    .ToListAsync();
```

### 2. List Comprehensions

**Python:**
```python
lotos = [loto for loto in all_lotos if len(loto) == 2]
```

**C#:**
```csharp
var lotos = allLotos.Where(l => l.Length == 2).ToList();
```

### 3. Dictionary Operations

**Python:**
```python
BONG_DUONG = {"0": "5", "1": "6", ...}
shadow = BONG_DUONG.get(digit, digit)
```

**C#:**
```csharp
private static readonly Dictionary<char, char> BongDuong = new()
{
    ['0'] = '5', ['1'] = '6', ...
};
var shadow = BongDuong.TryGetValue(digit, out var s) ? s : digit;
```

### 4. Async/Await

**Python:**
```python
def process_data():
    data = fetch_from_db()
    return analyze(data)
```

**C#:**
```csharp
public async Task<AnalysisResult> ProcessDataAsync()
{
    var data = await FetchFromDbAsync();
    return await AnalyzeAsync(data);
}
```

## Performance Optimizations

### 1. Parallel Processing

**Python:**
```python
results = []
for bridge in bridges:
    result = backtest_bridge(bridge)
    results.append(result)
```

**C#:**
```csharp
var results = await Task.WhenAll(
    bridges.Select(bridge => BacktestBridgeAsync(bridge))
);
```

### 2. Caching

```csharp
private readonly IMemoryCache _cache;

public async Task<List<LotteryResult>> GetRecentResultsAsync()
{
    return await _cache.GetOrCreateAsync(
        "recent_results",
        async entry =>
        {
            entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5);
            return await _context.LotteryResults
                .OrderByDescending(r => r.Ky)
                .Take(100)
                .ToListAsync();
        }
    );
}
```

### 3. Batch Operations

```csharp
// Instead of multiple single inserts
foreach (var bridge in bridges)
    await _context.ManagedBridges.AddAsync(bridge);

// Use batch insert
await _context.ManagedBridges.AddRangeAsync(bridges);
await _context.SaveChangesAsync();
```

## Testing Strategy

### Unit Tests

Cover all utility functions, business logic, and calculations:

```csharp
[Theory]
[InlineData("33", "88")]  // Kép case
[InlineData("35", "53")]  // Regular case
public void TaoStlV30Bong_VariousCases_ReturnsCorrectPairs(string input1, string input2)
{
    var result = LotteryUtils.TaoStlV30Bong(int.Parse(input1[0].ToString()), 
                                            int.Parse(input1[1].ToString()));
    Assert.Contains(input1, result);
    Assert.Contains(input2, result);
}
```

### Integration Tests

Test complete workflows:

```csharp
public class BridgeScanningIntegrationTests : IClassFixture<DatabaseFixture>
{
    [Fact]
    public async Task ScanBridges_WithRealData_ReturnsValidResults()
    {
        // Arrange
        var service = new ScannerService(_context);
        
        // Act
        var results = await service.ScanAllBridgesAsync();
        
        // Assert
        Assert.NotEmpty(results);
        Assert.All(results, r => Assert.InRange(r.WinRate, 0, 100));
    }
}
```

## Deployment

### Release Build

```bash
cd csharp
dotnet publish XsDas.App/XsDas.App.csproj -c Release -r win-x64 --self-contained
```

### Output

Single executable with all dependencies:
```
publish/
└── XsDas.App.exe  (main executable)
└── *.dll          (dependencies)
└── loto_model.onnx (AI model)
```

## Troubleshooting

### Issue: EF Core Migration Errors

**Solution:**
```bash
cd csharp/XsDas.Infrastructure
dotnet ef migrations add InitialCreate --startup-project ../XsDas.App
dotnet ef database update --startup-project ../XsDas.App
```

### Issue: ONNX Model Not Loading

**Solution:**
Ensure model file is copied to output directory. In .csproj:
```xml
<ItemGroup>
  <None Update="Models\loto_model.onnx">
    <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
  </None>
</ItemGroup>
```

### Issue: WPF Not Building on Linux

**Solution:**
Add to .csproj:
```xml
<PropertyGroup>
  <EnableWindowsTargeting>true</EnableWindowsTargeting>
</PropertyGroup>
```

## Next Steps

1. Complete Phase 2 (Core Logic)
2. Set up CI/CD pipeline
3. Create installer (MSI/MSIX)
4. Performance benchmarking vs Python
5. User acceptance testing

## Resources

- [EF Core Documentation](https://docs.microsoft.com/ef/core/)
- [WPF Tutorial](https://docs.microsoft.com/dotnet/desktop/wpf/)
- [MVVM Pattern](https://docs.microsoft.com/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures#mvvm)
- [ML.NET](https://dotnet.microsoft.com/learn/ml-dotnet)
- [ONNX Runtime](https://onnxruntime.ai/)
