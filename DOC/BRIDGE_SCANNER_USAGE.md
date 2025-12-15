# Bridge Scanner Usage Guide

## Overview

The Bridge Scanner module (`ui/ui_bridge_scanner.py`) provides a robust UI component for scanning bridges and adding them to management with comprehensive validation.

## Quick Start

### Running Tests

```bash
# Run all bridge normalization tests
python -m pytest tests/test_bridge_add_normalization.py -v

# Run specific test
python -m pytest tests/test_bridge_add_normalization.py::TestBridgeNormalization::test_valid_dict_with_all_fields -v
```

### Using the Bridge Scanner Tab

```python
import tkinter as tk
from ui.ui_bridge_scanner import BridgeScannerTab

# Create main window
root = tk.Tk()

# Create scanner tab with logger
scanner = BridgeScannerTab(root, logger=my_logger)

# Load scan results (supports multiple formats)
bridges = [
    {"name": "Cầu 1", "type": "LÔ_V17", "rate": 45.5},  # Dict format
    ("Cầu 2", "LÔ_BN", "Mô tả", 50.0, 3),              # Tuple format
    my_bridge_object,                                    # Object format
]
scanner.load_scan_results(bridges)

root.mainloop()
```

## Features

### 1. Robust Validation

#### Name Validation
- ✅ Rejects: empty, None, "N/A", whitespace-only, "None", "null"
- ✅ Trims whitespace automatically
- ✅ Supports Vietnamese characters and special symbols

**Examples:**
```python
# Valid names
"Cầu + Đặc Biệt #123"  ✅
"Lô V17 - Vị trí 5+7"  ✅

# Invalid names (rejected)
""          ❌ Empty string
"   "       ❌ Whitespace only
"N/A"       ❌ Not applicable
None        ❌ None value
```

#### Type Validation
Valid types whitelist:
- `LÔ_V17` - Lô version 17
- `LÔ_BN` - Lô Bạc Nhớ
- `LÔ_STL_FIXED` - Lô STL fixed
- `ĐỀ` - Đề
- `MEMORY` - Memory bridge
- `CLASSIC` - Classic bridge

Unknown types are marked as `UNKNOWN_xxx` but not rejected.

### 2. Multiple Input Formats

#### Dict Format
```python
bridge = {
    "name": "Cầu Test",           # or "normalized_name", "bridge_name"
    "type": "LÔ_V17",             # or "bridge_type"
    "description": "Mô tả",       # or "desc"
    "rate": 45.5,                 # or "win_rate", can be string "45.5%"
    "streak": 3                   # or "current_streak"
}
```

**Priority order for name extraction:**
1. `normalized_name`
2. `name`
3. `bridge_name`

#### Object Format
```python
class Bridge:
    def __init__(self):
        self.name = "Cầu Test"
        self.type = "LÔ_V17"
        self.rate = 45.5
        self.streak = 3
```

**Supported attributes:**
- Name: `normalized_name`, `name`, `bridge_name`
- Type: `type`, `bridge_type`
- Description: `description`, `desc`
- Rate: `rate`, `win_rate`
- Streak: `streak`, `current_streak`

#### Tuple/List Format
```python
bridge = ("Name", "Type", "Description", 45.5, 3)
# Index:    [0]     [1]        [2]       [3]  [4]

# Minimum required: name and type
bridge = ("Name", "Type")  # Valid
```

### 3. Rate Normalization

Handles various rate formats:
```python
"45.5%"   → 45.5   # String with %
"45.5"    → 45.5   # String without %
45.5      → 45.5   # Float
45        → 45.0   # Integer
"invalid" → 0.0    # Invalid → default 0
```

### 4. Error Reporting

#### Success (All bridges added)
```
✅ Thành công
Đã thêm thành công 5 cầu vào quản lý.
```

#### Partial Success
```
⚠️  Hoàn thành có lỗi
Đã thêm thành công 3/5 cầu.

Có 2 cầu bị bỏ qua do lỗi:
- Cầu '': Tên không hợp lệ hoặc thiếu thông tin
- Cầu 'Test': Loại không xác định ('INVALID_TYPE')
```

#### All Failed
```
❌ Lỗi
Không thể thêm cầu nào. Tất cả 5 cầu đều bị lỗi:
- Cầu 'Cầu 1': Tên không hợp lệ hoặc thiếu thông tin
- Cầu 'Cầu 2': Loại không xác định ('WRONG_TYPE')
...
```

## Architecture

### Class Structure

```
BridgeScannerTab
├── __init__(parent, logger)
├── _create_results_area()          # Create treeview UI
├── _create_action_buttons()        # Create action buttons
├── _normalize_bridge_info(bridge)  # Normalize & validate bridge data
├── _add_selected_to_management()   # Add bridges with validation
├── _select_all_results()           # Select all items
└── load_scan_results(results)      # Load results into UI
```

### Validation Flow

```
User selects bridges
       ↓
_add_selected_to_management()
       ↓
For each bridge:
  ├─→ Get data from treeview
  ├─→ _normalize_bridge_info()
  │     ├─→ Extract name (priority order)
  │     ├─→ Validate name (not empty/None/N/A)
  │     ├─→ Validate type (whitelist check)
  │     ├─→ Normalize rate (remove %, convert to float)
  │     ├─→ Normalize streak (convert to int)
  │     └─→ Return normalized dict or None
  │
  ├─→ If valid:
  │     └─→ upsert_managed_bridge()
  │
  └─→ If invalid:
        └─→ Add to error_list
       ↓
Display summary with errors
```

