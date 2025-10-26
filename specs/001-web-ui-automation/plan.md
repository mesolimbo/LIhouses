# Implementation Plan: Local Web Interface for Existing Data Scripts

**Branch**: `001-web-ui-automation` | **Date**: 2025-10-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-web-ui-automation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature creates a simple local web server and browser-based UI that wraps two existing Python scripts (`rentcast_homes.py` and `generate_reports.py`), allowing users to trigger them with button clicks instead of command-line execution. The technical approach prioritizes simplicity: a lightweight Flask server that executes the existing scripts as subprocesses, captures their output, and streams it to a minimal single-page HTML interface via Server-Sent Events (SSE). No modifications to existing scripts, no database, no complex state management - just a thin UI wrapper.

## Technical Context

**Language/Version**: Python 3.13+
**Package Manager**: pipenv (dependencies pinned in Pipfile)
**Primary Dependencies**:

  - Existing: pandas, numpy, matplotlib, seaborn, googlemaps, requests
  - New: Flask (web server), simple built-in subprocess/threading for script execution
**Storage**: CSV files in data/, generated outputs in .tmp/
**Testing**: Manual testing in Git Bash + browser-based UI testing
**Target Platform**: Git Bash (Windows), cross-platform Python
**Execution**:
  - CLI: Existing via `pipenv run python src/homes/rentcast_homes.py` and `pipenv run python src/report/generate_reports.py`
  - Web: New via `pipenv run python src/web/app.py` (starts server on port 8080)
**Project Type**: Adding Flask web wrapper to existing modular CLI utilities
**Performance Goals**: Server startup under 10 seconds, UI feedback within 2 seconds of button clicks
**Constraints**:
  - Must NOT modify existing scripts
  - Single user only (no concurrent script execution)
  - Windows path compatibility required
  - Localhost only (no external network exposure)
**Scale/Scope**:
  - Two scripts to wrap (download data, generate reports)
  - Single web page with two buttons
  - Real-time output streaming from long-running scripts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with [LIhouses Constitution](../../../.specify/memory/constitution.md):

- [x] **Module-First Architecture**: Yes - Flask app as standalone module in `src/web/`
- [x] **Dual Interface**: Yes - existing CLI scripts remain unchanged, web interface wraps them (fulfilling Dual Interface Pattern from constitution)
- [x] **Dependencies**: Yes - Flask pinned in Pipfile (only new dependency beyond stdlib)
- [x] **Data Separation**: Yes - no new data files, web templates in src/web/templates/
- [x] **Git Bash Compatibility**: Yes - uses `os.path.join()`, subprocess module is cross-platform, Flask server works in Git Bash
- [x] **Output Quality**: Yes - existing scripts already generate professional outputs, web UI just triggers them
- [x] **Minimal Dependencies**: Yes - Flask is necessary (cannot build web server with stdlib alone), SSE uses built-in streaming (no Socket.IO/WebSockets library needed)
- [x] **API Keys**: N/A - web server doesn't use API keys directly; existing scripts already handle RENTCAST_API_KEY and GOOGLE_MAPS_API_KEY from .env
- [x] **Code Style**: Yes - will follow PEP 8, include docstrings, comments for complex streaming logic
- [x] **Testing**: Yes - manual testing: start server in Git Bash, test buttons in browser, verify script execution

**Violations requiring justification**: None - full compliance with constitution

## Project Structure

### Documentation (this feature)

