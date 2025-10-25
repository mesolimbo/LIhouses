# Feature Specification: Local Web Interface for Existing Data Scripts

**Feature Branch**: `001-web-ui-automation`
**Created**: 2025-10-25
**Status**: Draft
**Input**: User description: "Set-up a basic server and a web ui that I can run locally so that I can 1) Download new data via API (using src/homes/rentcast_homes.py) and 2) Generate the latest reports (using src/report/generate_reports.py), all with the single click of a button."

## Feature Overview

**What Already Exists:**
- `src/homes/rentcast_homes.py`: A working Python script that downloads property listing data from the RentCast API and saves it to dated directories
- `src/report/generate_reports.py`: A working Python script that generates HTML reports with maps, charts, and statistics from the downloaded data

**What This Feature Adds:**
This feature creates a **local web server and user interface** that wraps the existing scripts, allowing users to trigger them through a browser instead of the command line. The core data download and report generation logic remains unchanged; we are only building the UI and server layer to make these operations accessible via web buttons.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trigger Data Download via Web UI (Priority: P1)

As a real estate analyst, I want to trigger the existing data download script through a web button instead of running command-line scripts, so that I can keep my analysis up-to-date without technical knowledge.

**Why this priority**: This is the foundational UI capability that makes the existing download functionality accessible to non-technical users. The download logic already exists and works; we just need a simple way to trigger it.

**Independent Test**: Can be fully tested by clicking the download button in the web interface and verifying that the existing Python script executes successfully and produces the expected data files, delivering immediate value by replacing command-line execution with a simple button click.

**Acceptance Scenarios**:

1. **Given** the web interface is open and no data has been downloaded today, **When** I click the "Download Data" button, **Then** the system initiates the data download process and shows a progress indicator
2. **Given** the download process is running, **When** the download completes successfully, **Then** the system displays a success message showing the number of listings downloaded and the file location
3. **Given** the download process is running, **When** an error occurs (e.g., missing API key, network failure), **Then** the system displays a clear error message explaining what went wrong
4. **Given** data has already been downloaded today, **When** I attempt to download again, **Then** the system informs me that today's data already exists and asks for confirmation before re-downloading

---

### User Story 2 - Trigger Report Generation via Web UI (Priority: P2)

As a real estate analyst, I want to trigger the existing report generation script through a web button instead of running command-line scripts, so that I can create visualizations without technical knowledge.

**Why this priority**: This makes the existing report generation functionality accessible through the UI. The report logic already exists and works; we just need a simple way to trigger it. Naturally follows after the download UI since reports depend on having data.

**Independent Test**: Can be fully tested by clicking the generate reports button in the web interface (assuming downloaded data exists) and verifying that the existing Python script executes successfully and produces the expected HTML reports, delivering immediate value by replacing command-line execution with a simple button click.

**Acceptance Scenarios**:

1. **Given** property data exists in one or more dated directories, **When** I click the "Generate Reports" button, **Then** the system processes all available data and shows a progress indicator
2. **Given** the report generation is running, **When** the process completes successfully, **Then** the system displays a success message with links to view the generated reports
3. **Given** the report generation is running, **When** an error occurs (e.g., missing Google Maps API key, corrupted data), **Then** the system displays a clear error message explaining the issue
4. **Given** no property data exists, **When** I click the "Generate Reports" button, **Then** the system displays a message indicating that data must be downloaded first

---

### User Story 3 - Monitor Script Execution Status (Priority: P3)

As a real estate analyst, I want to see real-time progress updates in the web interface while the underlying scripts are executing so that I know the system is working and can estimate completion time.

**Why this priority**: While helpful for user experience, this is a "nice to have" UI enhancement. The scripts work fine and provide console output; we're just making that output visible in the browser. This is lower priority than the basic button-to-script-execution functionality.

**Independent Test**: Can be fully tested by triggering either script via the web UI and verifying that console output from the Python scripts is captured and displayed in real-time in the browser, delivering value by reducing user anxiety during long-running script executions.

**Acceptance Scenarios**:

1. **Given** a download or report generation is in progress, **When** I view the status panel, **Then** I see which operation is running, how long it has been running, and an indication of progress
2. **Given** multiple operations have been performed, **When** I view the history panel, **Then** I see a log of past operations with timestamps, status (success/failure), and result summaries

---

### Edge Cases

- What happens when the user closes the browser while a download or report generation is in progress?
- How does the system handle concurrent requests (e.g., user clicks download twice rapidly)?
- What happens if the system runs out of disk space during data download?
- How does the system behave if required environment variables (API keys) are missing or invalid?
- What happens if the data files exist but are corrupted or incomplete?
- How does the system handle very large datasets that might take several minutes to process?

