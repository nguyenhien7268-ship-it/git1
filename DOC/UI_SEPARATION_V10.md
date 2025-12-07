# UI Refactoring V10.0: Complete Separation of Scanning and Management

## Overview

This document describes the complete separation of Bridge Scanning and Management functionality into two distinct tabs, following the Single Responsibility Principle (SRP) at the UI level.

## Motivation

Previously, the application mixed scanning (discovery) and management functions:
- A single "Bridge Manager" window handled both scanning and CRUD operations
- "Dò Tìm Cầu" button on home page created confusion about workflow
- No clear distinction between discovered bridges vs managed bridges
- Violated SRP: one component had two responsibilities

## Solution

### New Tab Structure

```
Main Window Notebook:
├── 🏠 Trang Chủ (Home)
├── 📊 Bảng Quyết Định (Dashboard)
├── 🔮 Soi Cầu Đề (DE Analysis)
├── 🔍 Dò Tìm Cầu Mới ← NEW: SCANNING ONLY
├── 🛠️ Quản Lý Cầu ← NEW: MANAGEMENT ONLY
├── 📖 Tra Cứu (Lookup)
├── 🚀 Tối Ưu Hóa (Optimizer)
└── 📝 Log Hệ Thống (System Log)
```

### Tab 1: 🔍 Dò Tìm Cầu Mới (Bridge Scanner)

**File:** `ui/ui_bridge_scanner.py`

**Purpose:** Scanning and discovery of new bridges ONLY

**Features:**
- Scan V17 Shadow bridges
- Scan Memory (Bạc Nhớ) bridges  
- Update Fixed bridges (15 cầu cố định)
- Scan DE bridges
- Display scan results in dedicated table
- Add selected/all bridges to management system

**Does NOT have:**
- Enable/Disable bridges
- Delete bridges
- Edit bridge details
- Prune/Auto-manage operations

**Imports:**
```python
from logic.bridges.lo_bridge_scanner import (
    TIM_CAU_TOT_NHAT_V16,
    TIM_CAU_BAC_NHO_TOT_NHAT,
    update_fixed_lo_bridges,
)
from logic.bridges.bridge_manager_de import find_and_auto_manage_bridges_de
```

### Tab 2: 🛠️ Quản Lý Cầu (Bridge Management)

**File:** `ui/ui_bridge_management.py`

**Purpose:** Management of existing bridges ONLY

**Features:**
- Display all managed bridges with status
- Edit form for bridge details
- Add new bridge manually
- Update bridge information
- Delete bridge
- Pin/Unpin bridge
- Enable/Disable bridge
- Smart optimization (prune bad bridges)
- Test bridge (backtest)

**Does NOT have:**
- Scan for new bridges
- Discovery functions
- Any scanning operations

**Imports:**
```python
from logic.bridges.bridge_manager_core import (
    prune_bad_bridges,
    auto_manage_bridges,
)
from logic.data_repository import get_managed_bridges_with_prediction
```

## Workflow

### Scanning Workflow

1. User opens "🔍 Dò Tìm Cầu Mới" tab
2. Selects scan type (V17, Memory, Fixed, DE, or All)
3. Clicks scan button
4. System displays results in scan results table
5. User selects bridges to add
6. Clicks "Thêm vào Quản Lý" button
7. Selected bridges are added to management system
8. Management tab refreshes automatically

### Management Workflow

1. User opens "🛠️ Quản Lý Cầu" tab
2. Views all managed bridges in table
3. Selects a bridge
4. Performs action:
   - Edit details in form
   - Toggle enable/disable
   - Pin/Unpin
   - Delete
   - Smart optimize (prune weak bridges)
5. Changes are saved to database
6. Table refreshes

## Data Separation

### Scan Results
- Stored temporarily in `BridgeScannerTab.scan_results`
- Displayed in scanner tab's results table
- Columns: Type, Name, Description, K2N Rate, Streak, Added Status
- Not persisted until user adds to management

### Managed Bridges
- Stored in database `ManagedBridges` table
- Displayed in management tab's bridges table
- Columns: ID, Name, Description, K1N, K2N, Status, Pinned, Created Date
- Full CRUD operations available

## Technical Implementation

### Files Created

1. **ui/ui_bridge_scanner.py** (458 lines)
   - `BridgeScannerTab` class
   - Scan control buttons
   - Results table
   - Action buttons
   - Threading for non-blocking scans

2. **ui/ui_bridge_management.py** (563 lines)
   - `BridgeManagementTab` class
   - Edit form
   - Management table
   - CRUD operations
   - Smart optimization

### Files Modified

1. **ui/ui_main_window.py**
   - Added imports for new tabs
   - Integrated tabs into notebook
   - Removed old "Dò Tìm Cầu" button
   - Removed old "Quản Lý Cầu" button
   - Updated button list for task manager
   - Redirected old methods to new tabs (backward compatibility)

## Backward Compatibility

Old methods are maintained but redirected:

```python
def show_bridge_manager_window(self):
    """Switches to Management tab instead of opening popup."""
    self.notebook.select(self.bridge_management_tab)

def run_auto_find_bridges(self):
    """Switches to Scanner tab instead of running scan."""
    self.notebook.select(self.bridge_scanner_tab)
```

## Benefits

1. **Clear Separation of Concerns**
   - Scanning logic isolated from management logic
   - Each tab has single responsibility

2. **Better User Experience**
   - Clear workflow: Scan → Add → Manage
   - No confusion about where to perform actions
   - Dedicated space for each function

3. **Maintainability**
   - Easy to modify scanning without affecting management
   - Easy to add new scan types
   - Clear module boundaries

4. **Testability**
   - Can test scanning independently
   - Can test management independently
   - Clear interfaces between components

## Migration Guide

### For Users

**Old Way:**
1. Click "Quản Lý Cầu" button → Open popup
2. Popup had scan and manage mixed together
3. Click "Dò Tìm Cầu" button → Run scan

**New Way:**
1. Go to "🔍 Dò Tìm Cầu Mới" tab → Run scans
2. Add results to management
3. Go to "🛠️ Quản Lý Cầu" tab → Manage bridges

### For Developers

**Old Way:**
```python
# Mixed responsibilities in one class
class BridgeManagerWindow:
    def scan_bridges(self): ...
    def manage_bridges(self): ...
```

**New Way:**
```python
# Separate responsibilities
class BridgeScannerTab:
    def scan_bridges(self): ...  # ONLY scanning

class BridgeManagementTab:
    def manage_bridges(self): ...  # ONLY management
```

## Commit History

1. **b0831d7** - Backend refactoring: Separated scanner and manager modules
2. **0911e9e** - Added comprehensive tests for scanner module
3. **4b64486** - UI refactoring: Created scanner and management tabs

## Future Enhancements

1. Add filters to scanner results (by rate, type, etc.)
2. Add batch operations in management (select multiple → enable/disable)
3. Add export/import of scan results
4. Add scheduling for automatic scans
5. Add notifications when scan completes

## References

- Single Responsibility Principle: https://en.wikipedia.org/wiki/Single-responsibility_principle
- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
