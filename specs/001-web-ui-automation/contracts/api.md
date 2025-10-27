# API Contract: Local Web Interface

**Feature**: 001-web-ui-automation
**Date**: 2025-10-25
**Protocol**: HTTP/1.1
**Base URL**: `http://localhost:8080`

## Overview

This document defines the HTTP API contract for the Flask web server. The API provides endpoints to:
1. Serve the single-page UI
2. Execute Python scripts (download/generate)
3. Stream script output in real-time via SSE

**Design Principles**:
- RESTful where applicable (GET for queries, POST for actions)
- JSON for structured data
- SSE (text/event-stream) for real-time streaming
- Simple error responses with clear messages

## Endpoints

### 1. GET /

**Purpose**: Serve the main web UI (single-page application)

**Response**:
- **Status**: 200 OK
- **Content-Type**: `text/html`
- **Body**: HTML page with buttons, log viewer

**Example**:
```http
GET / HTTP/1.1
Host: localhost:8080

HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
  <head><title>LIhouses Data Manager</title></head>
  <body>
    <!-- UI content -->
  </body>
</html>
```

---

### 2. POST /api/execute

**Purpose**: Start execution of a Python script (download or generate)

**Request**:
- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
    "operation_type": "download" | "generate"
  }
  ```

**Validation**:
- `operation_type` must be one of: `"download"`, `"generate"`
- No other operation can be running
- Required environment variables must be set:
  - `download` requires: `RENTCAST_API_KEY`
  - `generate` requires: `GOOGLE_MAPS_API_KEY`

**Success Response**:
- **Status**: 200 OK
- **Body**:
  ```json
  {
    "status": "success",
    "operation_id": "a7f3c8e1-4b2d-4f9a-8c3e-1d5e6f7a8b9c",
    "message": "Operation started successfully"
  }
  ```

**Error Responses**:

**400 Bad Request** (Invalid operation type):
```json
{
  "status": "error",
  "error": "Invalid operation type: 'foo'. Must be 'download' or 'generate'."
}
```

**409 Conflict** (Operation already running):
```json
{
  "status": "error",
  "error": "Cannot start operation: another operation is already running"
}
```

**400 Bad Request** (Missing env var):
```json
{
  "status": "error",
  "error": "Missing required environment variable: RENTCAST_API_KEY"
}
```

**Example**:
```http
POST /api/execute HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "operation_type": "download"
}

HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "operation_id": "a7f3c8e1-4b2d-4f9a-8c3e-1d5e6f7a8b9c",
  "message": "Operation started successfully"
}
```

---

### 3. GET /api/stream/{operation_id}

**Purpose**: Stream real-time output from a running script via Server-Sent Events (SSE)

**Path Parameters**:
- `operation_id` (string, UUID): The ID returned from POST /api/execute

**Response**:
- **Status**: 200 OK
- **Content-Type**: `text/event-stream`
- **Cache-Control**: `no-cache`
- **Connection**: `keep-alive`

**SSE Event Types**:

1. **`output` event**: New line of script output
   ```
   event: output
   data: {"line": "Fetching data for zip code 11772..."}
   
   ```

2. **`completed` event**: Script finished successfully
   ```
   event: completed
   data: {"exit_code": 0, "summary": "245 listings downloaded", "links": []}
   
   ```

3. **`failed` event**: Script failed with error
   ```
   event: failed
   data: {"exit_code": 1, "error": "Missing required environment variable: RENTCAST_API_KEY"}
   
   ```

4. **`heartbeat` event**: Keep-alive ping (every 15 seconds)
   ```
   event: heartbeat
   data: {}
   
   ```

**Client Usage**:
```javascript
const eventSource = new EventSource(`/api/stream/${operationId}`);

eventSource.addEventListener('output', (event) => {
  const data = JSON.parse(event.data);
  console.log('Output:', data.line);
});

eventSource.addEventListener('completed', (event) => {
  const data = JSON.parse(event.data);
  console.log('Success!', data.summary);
  eventSource.close();
});

eventSource.addEventListener('failed', (event) => {
  const data = JSON.parse(event.data);
  console.error('Failed:', data.error);
  eventSource.close();
});
```

**Error Responses**:

**404 Not Found** (Invalid operation ID):
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "status": "error",
  "error": "Operation not found: invalid-id"
}
```

**Example**:
```http
GET /api/stream/a7f3c8e1-4b2d-4f9a-8c3e-1d5e6f7a8b9c HTTP/1.1
Host: localhost:8080

HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: output
data: {"line": "Loading Long Island zip codes..."}

event: output
data: {"line": "Loaded 150 Long Island zip codes"}

event: output
data: {"line": "Fetching data for 150 zip codes..."}

event: completed
data: {"exit_code": 0, "summary": "245 listings downloaded", "links": []}

```

