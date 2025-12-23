# C# Migration Guide - XS-DAS

## Phase 1: Foundation Complete ✅

This document tracks the migration progress from Python to C# .NET 8 WPF.

## Completed Tasks

### 1. Project Setup & Infrastructure ✅
- [x] Created solution structure (XsDas.sln)
- [x] Created Core project (domain logic)
- [x] Created Infrastructure project (data access)
- [x] Created App project (WPF UI)
- [x] Created Test project (xUnit)
- [x] Added all necessary NuGet packages
- [x] Setup EF Core with SQLite
- [x] Configured dependency injection

### 2. Database Layer ✅
- [x] Created LotteryResult model (maps to results_A_I table)
- [x] Created Bridge model (maps to ManagedBridges table)
- [x] Created LotteryDbContext with proper configuration
- [x] Implemented generic Repository pattern
- [x] Configured EF Core migrations support

### 3. Core Utilities ✅
- [x] Ported shadow mapping (BongDuongV30)
- [x] Ported STL pair generation (CreateStlBongPair)
- [x] Ported loto extraction (GetAllLotos)
- [x] Ported hit checking (CheckHitStlPair)
- [x] Added Vietnamese text normalization
- [x] Added validation helpers
- [x] Added win rate formatting

### 4. Bridge Scanning ✅ (Partial)
- [x] Created ScannerService infrastructure
- [x] Ported Cau1 (STL P5 V30) algorithm
- [x] Ported Cau2 (VT1 V30) algorithm
- [x] Ported Cau3 (VT2 V30) algorithm
- [x] Ported Cau4 (G2+G3) algorithm
- [x] Implemented backtest framework
- [ ] Remaining 11 bridge algorithms (Phase 2)

### 5. WPF UI Foundation ✅
- [x] Created MainWindow with Material Design
- [x] Added navigation tabs (Dashboard, Bridges, Settings)
- [x] Setup dependency injection for WPF
- [x] Configured app startup with database initialization
- [x] Added status bar and header

### 6. Testing Infrastructure ✅
- [x] Created test project
- [x] Wrote 38 unit tests for LotteryUtils
- [x] All tests passing (100% success rate)
- [x] Setup test automation

## Python to C# Mapping

### Core Logic Mapping

| Python Function | C# Method | Notes |
|----------------|-----------|-------|
| `BONG_DUONG_V30` | `BongDuongV30` dict | Shadow mapping dictionary |
| `getBongDuong_V30()` | `GetBongDuong()` | Shadow digit lookup |
| `taoSTL_V30_Bong()` | `CreateStlBongPair()` | STL pair generation |
| `getAllLoto_V30()` | `GetAllLotos()` | Extract lotos from row |
| `checkHitSet_V30_K2N()` | `CheckHitStlPair()` | Hit checking logic |
| `normalize_vietnamese()` | `NormalizeVietnamese()` | Text normalization |

### Bridge Algorithms Mapping

| Python Function | C# Method | Status |
|----------------|-----------|--------|
| `getCau1_STL_P5_V30_V5()` | `ScanCau1StlP5()` | ✅ Done |
| `getCau2_VT1_V30_V5()` | `ScanCau2Vt1()` | ✅ Done |
| `getCau3_VT2_V30_V5()` | `ScanCau3Vt2()` | ✅ Done |
| `getCau4_G2_1_G3_1_V30_V5()` | `ScanCau4G2G3()` | ✅ Done |
| Remaining 11 algorithms | TBD | ⏳ Phase 2 |

### Database Models Mapping

| Python Table/Class | C# Entity | Properties |
|-------------------|-----------|------------|
| `DuLieu_AI` | `LotteryResult` | Mapped to results_A_I |
| `results_A_I` | `LotteryResult` | Id, Ky, Date, Gdb-G7, L0-L26 |
| `ManagedBridges` | `Bridge` | All columns including K1N/K2N rates |

## Remaining Work

### Phase 2: Complete Core Logic (Estimated: 2-3 days)

#### Bridge Algorithms
- [ ] Port remaining 11 fixed bridge algorithms
- [ ] Implement V17/Bong bridge scanning
- [ ] Implement Memory bridge (Bạc Nhớ) scanning
- [ ] Implement DE bridge scanning algorithms
- [ ] Add parallel processing support

