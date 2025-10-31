# Feature Specification: SFTP Report Upload

**Feature Branch**: `001-sftp-report-upload`
**Created**: 2025-10-30
**Status**: Draft
**Input**: User description: "Add a script that can automatically upload the reports generated to an SFTP host. I will provide the script with a host, port (default 22), username, and password via env vars. The script is only to upload html files. It should always update index html, but it should only upload individual reports and their date directories if they aren't already preset in the host server."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Main Index (Priority: P1)

As a report administrator, I want to upload the main index.html file to the SFTP server so that users can access the latest list of available reports.

**Why this priority**: This is the entry point for all reports and must be kept up-to-date. Without this, users cannot discover available reports.

**Independent Test**: Can be fully tested by running the upload script and verifying that index.html exists on the SFTP server with the latest content.

**Acceptance Scenarios**:

1. **Given** an index.html file exists in .tmp/, **When** the upload script runs, **Then** index.html is uploaded to the SFTP server root directory
2. **Given** index.html already exists on the SFTP server, **When** the upload script runs, **Then** the existing index.html is overwritten with the latest version
3. **Given** SFTP credentials are valid, **When** the upload script runs, **Then** the script connects successfully and uploads the file

---

### User Story 2 - Upload New Report Directories (Priority: P2)

As a report administrator, I want to upload new dated report directories (e.g., 20251026/) with their HTML reports to the SFTP server so that new reports are available to users while avoiding redundant uploads.

**Why this priority**: This ensures new reports are made available while efficiently handling existing reports.

**Independent Test**: Can be tested by creating a new dated directory with a report, running the script, and verifying the directory appears on the SFTP server.

**Acceptance Scenarios**:

1. **Given** a dated directory (e.g., 20251026/) exists locally but not on SFTP, **When** the upload script runs, **Then** the directory is created on the SFTP server and HTML files are uploaded
2. **Given** a dated directory exists both locally and on SFTP, **When** the upload script runs, **Then** the directory is skipped and no files are re-uploaded
3. **Given** a dated directory contains HTML and non-HTML files, **When** the upload script runs, **Then** only HTML files are uploaded
4. **Given** multiple new dated directories exist, **When** the upload script runs, **Then** all new directories are uploaded with their HTML reports

---

### User Story 3 - Handle Connection Errors Gracefully (Priority: P3)

As a report administrator, I want the upload script to handle connection errors gracefully and provide clear error messages so that I can diagnose and fix issues quickly.

**Why this priority**: Error handling is important for reliability but the core functionality (uploading) is more critical.

**Independent Test**: Can be tested by providing invalid credentials or an unreachable host and verifying error messages are clear and helpful.

**Acceptance Scenarios**:

1. **Given** invalid SFTP credentials, **When** the upload script runs, **Then** a clear authentication error message is displayed
2. **Given** an unreachable SFTP host, **When** the upload script runs, **Then** a clear connection error message is displayed
3. **Given** insufficient permissions on SFTP server, **When** the upload script runs, **Then** a clear permission error message is displayed
4. **Given** a network interruption during upload, **When** the connection is lost, **Then** the script reports which files were successfully uploaded and which failed

---

### Edge Cases

- What happens when .tmp/ directory doesn't exist?
  - Script should exit gracefully with a clear error message indicating no reports found

- What happens when index.html doesn't exist but dated directories do?
  - Script should warn but continue uploading dated directories

- What happens when a dated directory has no HTML files?
  - Script should skip the directory and log a warning

- What happens when SFTP server runs out of disk space during upload?
  - Script should catch the error, report which file failed, and exit gracefully

- What happens when required environment variables are missing?
  - Script should exit immediately with clear error message listing missing variables

- What happens when port is not a valid number?
  - Script should validate and default to 22, or exit with error if invalid

- What happens when uploading very large HTML files?
  - Script should handle large files without timeout issues (configurable timeout if needed)

- What happens when SFTP directory structure doesn't exist?
  - Script should create necessary directories on the SFTP server

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Script MUST read SFTP connection details from environment variables: SFTP_HOST, SFTP_PORT (default 22), SFTP_USERNAME, SFTP_PASSWORD
- **FR-002**: Script MUST validate that required environment variables (SFTP_HOST, SFTP_USERNAME, SFTP_PASSWORD) are set before attempting connection
- **FR-003**: Script MUST connect to the SFTP server using the provided credentials
- **FR-004**: Script MUST always upload index.html from .tmp/ directory to the SFTP server root, overwriting if it already exists
- **FR-005**: Script MUST scan for dated directories (YYYYMMDD format) in .tmp/ directory
- **FR-006**: Script MUST check if each dated directory already exists on the SFTP server before uploading
- **FR-007**: Script MUST only upload dated directories that do not already exist on the SFTP server
- **FR-008**: Script MUST only upload files with .html extension (case-insensitive)
- **FR-009**: Script MUST skip non-HTML files (JSON, CSV, etc.) in dated directories
- **FR-010**: Script MUST create directories on the SFTP server if they don't exist
- **FR-011**: Script MUST provide clear success/failure messages for each upload operation
- **FR-012**: Script MUST exit with appropriate error code (non-zero) on failure
- **FR-013**: Script MUST be executable as a standalone Python script
- **FR-014**: Script MUST use secure SFTP protocol (not plain FTP)

### Key Entities *(include if feature involves data)*

- **Report Index**: The main index.html file that lists all available reports. Located at .tmp/index.html locally and root of SFTP server remotely. Always uploaded to ensure users see the latest report list.

- **Dated Report Directory**: Directory named in YYYYMMDD format (e.g., 20251026/) containing HTML reports and supporting files for a specific date. Contains:
  - One HTML report file (e.g., real_estate_report_20251026.html)
  - Supporting CSV and JSON files (not uploaded to SFTP)

- **SFTP Connection**: Represents the connection to the remote SFTP server. Configured via environment variables (host, port, username, password). Used to upload files and check for existing directories.

- **Upload Manifest**: Implicit list of files to be uploaded, determined by:
  - index.html (always included)
  - Dated directories that don't exist on SFTP server (filtered to only HTML files)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Script successfully uploads index.html to SFTP server in under 30 seconds
- **SC-002**: Script correctly identifies and skips existing dated directories 100% of the time
- **SC-003**: Script only uploads HTML files, skipping 100% of non-HTML files (CSV, JSON, etc.)
- **SC-004**: Script provides clear success/failure feedback for every upload operation
- **SC-005**: Script handles connection failures gracefully, exiting with appropriate error codes
- **SC-006**: Script can be run multiple times without creating duplicate files or directories on SFTP server
- **SC-007**: Administrator can configure SFTP connection using only environment variables, without modifying code
- **SC-008**: Script completes full upload of 10 dated directories (each with 1 HTML file) in under 2 minutes
