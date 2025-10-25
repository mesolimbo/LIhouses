# Research: Local Web Interface for Existing Data Scripts

**Feature**: 001-web-ui-automation
**Date**: 2025-10-25
**Status**: Complete

## Overview

This document records the technical research and decisions made during Phase 0 of planning. The goal was to determine the simplest possible approach to wrap existing Python scripts with a web UI, keeping the implementation minimal and aligned with the "keep things as simple as possible" directive.

## Key Decisions

### Decision 1: Web Framework Selection

**Decision**: Use Flask (lightweight Python web framework)

**Rationale**:
- Minimal boilerplate - can create entire server in ~50 lines
- Already familiar to Python developers (low learning curve)
- Built-in development server (no deployment complexity)
- Perfect for single-page apps with minimal routes
- Native Python integration makes calling subprocess easy
- Supports Server-Sent Events (SSE) out of the box

**Alternatives Considered**:
- **FastAPI**: Too complex for this simple use case, requires async/await, better for REST APIs
- **Django**: Way too heavyweight, requires ORM/database setup, not needed for 2 buttons
- **Bottle**: Even more minimal than Flask, but less documentation/community support
- **Plain HTTP server (http.server)**: Would require manual routing, SSE implementation, HTML serving - more work

**Rejected Simpler Alternatives**:
- **No web server (CLI only)**: Violates requirement for browser-based UI
- **Static HTML + Python simple server**: Cannot execute scripts or stream output without server-side logic

### Decision 2: Real-Time Output Streaming

**Decision**: Use Server-Sent Events (SSE) for one-way server-to-client streaming

**Rationale**:
- Built-in browser support (EventSource API), no libraries needed
- Perfect for one-way streaming (server stdout → browser)
- Simpler than WebSockets (no bidirectional communication needed)
- Works with plain HTTP (no protocol upgrade required)
- Flask has native support via Response streaming

**Alternatives Considered**:
- **WebSockets (Socket.IO)**: Bidirectional, but we only need server→client; requires extra library
- **Long polling**: Hacky, inefficient, creates many HTTP requests
- **No streaming (batch updates)**: Would miss real-time output, poor UX for long operations

### Decision 3: Script Execution Approach

**Decision**: Use Python's `subprocess.Popen` with stdout/stderr capture in separate thread

**Rationale**:
- `subprocess` is stdlib (no dependencies)
- `Popen` allows non-blocking execution with real-time output capture
- Thread-based execution keeps server responsive during long scripts
- Can capture both stdout and stderr separately
- Works cross-platform (Windows/Linux/Mac)

**Alternatives Considered**:
- **`os.system()`**: Blocking, cannot capture output in real-time
- **`subprocess.run()`**: Blocking by default, harder to stream output
- **Async/await with `asyncio.create_subprocess_exec`**: Requires FastAPI/async framework, more complex
- **Celery/RQ task queue**: Way overkill for single-user local app

### Decision 4: State Management

**Decision**: In-memory dictionary + simple JSON file for operation history

**Rationale**:
- No database needed for single user
- JSON file in .tmp/ persists history across server restarts
- In-memory dict tracks current running operation (only one at a time)
- Simple to implement (10 lines of code)
- Aligns with "data separation" principle (.tmp/ for outputs)

**Alternatives Considered**:
- **SQLite database**: Overkill for storing 20 operation records
- **No persistence**: Would lose history on server restart
- **Complex state machine**: Not needed - only 3 states (idle, running, completed)

### Decision 5: Frontend Technology

**Decision**: Vanilla JavaScript (ES6+) with no frameworks

**Rationale**:
- Modern browsers support ES6 modules, fetch, EventSource natively
- Single-page app with 2 buttons doesn't need React/Vue/Angular
- Zero build step, zero dependencies, zero complexity
- Faster initial load (no framework overhead)
- Easier to debug and maintain

**Alternatives Considered**:
- **React/Vue/Angular**: Massive overkill for 2 buttons and a log viewer
- **jQuery**: Still a dependency, not needed when using modern ES6
- **Alpine.js/htmx**: Tempting for reactivity, but still a dependency

### Decision 6: Environment Variable Validation

**Decision**: Check for required env vars at route invocation time (not server startup)

**Rationale**:
- User might start server before setting API keys
- Better UX to show error when clicking button (with helpful message)
- Allows user to fix env vars without restarting server
- Simpler error handling (one place, not two)