---

### 4. GET /api/status

**Purpose**: Check server status and current running operation (if any)

**Response**:
- **Status**: 200 OK
- **Content-Type**: `application/json`
- **Body** (idle):
  ```json
  {
    "server_status": "running",
    "current_operation": null
  }
  ```
- **Body** (operation running):
  ```json
  {
    "server_status": "running",
    "current_operation": {
      "id": "a7f3c8e1-4b2d-4f9a-8c3e-1d5e6f7a8b9c",
      "type": "download",
      "status": "running",
      "start_time": "2025-10-25T14:23:45.123456"
    }
  }
  ```

**Use Case**: Frontend can poll this on page load to check if an operation is already running

**Example**:
```http
GET /api/status HTTP/1.1
Host: localhost:8080

HTTP/1.1 200 OK
Content-Type: application/json

{
  "server_status": "running",
  "current_operation": null
}
```

---

## Static Assets

### GET /static/{filename}

**Purpose**: Serve static files (CSS, JavaScript)

**Supported Files**:
- `/static/style.css` → `src/web/static/style.css`
- `/static/script.js` → `src/web/static/script.js`

**Response**:
- **Status**: 200 OK
- **Content-Type**: Determined by file extension
  - `.css` → `text/css`
  - `.js` → `application/javascript`

---

## Error Handling

### Standard Error Response Format

All errors follow this JSON structure:

```json
{
  "status": "error",
  "error": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input (wrong operation type, missing fields) |
| 404 | Not Found | Resource not found (invalid operation ID, missing file) |
| 409 | Conflict | Operation already running (cannot start concurrent operations) |
| 500 | Internal Server Error | Unexpected server error (script crash, file I/O error) |

### Error Examples

**Missing Request Body**:
```http
POST /api/execute HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{}

HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": "error",
  "error": "Missing required field: operation_type"
}
```

**Script Not Found** (should never happen, but handle gracefully):
```http
POST /api/execute HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "operation_type": "download"
}

HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "status": "error",
  "error": "Script not found: src/homes/rentcast_homes.py"
}
```

---

## CORS Headers

Even though this is localhost-only, include CORS headers for strict browsers:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

---

## Rate Limiting

**None** - Single user, local only, no need for rate limiting.

---

## Authentication

**None** - Localhost only, single user, no authentication required.

---

## Implementation Notes

### Flask Route Mapping

```python
from flask import Flask, request, jsonify, render_template, Response

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/execute', methods=['POST'])
def execute_operation():
    # Implementation
    pass

@app.route('/api/stream/<operation_id>')
def stream_operation(operation_id):
    # SSE implementation
    pass

@app.route('/api/status', methods=['GET'])
def get_status():
    # Implementation
    pass
```

### SSE Generator Function

```python
def event_stream(operation_id):
    """Generator function for SSE"""
    # Get operation from execution_state
    operation = execution_state.get('current_operation')

    if not operation or operation['id'] != operation_id:
        yield f"event: error\ndata: {json.dumps({'error': 'Operation not found'})}\n\n"
        return

    # Stream existing output lines
    for line in operation['output_lines']:
        yield f"event: output\ndata: {json.dumps({'line': line})}\n\n"

    # Stream new output as it arrives (polling thread-safe queue)
    while operation['status'] == 'running':
        # Poll for new output (implementation detail)
        time.sleep(0.1)

    # Send completion event
    if operation['status'] == 'completed':
        yield f"event: completed\ndata: {json.dumps({'exit_code': 0, 'summary': operation['result_summary']})}\n\n"
    else:
        yield f"event: failed\ndata: {json.dumps({'exit_code': operation['exit_code'], 'error': operation['error_message']})}\n\n"
```

---

## Testing

### Manual Testing with curl

**Start download operation**:
```bash
curl -X POST http://localhost:8080/api/execute \
  -H "Content-Type: application/json" \
  -d '{"operation_type":"download"}'
```

**Stream output**:
```bash
curl -N http://localhost:8080/api/stream/{operation_id}
```

**Check server status**:

```bash
curl http://localhost:8080/api/status
```

---

## Summary

This API provides a minimal yet complete interface for:
- ✅ Triggering script execution with validation
- ✅ Real-time output streaming via SSE
- ✅ Server status checking
- ✅ Static asset serving for UI

Total: **5 routes** + static file serving - extremely simple for a web application.