```text
specs/001-web-ui-automation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api.md          # HTTP endpoints for Flask server
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
LIhouses/
├── .env                 # API keys (NOT committed - in .gitignore)
├── .env.example         # NEW - Template for API keys (safe to commit)
├── src/
│   ├── core/        # Core utilities (KML generation, data enrichment) - unchanged
│   ├── homes/       # Property data fetching/processing - unchanged
│   │   └── rentcast_homes.py  # Existing script
│   ├── report/      # Report generation & visualization - unchanged
│   │   └── generate_reports.py  # Existing script
│   └── web/         # Flask app (NEW - GUI wrapper only)
│       ├── app.py           # Flask server with routes
│       ├── executor.py      # Subprocess execution logic
│       ├── templates/
│       │   └── index.html  # Single-page UI
│       └── static/
│           ├── style.css   # Minimal styling
│           └── script.js   # Client-side logic for SSE
├── data/            # Input datasets (committed to repo) - unchanged
└── .tmp/            # Generated outputs (NOT committed)
    └── YYYYMMDD/           # Existing - script outputs
        ├── *.json          # Property data
        └── *.html          # Reports
```

**Module Selection**: **web/** - This feature creates the Flask web interface module

**Structure Decision**: Create new `src/web/` module with:
- `app.py`: Flask server, routes, SSE endpoints
- `executor.py`: Script execution logic (subprocess management, output capture)
- `templates/index.html`: Single-page UI with two buttons
- `static/style.css`: Minimal CSS styling
- `static/script.js`: EventSource for SSE, button click handlers

## Environment Configuration

### Required Secrets (.env file)

**CRITICAL**: API keys must be stored in `.env` file (NOT committed to git)

**Required Environment Variables**:

| Variable | Required For | Purpose | How to Obtain |
|----------|-------------|---------|---------------|
| `RENTCAST_API_KEY` | Download Data | Access RentCast API for property listings | Sign up at https://www.rentcast.io/ |
| `GOOGLE_MAPS_API_KEY` | Generate Reports | Embed Google Maps in HTML reports | Get key from Google Cloud Console |

**Setup Steps**:

1. **Create `.env` file** in project root (if it doesn't exist):
   ```bash
   touch .env
   ```

2. **Add API keys** to `.env`:
   ```bash
   # LIhouses API Keys
   # DO NOT COMMIT THIS FILE - it's in .gitignore
   
   # RentCast API Key (for downloading property data)
   # Get your key from: https://www.rentcast.io/
   RENTCAST_API_KEY=your_rentcast_api_key_here
   
   # Google Maps API Key (for generating reports with maps)
   # Get your key from: Google Cloud Console
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```

3. **Verify `.gitignore` excludes `.env`**:
   ```bash
   # Should already exist in .gitignore:
   .env
   ```

4. **Create `.env.example`** template (safe to commit):
   ```bash
   # LIhouses API Keys - Template
   # Copy this file to .env and fill in your actual keys
   
   RENTCAST_API_KEY=your_rentcast_api_key_here
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```

**Validation in Web Interface**:

The Flask app will validate environment variables **before** executing scripts:

```python
# In app.py - before script execution
REQUIRED_ENV_VARS = {
    "download": ["RENTCAST_API_KEY"],
    "generate": ["GOOGLE_MAPS_API_KEY"]
}

def validate_env_vars(operation_type):
    """Validate required env vars exist for operation"""
    for var in REQUIRED_ENV_VARS[operation_type]:
        if not os.environ.get(var):
            raise ValueError(
                f"Missing required environment variable: {var}. "
                f"Please add it to your .env file."
            )
```

**User Experience**:
- If user clicks "Download Data" without `RENTCAST_API_KEY` set:
  - Web UI shows error: "Missing required environment variable: RENTCAST_API_KEY"
  - Script does NOT execute (fail fast)
  - User can fix .env and retry (no server restart needed)

**Loading .env in Flask App**:

The existing scripts likely already use `python-dotenv`. The web app will reuse this:

```python
# In app.py - at top of file
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Now os.environ['RENTCAST_API_KEY'] is available
```

**Security Notes**:
- ✅ `.env` is in `.gitignore` (never committed)
- ✅ `.env.example` is committed (shows required vars, no secrets)
- ✅ Flask validates vars before script execution
- ✅ Error messages don't expose secret values
- ✅ Localhost-only server (no network exposure)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations
