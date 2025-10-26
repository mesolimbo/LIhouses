# Quickstart Guide: Local Web Interface

**Feature**: 001-web-ui-automation
**Date**: 2025-10-25
**For**: Developers implementing this feature

## Overview

This guide provides a quick-start implementation roadmap for building the local web interface. It assumes you've read the spec, research, data model, and API contracts.

## Implementation Order

Follow this order to build the feature incrementally, testing each component before moving to the next:

### Phase 1: Basic Flask Server
1. Create `src/web/app.py` with minimal Flask app
2. Add route for `GET /` (serve "Hello World" HTML)
3. Test: Run `pipenv run python src/web/app.py`, visit localhost:8080

### Phase 2: Static UI
4. Create `src/web/templates/index.html` with:
   - Two buttons: "Download Data" and "Generate Reports"
   - Empty log viewer `<div>
5. Create `src/web/static/style.css` with basic layout
6. Update `GET /` to serve template
7. Test: Buttons visible and styled, no functionality yet

### Phase 3: Script Execution
8. Create `src/web/executor.py` with:
   - `execute_script(script_type)` function using `subprocess.Popen`
   - Output capture logic (read stdout/stderr line-by-line)
   - Store in global `execution_state` dict
9. Add `POST /api/execute` route in `app.py`
10. Validate input, check for running operation, call executor
11. Test with curl: `curl -X POST localhost:8080/api/execute -d '{"operation_type":"download"}'`

### Phase 4: Real-Time Streaming
12. Add `GET /api/stream/<operation_id>` route
13. Implement SSE generator function (yield output lines)
14. Create `src/web/static/script.js` with EventSource logic
15. Connect buttons to POST /api/execute, then open SSE stream
16. Test: Click button, see real-time output in console

### Phase 5: UI Updates
17. Update `script.js` to append output to log viewer
18. Add success/failure message display
19. Disable buttons during operation
20. Test: Full user flow works end-to-end

### Phase 6: Polish
26. Add auto-browser-open on server startup (webbrowser module)
27. Add environment variable validation before script execution
28. Parse script output for result summary and links
29. Add error handling for all edge cases
30. Test: Complete user scenarios from spec

---

## File Structure to Create

```
src/web/
├── app.py                 # Flask server (main entry point)
├── executor.py            # Script execution logic
├── templates/
│   └── index.html        # Single-page UI
└── static/
    ├── style.css         # UI styling
    └── script.js         # Client-side logic
```

---

## Minimal Starter Code

### 1. `src/web/app.py` (Skeleton)

```python
#!/usr/bin/env python3
"""
Flask web server for triggering LIhouses data scripts via browser UI.
"""

import os
import json
import webbrowser
from flask import Flask, render_template, request, jsonify, Response
from executor import execute_script, get_execution_state

app = Flask(__name__)

# Global state (in-memory)
execution_state = {
    'current_operation': None,
    'process': None,
    'output_thread': None
}

@app.route('/')
def index():
    """Serve main UI"""
    return render_template('index.html')


@app.route('/api/execute', methods=['POST'])
def execute_operation():
    """Start script execution"""
    # TODO: Validate input
    # TODO: Check for running operation
    # TODO: Validate env vars
    # TODO: Call execute_script()
    # TODO: Return operation ID
    pass