#### Analytics Services
- [ ] Create DeAnalysisService
- [ ] Port dashboard analytics logic
- [ ] Implement scoring algorithms
- [ ] Add trend analysis

#### Backtester
- [ ] Port backtester core logic
- [ ] Implement K1N backtesting
- [ ] Implement K2N backtesting
- [ ] Add performance metrics calculation

### Phase 3: AI Model Integration (Estimated: 2 days)

- [ ] Convert .joblib model to .onnx format
- [ ] Create AiService class
- [ ] Implement feature extraction (14 features)
- [ ] Test predictions vs Python output
- [ ] Add model loading/caching
- [ ] Implement prediction confidence scoring

### Phase 4: UI Development (Estimated: 3-4 days)

#### Dashboard View
- [ ] Create DashboardView.xaml
- [ ] Create DashboardViewModel
- [ ] Implement bridge scoring table
- [ ] Add real-time updates
- [ ] Implement async data loading with spinner

#### Bridge Management View
- [ ] Create BridgeManagementView.xaml
- [ ] Create BridgeManagementViewModel
- [ ] Implement bridge list DataGrid
- [ ] Add enable/disable functionality
- [ ] Add import/export features

#### Settings View
- [ ] Create SettingsView.xaml
- [ ] Create SettingsViewModel
- [ ] Add threshold configuration
- [ ] Add algorithm selection
- [ ] Add database management tools

### Phase 5: Background Services (Estimated: 1-2 days)

- [ ] Implement auto-pruning service (IHostedService)
- [ ] Implement background backtesting
- [ ] Add scheduled data refresh
- [ ] Implement notification system

### Phase 6: Testing & Validation (Ongoing)

- [ ] Write integration tests
- [ ] Write UI tests
- [ ] Validate against Python results
- [ ] Performance benchmarking
- [ ] Memory profiling

### Phase 7: Documentation & Finalization (Estimated: 1 day)

- [ ] Complete API documentation
- [ ] Write user guide
- [ ] Create deployment guide
- [ ] Performance optimization
- [ ] Code cleanup and refactoring

## Code Style Guidelines

### Naming Conventions
- **Classes**: PascalCase (e.g., `LotteryResult`)
- **Methods**: PascalCase (e.g., `GetAllLotos()`)
- **Properties**: PascalCase (e.g., `WinRate`)
- **Private fields**: camelCase with underscore (e.g., `_context`)
- **Constants**: PascalCase (e.g., `BongDuongV30`)

### Async/Await
- All database operations use async/await
- UI operations that take >100ms should be async
- Use `Task<T>` for async methods

### Error Handling
- Use try-catch for expected exceptions
- Log errors appropriately
- Provide user-friendly error messages

### Comments
- Use XML documentation comments for public APIs
- Include Vietnamese terms where relevant for context
- Keep comments concise and meaningful

## Testing Strategy

### Unit Tests
- Test all utility functions
- Test business logic in isolation
- Aim for 80%+ code coverage

### Integration Tests
- Test database operations
- Test service interactions
- Test end-to-end workflows

### UI Tests
- Test ViewModel logic
- Test data binding
- Manual UI testing for UX

## Performance Goals

- **Startup time**: < 2 seconds
- **Database queries**: < 100ms for typical operations
- **Bridge scanning**: < 5 seconds for 100 periods
- **Memory usage**: < 200MB typical
- **UI responsiveness**: 60 FPS, no freezing

## Migration Notes

### Key Differences from Python

1. **Type Safety**: C# is statically typed - caught many potential bugs during compilation
2. **Async/Await**: More explicit async handling in C#
3. **LINQ**: Powerful query syntax replaces many Python list comprehensions
4. **Parallel Processing**: Built-in `Parallel.ForEach` for performance
5. **Property Binding**: WPF data binding is different from Tkinter

### Challenges Overcome

1. **Vietnamese Text**: Handled with proper Unicode normalization
2. **Database Schema**: Mapped nullable columns properly
3. **Material Design**: Integrated theme successfully
4. **Dependency Injection**: Setup proper DI container for WPF

## Contact & Support

For questions about the migration, refer to the original Python codebase documentation or consult the development team.