## Testing

### Test Coverage (32 Tests)

#### TestBridgeNormalization (27 tests)
- ✅ Valid dict with all fields
- ✅ Dict with normalized_name priority
- ✅ Dict with alternate field names
- ✅ Empty name returns None
- ✅ None name returns None
- ✅ "N/A" name returns None
- ✅ Whitespace-only name returns None
- ✅ "None" string returns None
- ✅ Tuple format
- ✅ List format
- ✅ Tuple with fewer elements
- ✅ Object with attributes
- ✅ Object with normalized_name
- ✅ Unknown type marked as UNKNOWN_
- ✅ Missing type marked as UNKNOWN
- ✅ Valid types whitelist
- ✅ Rate string with %
- ✅ Rate string without %
- ✅ Rate as integer
- ✅ Invalid rate defaults to 0
- ✅ Streak as string
- ✅ Invalid streak defaults to 0
- ✅ Description defaults to name
- ✅ Name whitespace trimmed
- ✅ None bridge returns None
- ✅ Empty dict returns None
- ✅ Empty list returns None

#### TestBridgeNormalizationEdgeCases (5 tests)
- ✅ Very long name (500 chars)
- ✅ Special characters in name
- ✅ Negative rate
- ✅ Very high rate (>100%)
- ✅ Negative streak

### Running Specific Tests

```bash
# Test name validation
pytest tests/test_bridge_add_normalization.py -k "name" -v

# Test type validation
pytest tests/test_bridge_add_normalization.py -k "type" -v

# Test rate normalization
pytest tests/test_bridge_add_normalization.py -k "rate" -v

# Test edge cases
pytest tests/test_bridge_add_normalization.py::TestBridgeNormalizationEdgeCases -v
```

## Troubleshooting

### Common Issues

#### 1. Import Error
```python
ImportError: cannot import name 'upsert_managed_bridge'
```
**Solution:** Ensure `lottery_service.py` is properly configured with the bridge management functions.

#### 2. All Bridges Rejected
```
Không thể thêm cầu nào. Tất cả X cầu đều bị lỗi
```
**Check:**
- Bridge names are not empty/None/"N/A"
- Bridge types match whitelist (or accept UNKNOWN_ prefix)
- Data format is correct (dict/object/tuple/list)

#### 3. Type Validation Warnings
```
- Cầu 'xxx': Loại không xác định ('CUSTOM_TYPE')
```
**This is a warning, not an error.** The bridge will still be added but marked with `UNKNOWN_` prefix.

## Logging

The module logs detailed information if a logger is provided:

```python
[SUCCESS] Added bridge 'Cầu 1': Đã THÊM cầu 'Cầu 1'.
[ERROR] Bridge normalization failed: {'name': '', 'type': 'LÔ_V17'}
[WARNING] Bridge 'Cầu 2': Unknown type 'INVALID_TYPE'
[EXCEPTION] Processing item iid123: KeyError('name')
```

## Best Practices

1. **Always provide a logger** for debugging
2. **Validate data before loading** if possible
3. **Use consistent data format** across your application
4. **Test with edge cases** before production
5. **Monitor error logs** for recurring issues

## Examples

### Example 1: Basic Usage
```python
from ui.ui_bridge_scanner import BridgeScannerTab

scanner = BridgeScannerTab(parent, logger)
scanner.load_scan_results([
    {"name": "Cầu 1", "type": "LÔ_V17", "rate": 45.5},
    {"name": "Cầu 2", "type": "LÔ_BN", "rate": 50.0},
])
# User selects and clicks "Add to management"
```

### Example 2: Mixed Formats
```python
results = [
    {"name": "Dict Bridge", "type": "LÔ_V17", "rate": 45.5},
    ("Tuple Bridge", "LÔ_BN", "Description", 50.0, 3),
    my_object_bridge,  # Has .name, .type attributes
]
scanner.load_scan_results(results)
```

### Example 3: With Error Handling
```python
# Invalid bridges will be rejected with clear messages
results = [
    {"name": "Valid Bridge", "type": "LÔ_V17", "rate": 45.5},
    {"name": "", "type": "LÔ_V17", "rate": 0},        # Empty name → rejected
    {"name": "N/A", "type": "LÔ_V17", "rate": 0},     # N/A → rejected
    {"name": "Bridge 3", "type": "INVALID", "rate": 50.0},  # Unknown type → warning
]
scanner.load_scan_results(results)
# Result: 2 added successfully, 2 rejected with error messages
```

## Version History

- **v1.0** (2025-12-15): Initial implementation
  - Complete validation & normalization
  - 32 comprehensive tests
  - Multiple format support
  - Clear error reporting

## Support

For issues or questions:
1. Check test cases: `tests/test_bridge_add_normalization.py`
2. Review this documentation
3. Check logs if logger is enabled
4. Run tests to verify behavior

---

**Last Updated:** 2025-12-15  
**Status:** ✅ Production Ready  
**Test Coverage:** 32/32 passing
