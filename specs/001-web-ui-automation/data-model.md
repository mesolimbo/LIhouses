# Data Model: Local Web Interface for Existing Data Scripts

**Feature**: 001-web-ui-automation
**Date**: 2025-10-25
**Status**: Complete

## Overview

This document defines the data structures used by the web interface to manage script execution state. Note that this feature does NOT modify the data models of the existing scripts (rentcast_homes.py and generate_reports.py) - those remain unchanged.

## Core Entities

### 1. Operation

Represents a single execution of a Python script triggered via the web UI.

**Purpose**: Track script execution state and capture output.

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|-----------|
| `id` | string (UUID) | Yes | Unique identifier for this operation | Auto-generated (uuid.uuid4()) |
| `type` | string | Yes | Script type: "download" or "generate" | Must be one of: ["download", "generate"] |
| `status` | string | Yes | Current state: "running", "completed", "failed" | Must be one of: ["running", "completed", "failed"] |
| `start_time` | string (ISO 8601) | Yes | When the operation started | Auto-generated (datetime.now().isoformat()) |
| `end_time` | string (ISO 8601) | No | When the operation finished | Only set when status != "running" |
| `exit_code` | integer | No | Script's exit code (0 = success) | Set when script completes; 0 for success, non-zero for error |
| `output_lines` | array[string] | Yes | Captured stdout/stderr lines | Append-only; limit to last 1000 lines to prevent memory issues |
| `error_message` | string | No | User-friendly error description | Set when status = "failed" |
| `result_summary` | string | No | Extracted result (e.g., "245 listings downloaded") | Parsed from script output on success |
| `report_links` | array[string] | No | Relative URLs to generated reports | Only for "generate" operations; parsed from script output |

**State Transitions**:
```
[Created] → status="running"
    ↓
[Script completes successfully] → status="completed", exit_code=0
    ↓
[Script fails/errors] → status="failed", exit_code>0
```

**Example (JSON)**:
```json
{
  "id": "a7f3c8e1-4b2d-4f9a-8c3e-1d5e6f7a8b9c",
  "type": "download",
  "status": "completed",
  "start_time": "2025-10-25T14:23:45.123456",
  "end_time": "2025-10-25T14:28:12.654321",
  "exit_code": 0,
  "output_lines": [
    "Loading Long Island zip codes...",
    "Loaded 150 Long Island zip codes",
    "Fetching data for 150 zip codes...",
    "Found 245 listings within 1.5 miles of Patchogue for zip 11772",
    "...",
    "Complete! Filtered homes saved to: .tmp/20251025/homes-20251025_142812.csv"
  ],
  "error_message": null,
  "result_summary": "245 listings downloaded",
  "report_links": null
}
```

**Example (Failed Operation)**:
```json
{
  "id": "b8e4d9f2-5c3e-4g0b-9d4f-2e6f7g8a9c0d",
  "type": "generate",
  "status": "failed",
  "start_time": "2025-10-25T15:10:30.000000",
  "end_time": "2025-10-25T15:10:32.500000",
  "exit_code": 1,
  "output_lines": [
    "Error: GOOGLE_MAPS_API_KEY environment variable not set!",
    "Please set it with: export GOOGLE_MAPS_API_KEY='your-api-key'"
  ],
  "error_message": "Missing required environment variable: GOOGLE_MAPS_API_KEY",
  "result_summary": null,
  "report_links": null
}
```

### 2. ExecutionState (In-Memory Only)

Represents the currently running operation (if any).

**Purpose**: Prevent concurrent script execution, provide lock mechanism.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `current_operation` | Operation \| None | The operation currently executing, or None if idle |
| `process` | subprocess.Popen \| None | The running subprocess, or None if idle |
| `output_thread` | threading.Thread \| None | Thread capturing stdout/stderr, or None if idle |

**Storage**: Python dictionary in app.py global state (not persisted)

**Concurrency Control**:
```python
# Before starting new operation:
if execution_state['current_operation'] is not None:
    return error("An operation is already running")

# After operation completes:
execution_state['current_operation'] = None
execution_state['process'] = None
execution_state['output_thread'] = None
```

## Relationships

```
ExecutionState (in-memory)
    │
    ├─ 1:0..1 → Operation (current)
                └─ 1:0..1 → subprocess.Popen
```

## Data Flow

### Starting an Operation

1. User clicks "Download Data" or "Generate Reports" button
2. Frontend sends POST to `/api/execute` with `{ "operation_type": "download" }`
3. Backend validates:
   - No current operation running
   - Required env vars exist
   - Operation type is valid
4. Backend creates new Operation with status="running"
5. Backend starts subprocess (Popen) and output capture thread
6. Backend stores Operation in ExecutionState
7. Backend returns 200 OK with operation ID
8. Frontend opens SSE connection to `/api/stream/{operation_id}`
9. Backend streams output lines to frontend via SSE
10. When script completes:
    - Backend updates Operation (status, exit_code, end_time)
    - Backend clears ExecutionState
    - Backend sends final SSE event with completion status
    - Frontend closes SSE connection

## Validation Rules

### Operation Type Validation
```python
VALID_OPERATIONS = ["download", "generate"]

if operation_type not in VALID_OPERATIONS:
    raise ValueError(f"Invalid operation type: {operation_type}")
```

### Environment Variable Validation
```python
REQUIRED_ENV_VARS = {
    "download": ["RENTCAST_API_KEY"],
    "generate": ["GOOGLE_MAPS_API_KEY"]
}

for var in REQUIRED_ENV_VARS[operation_type]:
    if not os.environ.get(var):
        raise ValueError(f"Missing required environment variable: {var}")
```

### Concurrency Validation
```python
if execution_state['current_operation'] is not None:
    raise RuntimeError("Cannot start operation: another operation is already running")
```

## Edge Cases

### 1. User Closes Browser During Execution
- Script continues running on server
- Operation remains in ExecutionState for a limited amount of time

### 2. Server Crashes During Execution
- Operation lost (not persisted until completion)
- Running operation appears "stuck" for a limited time - user can retry

### 3. Output Exceeds 1000 Lines
- Keep only last 1000 lines in memory
- Older lines dropped (FIFO)
- SSE clients see all lines in real-time (not truncated during streaming)

## Non-Data Elements

This feature does NOT define data models for:
- **Property listings**: Created by `rentcast_homes.py` (unchanged)
- **Reports**: Created by `generate_reports.py` (unchanged)
- **Zip codes, stations, etc.**: Handled by existing scripts (unchanged)

The web UI only manages:
- Operation execution state
- Real-time output streaming

## Implementation Notes

### In-Memory State

**Global State (app.py)**:
```python
execution_state = {
    'current_operation': None,  # Operation dict or None
    'process': None,             # Popen object or None
    'output_thread': None        # Thread object or None
}
```

## Summary

The data model is intentionally minimal:
- **1 main entity** (Operation) with clear state transitions
- **1 in-memory state** (current execution lock)
- **No database** (unnecessary for single-user local app)
- **No complex relationships** (flat structure)
- **No history**

This simplicity aligns with the "keep things as simple as possible" directive and the constitution's principle of minimal dependencies.