@app.route('/api/stream/<operation_id>')
def stream_operation(operation_id):
    """Stream real-time output via SSE"""
    # TODO: Implement SSE generator
    pass


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get server and current operation status"""
    # TODO: Return current_operation if exists
    pass


if __name__ == '__main__':
    # Create .tmp directory if doesn't exist
    os.makedirs('.tmp', exist_ok=True)

    # Open browser automatically
    webbrowser.open('http://localhost:8080')

    # Start Flask dev server
    print("Starting LIhouses Web Interface...")
    print("Server running at: http://localhost:8080")
    print("Press Ctrl+C to stop")

    app.run(debug=True, host='0.0.0.0', port=8080)
```

### 2. `src/web/executor.py` (Skeleton)

```python
"""
Script execution logic using subprocess.
"""

import subprocess
import threading
import os
import uuid
from datetime import datetime


def execute_script(script_type, execution_state):
    """
    Execute a Python script (download or generate) and capture output.

    Args:
        script_type (str): "download" or "generate"
        execution_state (dict): Global state dict to store operation

    Returns:
        str: Operation ID (UUID)
    """
    # TODO: Map script_type to script path
    # TODO: Create Operation dict
    # TODO: Start subprocess.Popen
    # TODO: Start thread to capture output
    # TODO: Store in execution_state
    # TODO: Return operation ID
    pass


def _capture_output(process, operation, execution_state):
    """
    Thread function to capture subprocess output line-by-line.

    Args:
        process (Popen): The running subprocess
        operation (dict): The Operation dict
        execution_state (dict): Global state dict
    """
    # TODO: Read stdout/stderr line-by-line
    # TODO: Append to operation['output_lines']
    # TODO: On completion, update operation status
    # TODO: Clear execution_state
    pass
```

### 3. `src/web/templates/index.html` (Skeleton)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LIhouses Data Manager</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>LIhouses Data Manager</h1>
            <p>Manage real estate data and reports with one click</p>
        </header>

        <main>
            <!-- Action Buttons -->
            <section class="actions">
                <button id="btn-download" class="btn btn-primary">
                    Download Data
                </button>
                <button id="btn-generate" class="btn btn-secondary">
                    Generate Reports
                </button>
            </section>

            <!-- Log Viewer -->
            <section class="log-viewer">
                <h2>Output Log</h2>
                <div id="log-output" class="log-content"></div>
            </section>
        </main>
    </div>

    <script src="/static/script.js"></script>
</body>
</html>
```

### 4. `src/web/static/script.js` (Skeleton)

```javascript
/**
 * Client-side logic for LIhouses web interface
 */

// DOM elements
const btnDownload = document.getElementById('btn-download');
const btnGenerate = document.getElementById('btn-generate');
const logOutput = document.getElementById('log-output');

// State
let currentEventSource = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkServerStatus();

    btnDownload.addEventListener('click', () => executeOperation('download'));
    btnGenerate.addEventListener('click', () => executeOperation('generate'));
});

/**
 * Execute an operation (download or generate)
 */
async function executeOperation(operationType) {
    // TODO: Disable buttons
    // TODO: Clear log
    // TODO: POST to /api/execute
    // TODO: Get operation ID
    // TODO: Open SSE stream to /api/stream/<id>
}

/**
 * Open SSE connection to stream operation output
 */
function streamOperationOutput(operationId) {
    // TODO: Create EventSource
    // TODO: Listen for 'output', 'completed', 'failed' events
    // TODO: Update UI accordingly
}

/**
 * Check server status on page load
 */
async function checkServerStatus() {
    // TODO: GET /api/status
    // TODO: If operation running, reconnect to stream
}
```

### 5. `src/web/static/style.css` (Skeleton)

```css
/* Minimal styling for LIhouses web interface */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    overflow: hidden;
}

header {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 30px;
    text-align: center;
}

/* TODO: Add button styles */
/* TODO: Add log viewer styles */
```

---

## Testing Checklist

After implementing each phase, verify:

### Phase 1 ✓
- [ ] Server starts without errors
- [ ] Browser opens automatically to localhost:8080
- [ ] "Hello World" or basic HTML visible

### Phase 2 ✓
- [ ] Both buttons visible and styled
- [ ] Layout looks reasonable
- [ ] No JavaScript errors in console

### Phase 3 ✓
- [ ] curl POST to /api/execute returns operation ID
- [ ] Script actually runs (check .tmp/ for output files)
- [ ] Concurrent requests rejected with 409 error

### Phase 4 ✓
- [ ] curl to /api/stream shows SSE events
- [ ] JavaScript EventSource connects successfully
- [ ] Console logs show output lines in real-time

### Phase 5 ✓
- [ ] Clicking button shows output in UI
- [ ] Buttons disable during operation
- [ ] Success message appears when complete
- [ ] Error message appears on failure

### Phase 6 ✓
- [ ] Missing env var shows clear error before script runs
- [ ] Generated report links are clickable
- [ ] Browser closes gracefully on Ctrl+C
- [ ] No console errors or warnings

---

## Common Pitfalls

### 1. Subprocess Output Buffering
**Problem**: Output doesn't appear in real-time
**Solution**: Use `bufsize=1` (line-buffered) in `Popen()`:
```python
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    bufsize=1,  # Line-buffered
    universal_newlines=True
)
```

### 2. Thread Safety
**Problem**: Race conditions when updating operation state
**Solution**: Use `threading.Lock()` when modifying `execution_state`

### 3. SSE Connection Drops
**Problem**: Browser closes SSE after 30-60 seconds
**Solution**: Send heartbeat events every 15 seconds:
```python
yield f"event: heartbeat\ndata: {{}}\n\n"
```

### 4. Windows Path Issues
**Problem**: Hardcoded `/` or `\` breaks cross-platform
**Solution**: Always use `os.path.join()`:
```python
script_path = os.path.join('src', 'homes', 'rentcast_homes.py')
```

### 5. Flask Debug Mode
**Problem**: Server restarts unexpectedly during development
**Solution**: Use `debug=True` for development, but disable when testing multi-step flows

---

## Environment Setup

Before starting implementation:

### 1. Install Flask Dependency

```bash
pipenv install flask==3.0.0
```

### 2. Configure API Keys (CRITICAL - NOT committed to git)

**Create `.env` file** in project root with your API keys:

```bash
# Create .env file (if it doesn't exist)
touch .env

# Open in your editor and add:
nano .env  # or code .env, vim .env, etc.
```

**Add the following to `.env`**:

```bash
# LIhouses API Keys
# DO NOT COMMIT THIS FILE - it's in .gitignore

# RentCast API Key (for downloading property data)
# Get your key from: https://www.rentcast.io/
RENTCAST_API_KEY=your_actual_rentcast_api_key_here

# Google Maps API Key (for generating reports with maps)
# Get your key from: Google Cloud Console (https://console.cloud.google.com/)
GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key_here
```

**Create `.env.example` template** (safe to commit):

```bash
# Create example template
cat > .env.example << 'EOF'
# LIhouses API Keys - Template
# Copy this file to .env and fill in your actual keys

RENTCAST_API_KEY=your_rentcast_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
EOF
```

**Verify `.env` is in `.gitignore`**:

```bash
# Check if .env is already excluded
grep "^\.env$" .gitignore

# If not found, add it
echo ".env" >> .gitignore
```

### 3. Verify Existing Scripts Work

```bash
# Test download script (should fail gracefully if no API key yet)
pipenv run python src/homes/rentcast_homes.py

# Test report generation script
pipenv run python src/report/generate_reports.py
```

**Expected behavior if API keys are missing**:
- Download script: Error message about missing `RENTCAST_API_KEY`
- Report script: Error message about missing `GOOGLE_MAPS_API_KEY`

This is normal - the web interface will validate these before running scripts.

### 4. Load Environment Variables in Flask App

The Flask app will load `.env` automatically using `python-dotenv`:

```python
# In src/web/app.py - add at the very top
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now environment variables are available
# os.environ.get('RENTCAST_API_KEY')
# os.environ.get('GOOGLE_MAPS_API_KEY')
```

**Note**: `python-dotenv` should already be installed for the existing scripts. If not:

```bash
pipenv install python-dotenv
```

---

## Running the Final Implementation

```bash
# Start the web server
pipenv run python src/web/app.py

# Browser should open automatically to:
# http://localhost:8080

# Manual access if needed:
# Open http://localhost:8080 in your browser

# Stop the server:
# Press Ctrl+C in the terminal
```

---

## Next Steps After Quickstart

Once you've completed the quickstart implementation:

1. **Generate tasks.md**: Run `/speckit.tasks` to break down the implementation into specific tasks
2. **Implement incrementally**: Follow the task order, testing each piece
3. **Commit frequently**: Small commits after each working phase
4. **Test edge cases**: Try all scenarios from spec.md
5. **Update README**: Document the new web interface for users

---

## Success Criteria

You're done when:
- ✅ User can start server with one command
- ✅ Browser opens automatically
- ✅ Both buttons work (download data, generate reports)
- ✅ Real-time output appears during script execution
- ✅ All error cases show clear messages
- ✅ Existing scripts remain unchanged
- ✅ No external dependencies beyond Flask

---

## Getting Help

If stuck:
1. Check the API contract (contracts/api.md) for endpoint details
2. Review the data model (data-model.md) for state structure
3. Read the research doc (research.md) for design rationale
4. Test each component in isolation (curl for API, console for UI)
5. Add print statements / logging to debug flow

Remember: Keep it simple! This is just a thin wrapper around existing scripts.