**Alternatives Considered**:
- **Validate at startup**: Server would fail to start, worse UX
- **No validation**: Scripts would fail with cryptic errors

### Decision 7: Browser Auto-Open

**Decision**: Use Python's `webbrowser` module to open default browser on startup

**Rationale**:
- `webbrowser` is stdlib, cross-platform
- One less manual step for user
- Opens at exact moment server is ready (avoids "connection refused")

**Alternatives Considered**:
- **Manual open**: User must remember to navigate to localhost:8080
- **Shell command (`start`/`open`)**: Platform-specific, not cross-platform

## Technology Stack Summary

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Web Server | Flask | Minimal Python web framework, built-in dev server |
| Real-time Streaming | Server-Sent Events (SSE) | Browser-native, one-way streaming, no libraries |
| Script Execution | subprocess.Popen | Stdlib, non-blocking, cross-platform |
| Frontend | Vanilla JavaScript (ES6) | No build step, no dependencies, sufficient for 2 buttons |
| State Management | In-memory dict + JSON file | No database needed for single-user app |
| Styling | Plain CSS | No framework needed for simple layout |

## Implementation Complexity Assessment

**Lines of Code Estimate**:
- `app.py`: ~80 lines (Flask routes, SSE endpoint, server startup)
- `executor.py`: ~60 lines (subprocess management, output capture, thread handling)
- `index.html`: ~100 lines (structure, buttons, log viewer)
- `script.js`: ~60 lines (EventSource, button handlers, DOM updates)
- `style.css`: ~80 lines (basic layout, button styling, log formatting)

**Total**: ~380 lines of code (extremely simple for a web application)

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Script hangs indefinitely | Low | Add timeout to subprocess (configurable, default 30 min) |
| User closes browser during execution | Medium | Script continues running; history shows "running" until completion |
| Concurrent button clicks | Medium | Disable buttons when operation running; check lock before execution |
| Large output overwhelms browser | Low | Limit SSE messages to last 1000 lines; existing scripts have reasonable output |
| Port 8080 already in use | Medium | Try ports 8080-8090 in sequence; display actual port in startup message |

## Open Questions Resolved

1. **Q: How to handle script failures?**
   - A: Capture stderr separately, display in red in log viewer, mark operation as "failed" in history

2. **Q: Should we support stopping running scripts?**
   - A: No - adds complexity (process management, cleanup), not in requirements. User can Ctrl+C server if needed.

3. **Q: How to link to generated reports?**
   - A: Parse script output for file paths, convert to relative URLs, display as clickable links in success message

4. **Q: Should server be HTTPS?**
   - A: No - localhost only, no network exposure, no need for SSL/TLS complexity

5. **Q: Should we validate Python dependencies before starting server?**
   - A: No - pipenv ensures dependencies are installed; if missing, Flask won't even import

## Best Practices to Follow

### Flask Server
- Use blueprint for cleaner route organization (though only 4 routes, might skip)
- Enable CORS headers (even for localhost, some browsers are strict)
- Set proper Content-Type headers for SSE (`text/event-stream`)
- Use Flask's `after_request` for cleanup/logging

### Subprocess Management
- Always use `with` context manager for file handles
- Set `bufsize=1` for line-buffered output
- Handle both UTF-8 and potential encoding errors (Windows)
- Always `communicate()` or `wait()` to prevent zombie processes

### Error Handling
- Wrap all subprocess calls in try/except
- Log errors to both server console and operation history
- Return meaningful HTTP status codes (200, 400, 500)
- Never expose internal paths or stack traces to browser

### Security (even though localhost-only)
- Validate operation type (only "download" or "generate")
- Use `os.path.join()` for all file paths (prevent directory traversal)
- Never pass user input directly to shell
- Limit operation history size (prevent unbounded growth)

## Dependencies to Add

**Pipfile additions**:
```toml
[packages]
flask = "==3.0.0"  # Web framework

[dev-packages]
# None needed - manual testing only
```

**No additional JavaScript libraries needed** - using browser-native APIs.

## Conclusion

This research confirms that a simple Flask + vanilla JavaScript approach is the optimal solution for wrapping the existing Python scripts. The entire implementation requires less than 400 lines of code, no database, no build tools, and only one new dependency (Flask). This aligns perfectly with the user's directive to "keep things as simple as possible."

Next steps: Proceed to Phase 1 (data model and API contracts).
