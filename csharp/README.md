# XsDas - C# Migration

C# implementation of the Lottery Analytics System (XS-DAS) migrated from Python.

## Overview

This is a .NET 8.0 application using:
- **Clean Architecture** (Core/Infrastructure/App layers)
- **EF Core 8.0** with SQLite for data persistence
- **WPF** with MVVM pattern for UI
- **ONNX Runtime** for AI inference
- **IHostedService** for background tasks

## Project Structure

```
csharp/
├── XsDas.Core/               # Domain models, interfaces, business logic
│   ├── Models/              # Entity models (LotteryResult, ManagedBridge, DuLieuAi)
│   ├── Interfaces/          # Repository and service interfaces
│   └── Utils/               # Core utility functions (LotteryUtils)
├── XsDas.Infrastructure/     # Data access and external services
│   ├── Data/                # EF Core DbContext and repositories
│   ├── Services/            # Business services (ScannerService, AiService)
│   └── Background/          # Background services (Auto-pruning, Backtesting)
├── XsDas.App/               # WPF presentation layer
│   ├── Views/               # XAML views
│   └── ViewModels/          # View models with MVVM pattern
└── XsDas.Core.Tests/        # Unit tests
    └── Utils/               # Tests for utility functions
```

## Getting Started

### Prerequisites

- .NET 8.0 SDK or later
- Visual Studio 2022 / VS Code / Rider (optional)
- Existing Python SQLite database (xo_so_prizes_all_logic.db)

### Build

```bash
cd csharp
dotnet restore
dotnet build
```

### Run Tests

```bash
dotnet test --verbosity normal
```

Current test results: **12/12 tests passing** ✅

### Run Application

```bash
cd XsDas.App
dotnet run
```

## Database Compatibility

The C# implementation uses the same SQLite database schema as the Python version:

- **results_A_I** - Lottery results (100% compatible)
- **ManagedBridges** - Managed bridge configuration with K1N/K2N rates (V11.2)
- **DuLieu_AI** - AI training data (100% compatible)

All column names, types, and constraints match the Python schema exactly.

## Core Features Implemented

### Phase 1: Foundation ✅ (Complete)

- [x] EF Core DbContext with SQLite provider
- [x] Entity models: LotteryResult, ManagedBridge, DuLieuAi
- [x] Repository pattern with generic implementation
- [x] Core utility functions:
  - GetBongDuong - Shadow digit mapping
  - TaoStlV30Bong - STL pair generation
  - GetAllLotoV30 - Extract lottery numbers
  - CheckHitSetV30K2N - Hit detection
  - NormalizeVietnamese - Text normalization
  - FormatWinRate, IsValidLoto, IsValidKy - Helpers
- [x] 12 passing unit tests

### Phase 2: Core Logic (In Progress)

- [ ] ScannerService with 15 bridge types
- [ ] Bridge algorithms (classic, memory, V16)
- [ ] Backtesting engine
- [ ] Analytics service

### Phase 3: AI Integration (Planned)

- [ ] Python script for .joblib to .onnx conversion
- [ ] AiService with ONNX Runtime
- [ ] Model loading and inference
- [ ] Feature extraction

### Phase 4: WPF UI (Planned)

- [ ] MainWindow with navigation
- [ ] DashboardView with DataGrid
- [ ] MVVM view models
- [ ] Data binding
- [ ] Scanner interaction UI

### Phase 5: Background Services (Planned)

- [ ] Auto-Pruning service (IHostedService)
- [ ] Backtesting engine service
- [ ] Configuration and scheduling
- [ ] Logging and monitoring

## Performance

Expected performance improvements over Python:

- **3-5x faster** core algorithms (LINQ, parallel processing)
- **Lower memory** usage with lazy loading
- **Better concurrency** with async/await
- **Faster startup** time

## Migration Status

| Component | Python LOC | C# LOC | Status |
|-----------|-----------|---------|---------|
| EF Core & Models | - | 500+ | ✅ Complete |
| Core Utils | 80 | 250 | ✅ Complete |
| Repository Pattern | - | 150 | ✅ Complete |
| Bridge Scanners | 500+ | - | 🔄 Planned |
| AI Service | 300+ | - | 🔄 Planned |
| WPF UI | 2000+ | - | 🔄 Planned |
| Background Services | 200+ | - | 🔄 Planned |
| **Total** | **~5000** | **900+** | **20% Complete** |

## Testing

The test suite validates:

1. **Shadow Mapping** - All 10 digit mappings (0-9 → 5-4)
2. **STL Generation** - Duplicate and different digit pairs
3. **Lotto Extraction** - Prize parsing from database rows
4. **Hit Detection** - Win/loss checking with K2N simulation
5. **Vietnamese Normalization** - Diacritic removal and ASCII conversion
6. **Validation** - Lotto and period identifier validation

Run tests with coverage:
```bash
dotnet test --collect:"XPlat Code Coverage"
```

## Contributing

This is a migration project. When adding new features:

1. Keep 100% compatibility with Python SQLite schema
2. Match Python algorithm behavior exactly
3. Add unit tests for all new functionality
4. Follow Clean Architecture principles
5. Use async/await for I/O operations

## License

Same as parent Python project.

## Related Documentation

- [Migration Guide](../DOC/K1N_MIGRATION_GUIDE.md) - Python V11.2 migration details
- [Python README](../README.md) - Original Python implementation
- [Implementation Roadmap](../DOC/IMPLEMENTATION_ROADMAP.md) - Overall project roadmap
