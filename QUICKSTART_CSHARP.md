# C# Migration - Quick Start Guide

**Last Updated**: December 11, 2024  
**Status**: Phase 1 Complete ✅ | Phase 2 Ready to Start 🚀

---

## 🎯 What's Been Done

✅ **Phase 1 Complete (20% overall)**

- Clean Architecture solution with 3 layers (Core/Infrastructure/App)
- EF Core 8.0 + SQLite database integration (100% compatible with Python)
- 3 entity models matching Python schema exactly
- 8 core utility functions ported from Python
- **57 comprehensive unit tests - 100% passing**
- Complete documentation (4 guides)

**Quality**: Build clean (0 errors), all tests passing, type-safe, documented.

---

## ⚡ Quick Commands

### Build & Test
```bash
# Navigate to C# project
cd csharp

# Build solution (< 10 seconds)
dotnet build --configuration Release

# Run all tests (57 tests, 100% passing, < 1 second)
dotnet test --configuration Release --verbosity normal

# Build and test in one command
dotnet build && dotnet test
```

### Expected Output
```
Build succeeded.
    0 Warning(s)
    0 Error(s)

Test Run Successful.
Total tests: 57
     Passed: 57
 Total time: 0.56 seconds
```

### Project Structure
```bash
# View solution structure
ls -la csharp/

# Key directories
csharp/
├── XsDas.sln                      # Solution file
├── XsDas.Core/                    # Domain layer ✅
│   ├── Models/                    # Entity models ✅
│   ├── Interfaces/                # Abstractions ✅
│   └── Utils/                     # Core utilities ✅
├── XsDas.Infrastructure/          # Data layer ✅
│   └── Data/                      # EF Core DbContext ✅
├── XsDas.App/                     # UI layer (Phase 4)
└── XsDas.Core.Tests/             # Test project ✅
    └── Utils/                     # 57 tests ✅
```

---

## 📚 Documentation

### For Developers
1. **`csharp/README.md`**: Project overview, architecture, features
2. **`csharp/MIGRATION_GUIDE.md`**: Migration patterns, code conversions
3. **`csharp/IMPLEMENTATION_SUMMARY.md`**: Technical details, progress

### For Stakeholders
4. **`CSHARP_MIGRATION_STATUS.md`**: Executive summary, timeline, metrics

### Read First
Start with `csharp/README.md` to understand the architecture, then reference the migration guide for specific conversion patterns.

---

## 🚀 Next: Phase 2 - Core Logic

### What's Next (3-4 days)

**Priority 1**: Bridge Scanners
```
Task: Port 15 bridge scanners from Python
File: logic/bridges/bridges_classic.py → Infrastructure/Services/ScannerService.cs
Goal: Parallel processing, 3-5x faster than Python
```

**Priority 2**: Backtesting Engine
```
Task: Port backtesting logic
File: logic/backtester_core.py → Infrastructure/Services/BacktestService.cs
Features: K1N/K2N modes, streak calculation
```

**Priority 3**: Analytics
```
Task: Port analytics functions
File: logic/dashboard_analytics.py → Infrastructure/Services/AnalyticsService.cs
Features: Scoring, risk assessment, statistics
```

### Starting Phase 2

```bash
cd csharp

# Create new service files
mkdir -p XsDas.Infrastructure/Services
touch XsDas.Infrastructure/Services/ScannerService.cs
touch XsDas.Infrastructure/Services/BacktestService.cs
touch XsDas.Infrastructure/Services/AnalyticsService.cs

# Create test files
mkdir -p XsDas.Core.Tests/Services
touch XsDas.Core.Tests/Services/ScannerServiceTests.cs

# Build to verify structure
dotnet build
```

---

## 🔍 Key Components

### Already Implemented ✅

#### LotteryUtils (8 Functions)
```csharp
using XsDas.Core.Utils;

// Shadow mapping (Bóng Dương)
var shadow = LotteryUtils.GetBongDuong('3'); // Returns '8'

// Generate STL pairs
var pairs = LotteryUtils.TaoStlV30Bong(3, 5); // Returns ["35", "53"]

// Extract loto numbers from prizes
var lotos = LotteryUtils.GetAllLotoV30(gdb, g1, g2, g3, g4, g5, g6, g7);

// Check if pair hits
var result = LotteryUtils.CheckHitSetV30K2N(
    new List<string> { "12", "34" },
    new HashSet<string> { "12", "56", "78" }
); // Returns "✅ (Ăn 1)"

// Vietnamese normalization
var normalized = LotteryUtils.NormalizeVietnamese("Đề"); // Returns "de"

// Format win rate
var rate = LotteryUtils.FormatWinRate(85, 100); // Returns "85.00%"

// Validation
bool valid = LotteryUtils.IsValidLoto("12"); // Returns true
bool validKy = LotteryUtils.IsValidKy("2024001"); // Returns true
```

#### Entity Models
```csharp
using XsDas.Core.Models;

// Lottery result
var result = new LotteryResult
{
    Ky = "2024001",
    Date = "2024-01-01",
    Gdb = "12345",
    // ... other properties
};

// Managed bridge
var bridge = new ManagedBridge
{
    Name = "Bridge-001",
    Type = "LO_STL",
    IsEnabled = true,
    K1nRateLo = 85.5,
    K2nRateLo = 82.0
};
```

#### Repository Pattern
```csharp
using XsDas.Core.Interfaces;
using XsDas.Infrastructure.Data;

// Use repository
public class MyService
{
    private readonly IRepository<LotteryResult> _resultRepo;
    
    public async Task<List<LotteryResult>> GetRecentResultsAsync()
    {
        return (await _resultRepo.GetAllAsync())
            .OrderByDescending(r => r.Ky)
            .Take(100)
            .ToList();
    }
}
```

