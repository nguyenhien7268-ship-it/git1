# XsDas - C# .NET 8 WPF Migration

**Lottery Analytics System - C# Implementation**

## Overview

This is the C# .NET 8 WPF migration of the XS-DAS (Xổ Số Data Analysis System) Python application. The project follows Clean Architecture principles with MVVM pattern for the UI layer.

## Architecture

### Clean Architecture Layers

```
XsDas.sln
├── XsDas.Core              # Domain models, interfaces, business logic
│   ├── Models/             # Entity models (LotteryResult, ManagedBridge, etc.)
│   ├── Interfaces/         # Repository interfaces
│   └── Utils/              # Core utility functions (LotteryUtils)
│
├── XsDas.Infrastructure    # Data access, external services
│   ├── Data/               # EF Core DbContext, Repository implementations
│   ├── Services/           # Scanner service, AI service
│   └── Background/         # Background services (IHostedService)
│
├── XsDas.App              # WPF UI Layer (MVVM)
│   ├── ViewModels/         # ViewModels with CommunityToolkit.Mvvm
│   ├── Views/              # XAML views (MainWindow, Dashboard, etc.)
│   └── Services/           # UI-specific services
│
└── XsDas.Core.Tests       # Unit tests
    └── Utils/              # Utility function tests (38+ tests)
```

## Technology Stack

- **.NET 8**: Target framework
- **WPF**: Desktop UI framework
- **Entity Framework Core 8.0**: ORM for database access
- **SQLite**: Database engine (compatible with Python version)
- **Material Design**: Modern UI components
- **CommunityToolkit.Mvvm**: MVVM framework
- **Microsoft.ML.OnnxRuntime**: AI/ML inference
- **xUnit**: Unit testing framework

## Features Implemented

### Phase 1: Foundation ✅
- [x] Clean Architecture solution structure
- [x] EF Core 8.0 with SQLite configuration
- [x] Entity models (LotteryResult, ManagedBridge, DuLieuAi)
- [x] LotteryDbContext with proper mappings
- [x] Generic repository pattern
- [x] Core utility functions (LotteryUtils)
- [x] 57 passing unit tests (100% core utils coverage)

### Phase 2: Core Logic (In Progress)
- [ ] Bridge scanning algorithms (15 classic bridges)
- [ ] ScannerService implementation
- [ ] Backtesting engine
- [ ] Analytics service
- [ ] Additional unit tests

### Phase 3: AI Integration (Planned)
- [ ] ONNX model conversion from .joblib
- [ ] AiService with OnnxRuntime
- [ ] Feature extraction
- [ ] Prediction pipeline

### Phase 4: UI Development (Planned)
- [ ] MainWindow with Material Design
- [ ] Dashboard view with data grids
- [ ] Scanner view
- [ ] Bridge Manager view
- [ ] Settings view
- [ ] MVVM ViewModels

### Phase 5: Finalization (Planned)
- [ ] Auto-pruning background service
- [ ] Async operations with progress feedback
- [ ] Performance optimization
- [ ] Integration tests
- [ ] Documentation

## Getting Started

### Prerequisites

- .NET 8 SDK or later
- Visual Studio 2022 or VS Code with C# extension
- SQLite database file from Python version (optional)

### Build

```bash
cd csharp
dotnet restore
dotnet build --configuration Release
```

### Run Tests

```bash
cd csharp
dotnet test --configuration Release
```

**Test Results:**
```
Total tests: 57
Passed: 57 (100%)
Failed: 0
Time: < 1 second
```

### Run Application

```bash
cd csharp
dotnet run --project XsDas.App
```

## Key Components

### LotteryUtils

Core utility class with lottery-specific functions:

- **Shadow Mapping (Bóng Dương)**: Maps digits to complements (0↔5, 1↔6, etc.)
- **STL Pair Generation**: Creates lottery number pairs with shadow logic
- **Loto Extraction**: Extracts all 2-digit numbers from prize data
- **Hit Detection**: Checks if lottery pairs hit in results (K2N mode)
- **Vietnamese Normalization**: Converts Vietnamese text to ASCII
- **Win Rate Formatting**: Formats statistics as percentages
- **Validation**: Input validation for loto numbers and Ky identifiers

### Entity Models

- **LotteryResult**: Lottery drawing results (results_A_I table)
- **ManagedBridge**: Bridge strategy configurations (ManagedBridges table)
- **DuLieuAi**: AI data storage (DuLieu_AI table)

### Database

Uses SQLite with EF Core migrations. Compatible with the Python version's database schema including:
- K1N/K2N rate columns (V11.2 update)
- Pin/pending flags
- Search rate tracking
- Position indices for backtesting

## Performance Targets

- **3-5x faster** than Python implementation
- **50-80% reduction** in database queries (caching)
- **15-30% reduction** in memory usage
- **Sub-second** UI response times

## Migration Notes

### Ported from Python

The C# implementation maintains API compatibility with the Python version:

- `logic/utils.py` → `XsDas.Core/Utils/LotteryUtils.cs`
- `logic/db_manager.py` → `XsDas.Infrastructure/Data/LotteryDbContext.cs`
- `logic/bridges/` → `XsDas.Infrastructure/Services/ScannerService.cs`

### Improvements

- **Type Safety**: Full type checking with nullable reference types
- **Async/Await**: Asynchronous operations throughout
- **LINQ**: Efficient data queries
- **Dependency Injection**: Built-in DI container
- **Modern UI**: Material Design WPF components

## Testing Strategy

### Unit Tests (57 tests)

Comprehensive coverage of core utilities:
- Shadow mapping (11 tests)
- STL pair generation (8 tests)
- Loto extraction (4 tests)
- Hit detection (6 tests)
- Vietnamese normalization (5 tests)
- Win rate formatting (7 tests)
- Validation (16 tests)

### Integration Tests (Planned)

- Database operations
- End-to-end workflows
- UI interactions

## Contributing

This is a migration project. Changes should:
1. Maintain compatibility with Python database schema
2. Follow C# coding conventions
3. Include unit tests
4. Update documentation

## License

Same as the Python version.

## Status

**Current Version**: 0.1.0-alpha  
**Migration Progress**: Phase 1 Complete (20%)  
**Next Milestone**: Core Logic Implementation (Phase 2)

Last Updated: December 11, 2024