## Requirements *(mandatory)*

### Functional Requirements

**Server Requirements:**
- **FR-001**: System MUST provide a local web server accessible via browser at a configurable port (default: 8080)
- **FR-002**: Server MUST execute the existing data download script (src/homes/rentcast_homes.py) when requested via the web interface
- **FR-003**: Server MUST execute the existing report generation script (src/report/generate_reports.py) when requested via the web interface
- **FR-004**: Server MUST capture and stream output from the Python scripts back to the web interface in real-time
- **FR-005**: Server MUST prevent concurrent execution of the same script (e.g., prevent running download script twice simultaneously)
- **FR-006**: Server MUST start with a single, simple command
- **FR-007**: Server MUST automatically open the default browser to the web interface when started
- **FR-008**: Server MUST gracefully shut down and cleanup when stopped by the user

**Web Interface Requirements:**
- **FR-009**: Interface MUST display two primary action buttons: "Download Data" and "Generate Reports"
- **FR-010**: Interface MUST show real-time status updates during script execution (capturing script console output)
- **FR-011**: Interface MUST show success or failure messages after each script completes
- **FR-012**: Interface MUST display details about script results (e.g., number of listings downloaded, number of reports generated)
- **FR-013**: Interface MUST validate that required environment variables exist before triggering scripts (RENTCAST_API_KEY, GOOGLE_MAPS_API_KEY)
- **FR-014**: Interface MUST display error messages from the underlying Python scripts in a user-friendly format
- **FR-015**: Interface MUST provide direct links to view generated report HTML files
- **FR-016**: Interface MUST show operation history of past script executions with timestamps and results

### Key Entities

- **Script Execution**: Represents a web-triggered execution of an existing Python script. Key attributes include: script type (download/report), start time, end time, status (running/success/failure), captured output, error messages
- **DataSnapshot**: Represents the output from the download script - a dated directory of property data. Key attributes include: date, number of listings, zip codes covered, file location (created by existing script)
- **Report**: Represents the output from the report generation script - HTML files. Key attributes include: date, file location, number of properties analyzed (created by existing script)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can initiate data downloads and report generation in under 3 clicks from opening the browser
- **SC-002**: System provides clear feedback within 2 seconds of any button click (either progress indicator or error message)
- **SC-003**: Users can successfully complete both operations (download and generate) without consulting documentation or using the command line
- **SC-004**: 95% of users can successfully complete their first data download and report generation without assistance or documentation
- **SC-005**: System prevents user errors (e.g., running operations without prerequisites) through validation and clear messaging
- **SC-006**: Time from system start to ready-to-use interface is under 10 seconds

## Assumptions

- The user has Python and necessary dependencies already installed (as required by the existing scripts)
- The user will set required environment variables (RENTCAST_API_KEY, GOOGLE_MAPS_API_KEY) before starting the server
- The existing Python scripts (rentcast_homes.py and generate_reports.py) work correctly when called from the command line
- The web interface will run on localhost only (not exposed to external networks)
- Only one user will use the interface at a time (no multi-user concurrency needed)
- The browser supports modern web standards for real-time updates and interactive functionality

## Constraints

- **CRITICAL**: The solution MUST NOT modify the existing Python scripts (src/homes/rentcast_homes.py and src/report/generate_reports.py) - it only wraps and triggers them
- The solution MUST work with the scripts as they currently exist (no changes to script arguments, logic, or outputs)
- The solution must run entirely locally (no cloud deployment required)
- The interface should work on Windows (given the file paths in the codebase)

## Dependencies

- Existing Python scripts: src/homes/rentcast_homes.py and src/report/generate_reports.py
- Environment variables: RENTCAST_API_KEY and GOOGLE_MAPS_API_KEY
- Python dependencies as specified in project configuration
- Dated directory structure in .tmp/YYYYMMDD/ for data and reports

## Out of Scope

- **Modifying the existing Python scripts** - they are used as-is
- **Changing how data is downloaded or how reports are generated** - the existing logic is preserved
- Authentication or multi-user support
- Editing or modifying downloaded data through the interface
- Customizing report parameters or filtering criteria through the UI (scripts run with their default configurations)
- Scheduling automatic downloads or report generation
- Cloud deployment or remote access
- Mobile-responsive design (desktop browser assumed)
- Advanced error recovery or retry mechanisms beyond what the scripts already provide
- Data backup or archiving features