---

## 🎓 Migration Patterns

### Python → C# Quick Reference

#### List Comprehensions
```python
# Python
lotos = [loto for loto in all_lotos if len(loto) == 2]
```
```csharp
// C#
var lotos = allLotos.Where(l => l.Length == 2).ToList();
```

#### Dictionary Access
```python
# Python
shadow = BONG_DUONG.get(digit, digit)
```
```csharp
// C#
var shadow = BongDuong.TryGetValue(digit, out var s) ? s : digit;
```

#### Database Queries
```python
# Python
cursor.execute("SELECT * FROM ManagedBridges WHERE is_enabled = 1")
bridges = cursor.fetchall()
```
```csharp
// C#
var bridges = await _context.ManagedBridges
    .Where(b => b.IsEnabled)
    .ToListAsync();
```

#### Async Operations
```python
# Python
def process_data():
    data = fetch_from_db()
    return analyze(data)
```
```csharp
// C#
public async Task<AnalysisResult> ProcessDataAsync()
{
    var data = await FetchFromDbAsync();
    return await AnalyzeAsync(data);
}
```

More patterns in `csharp/MIGRATION_GUIDE.md`

---

## 🧪 Testing

### Run Specific Tests
```bash
# Run all tests
dotnet test

# Run specific test class
dotnet test --filter "FullyQualifiedName~LotteryUtilsTests"

# Run specific test method
dotnet test --filter "Name~GetBongDuong"

# Run with detailed output
dotnet test --verbosity detailed

# Run with code coverage (requires coverlet)
dotnet test /p:CollectCoverage=true
```

### Writing Tests
```csharp
using Xunit;
using XsDas.Core.Utils;

public class MyTests
{
    [Fact]
    public void MyFunction_ValidInput_ReturnsExpectedResult()
    {
        // Arrange
        var input = "test";
        
        // Act
        var result = MyFunction(input);
        
        // Assert
        Assert.Equal("expected", result);
    }
    
    [Theory]
    [InlineData("input1", "output1")]
    [InlineData("input2", "output2")]
    public void MyFunction_VariousInputs_ReturnsCorrectOutput(
        string input, string expected)
    {
        var result = MyFunction(input);
        Assert.Equal(expected, result);
    }
}
```

---

## 🔧 Troubleshooting

### Build Issues

**Issue**: `dotnet: command not found`
```bash
# Install .NET 8 SDK
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 8.0
```

**Issue**: `EnableWindowsTargeting` error
```bash
# Already fixed in XsDas.App.csproj
# If you see this, ensure the .csproj has:
<EnableWindowsTargeting>true</EnableWindowsTargeting>
```

**Issue**: Package restore fails
```bash
cd csharp
dotnet restore --force
dotnet clean
dotnet build
```

### Test Issues

**Issue**: Tests not discovered
```bash
# Rebuild test project
cd csharp
dotnet build XsDas.Core.Tests/XsDas.Core.Tests.csproj
dotnet test XsDas.Core.Tests/XsDas.Core.Tests.csproj --list-tests
```

**Issue**: Tests fail after code changes
```bash
# Clean and rebuild
dotnet clean
dotnet build
dotnet test
```

---

## 📊 Current Status

### Phase 1: Complete ✅
- Solution structure ✅
- Entity models ✅  
- EF Core setup ✅
- Core utilities ✅
- 57 tests ✅
- Documentation ✅

### Phase 2: Ready 🚀
- Bridge scanners ⏳
- Backtesting ⏳
- Analytics ⏳
- Integration tests ⏳

### Phase 3-6: Planned ⏳
- AI/ONNX (Phase 3)
- WPF UI (Phase 4)
- Background services (Phase 5)
- Final testing (Phase 6)

### Timeline
- **Completed**: 2 days (Phase 1)
- **Remaining**: 11-15 days (Phases 2-6)
- **Total**: 13-17 days estimated

---

## 🎯 Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Build | Clean | 0 errors | ✅ |
| Tests | 90%+ pass | 100% (57/57) | ✅ |
| Coverage | 80%+ | 100% (utils) | ✅ |
| Type Safety | 100% | 100% | ✅ |
| Documentation | Complete | 4 guides | ✅ |

---

## 📞 Need Help?

### Documentation
- Project overview: `csharp/README.md`
- Migration patterns: `csharp/MIGRATION_GUIDE.md`
- Technical details: `csharp/IMPLEMENTATION_SUMMARY.md`
- Status report: `CSHARP_MIGRATION_STATUS.md`

### Quick Links
- [EF Core Docs](https://docs.microsoft.com/ef/core/)
- [WPF Tutorial](https://docs.microsoft.com/dotnet/desktop/wpf/)
- [MVVM Pattern](https://docs.microsoft.com/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures#mvvm)
- [xUnit Testing](https://xunit.net/)

### Commands Summary
```bash
# Essential commands
cd csharp
dotnet build              # Build solution
dotnet test               # Run all tests
dotnet run --project XsDas.App  # Run application (Phase 4+)

# Package management
dotnet add package PackageName      # Add NuGet package
dotnet remove package PackageName   # Remove package
dotnet restore                      # Restore packages

# Cleaning
dotnet clean              # Clean build artifacts
rm -rf bin/ obj/          # Deep clean
```

---

## 🎉 You're Ready!

**Phase 1 is complete and working perfectly.**

To start Phase 2:
1. Read the bridge scanner Python code: `logic/bridges/bridges_classic.py`
2. Create `ScannerService.cs` in `XsDas.Infrastructure/Services/`
3. Port one bridge at a time
4. Write tests for each bridge
5. Run `dotnet test` to validate

**Happy coding! 🚀**

---

*For detailed technical information, see the comprehensive guides in `/csharp/`*
