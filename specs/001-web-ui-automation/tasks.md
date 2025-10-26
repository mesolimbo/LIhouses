# Tasks: Local Web Interface for Existing Data Scripts

**Feature**: 001-web-ui-automation
**Input**: Design documents from `/specs/001-web-ui-automation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: NOT requested in spec - manual testing only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create src/web/ directory for Flask web interface module
- [X] T002 Add Flask==3.1.2 to Pipfile dependencies
- [X] T003 [P] Create .env.example template file with RENTCAST_API_KEY and GOOGLE_MAPS_API_KEY placeholders in project root
- [X] T004 [P] Verify .env is in .gitignore to prevent committing API keys

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Flask server infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create src/web/app.py with basic Flask app skeleton and route structure
- [X] T006 [P] Create src/web/templates/ directory for HTML templates
- [X] T007 [P] Create src/web/static/ directory for CSS and JavaScript files
- [X] T008 Create src/web/executor.py with script execution logic using subprocess.Popen
- [X] T009 Add global execution_state dictionary to app.py for tracking running operations
- [ ] T012 Add environment variable loading using python-dotenv in src/web/app.py
- [ ] T013 Implement validate_env_vars() function in src/web/app.py for API key validation
- [ ] T014 Add webbrowser.open() call in src/web/app.py to auto-open browser on server startup

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Trigger Data Download via Web UI (Priority: P1) 🎯 MVP

**Goal**: Enable users to trigger the existing data download script (src/homes/rentcast_homes.py) through a web button instead of command line, making it accessible to non-technical users

**Independent Test**: Start web server, click "Download Data" button in browser, verify that rentcast_homes.py executes successfully and produces expected CSV files in .tmp/YYYYMMDD/ directory

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create src/web/templates/index.html with basic HTML structure and Download Data button
- [ ] T016 [P] [US1] Create src/web/static/style.css with minimal styling for buttons and layout
- [ ] T017 [P] [US1] Create src/web/static/script.js with button click event handler skeleton
- [ ] T018 [US1] Implement GET / route in src/web/app.py to serve index.html template
- [ ] T019 [US1] Implement POST /api/execute route in src/web/app.py with input validation for operation_type
- [ ] T020 [US1] Add concurrency check in POST /api/execute to prevent running multiple operations simultaneously
- [ ] T021 [US1] Add environment variable validation for RENTCAST_API_KEY in POST /api/execute before triggering download
- [ ] T022 [US1] Implement execute_script() function in src/web/executor.py to run download script as subprocess
- [ ] T023 [US1] Create Operation data structure in src/web/executor.py with id, type, status, start_time, output_lines fields
- [ ] T024 [US1] Implement _capture_output() thread function in src/web/executor.py to read stdout/stderr line-by-line
- [ ] T025 [US1] Store running operation in execution_state global dictionary in src/web/app.py
- [ ] T026 [US1] Implement executeOperation('download') function in src/web/static/script.js to POST to /api/execute
- [ ] T027 [US1] Add button disable logic in src/web/static/script.js during operation execution
- [ ] T028 [US1] Add success message display in src/web/static/script.js when operation completes
- [ ] T029 [US1] Add error message display in src/web/static/script.js when operation fails
- [ ] T031 [US1] Test in Git Bash: pipenv run python src/web/app.py, click Download Data button, verify CSV output in .tmp/

**Checkpoint**: At this point, User Story 1 should be fully functional - users can trigger data downloads via web button

---

## Phase 4: User Story 2 - Trigger Report Generation via Web UI (Priority: P2)

**Goal**: Enable users to trigger the existing report generation script (src/report/generate_reports.py) through a web button, making report creation accessible without command line

**Independent Test**: Start web server with existing downloaded data, click "Generate Reports" button in browser, verify that generate_reports.py executes successfully and produces expected HTML reports in .tmp/YYYYMMDD/ directory

### Implementation for User Story 2

- [ ] T032 [P] [US2] Add Generate Reports button to src/web/templates/index.html
- [ ] T033 [US2] Add environment variable validation for GOOGLE_MAPS_API_KEY in POST /api/execute before triggering generate
- [ ] T034 [US2] Map "generate" operation type to src/report/generate_reports.py path in src/web/executor.py
- [ ] T035 [US2] Add executeOperation('generate') button handler in src/web/static/script.js
- [ ] T036 [US2] Implement output parsing in src/web/executor.py to extract report file paths from script output
- [ ] T037 [US2] Display clickable report links in success message in src/web/static/script.js
- [ ] T038 [US2] Add validation in POST /api/execute to check if data exists before allowing report generation
- [ ] T039 [US2] Test in Git Bash: click Generate Reports button, verify HTML reports created in .tmp/

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - full download and report workflow via web UI

---

## Phase 5: User Story 3 - Monitor Script Execution Status (Priority: P3)

**Goal**: Show real-time progress updates in the web interface so users know scripts are working and can estimate completion time

**Independent Test**: Trigger either script via web UI, verify that console output from Python scripts is captured and displayed in real-time in the browser

### Implementation for User Story 3

- [ ] T040 [P] [US3] Add log viewer section to src/web/templates/index.html with scrollable output area
- [ ] T042 [P] [US3] Style log viewer with monospace font and scrolling in src/web/static/style.css
- [ ] T044 [US3] Implement GET /api/stream/<operation_id> route in src/web/app.py for Server-Sent Events
- [ ] T045 [US3] Implement event_stream() generator function in src/web/app.py to yield SSE events
- [ ] T046 [US3] Add heartbeat events (every 15 seconds) to SSE stream in src/web/app.py to prevent connection drops
- [ ] T047 [US3] Send 'output' events for each new line of script output in src/web/app.py
- [ ] T048 [US3] Send 'completed' event with result summary when script succeeds in src/web/app.py
- [ ] T049 [US3] Send 'failed' event with error message when script fails in src/web/app.py
- [ ] T050 [US3] Implement streamOperationOutput() function in src/web/static/script.js using EventSource API
- [ ] T051 [US3] Add event listener for 'output' events to append lines to log viewer in src/web/static/script.js
- [ ] T052 [US3] Add event listener for 'completed' events to show success message in src/web/static/script.js
- [ ] T053 [US3] Add event listener for 'failed' events to show error message in src/web/static/script.js
- [ ] T057 [US3] Implement GET /api/status route in src/web/app.py to return current running operation
- [ ] T058 [US3] Implement checkServerStatus() function in src/web/static/script.js to poll server status on page load
- [ ] T059 [US3] Auto-reconnect to SSE stream if operation was running when page loaded in src/web/static/script.js
- [ ] T060 [US3] Test real-time streaming: trigger download, watch output appear line-by-line in browser

**Checkpoint**: All user stories should now be independently functional - complete web UI with real-time feedback

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure production-ready quality

- [ ] T061 [P] Add comprehensive error handling for all subprocess exceptions in src/web/executor.py
- [ ] T062 [P] Add proper logging to stderr for server errors in src/web/app.py
- [ ] T063 Add timeout handling (30 minutes default) for long-running scripts in src/web/executor.py
- [ ] T064 [P] Ensure all file paths use os.path.join() for cross-platform compatibility in src/web/app.py and src/web/executor.py
- [ ] T065 [P] Add CORS headers to Flask responses in src/web/app.py for strict browser compatibility
- [ ] T066 Add limit of 1000 lines for operation output_lines to prevent memory issues in src/web/executor.py
- [ ] T068 [P] Add module docstrings to src/web/app.py and src/web/executor.py explaining purpose and usage
- [ ] T069 [P] Add inline comments for complex streaming logic in src/web/app.py
- [ ] T070 Verify PEP 8 compliance for all Python files in src/web/ using ruff check
- [ ] T071 [P] Add startup message to console showing server URL in src/web/app.py
- [ ] T072 [P] Add graceful shutdown message in src/web/app.py
- [ ] T073 Test edge case: Close browser during download, verify script continues running
- [ ] T074 Test edge case: Click download button twice rapidly, verify second request is rejected
- [ ] T075 Test edge case: Missing RENTCAST_API_KEY, verify clear error message before script runs
- [ ] T076 Test edge case: Missing GOOGLE_MAPS_API_KEY, verify clear error message before script runs
- [ ] T077 Test edge case: No data exists, verify generate reports shows helpful message
- [ ] T079 [P] Update project README.md with web interface usage instructions
- [ ] T080 [P] Add example commands to start web server in README.md
- [ ] T081 Run pipenv install clean test on fresh environment to verify dependencies
- [ ] T082 Verify web UI works in Chrome, Firefox, and Edge browsers
- [ ] T083 Final end-to-end test: Download data → Generate reports → Verify all outputs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independently testable with pre-existing data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 and US2 but doesn't block them

### Within Each User Story

- HTML/CSS/JS files can be created in parallel (marked [P])
- Backend routes depend on executor.py being implemented
- Frontend JavaScript depends on backend routes being available
- Testing requires all story tasks to be complete

### Parallel Opportunities

- Phase 1: T003 and T004 can run in parallel
- Phase 2: T006, T007, and T010 can run in parallel
- User Story 1: T015, T016, T017 can run in parallel (different files)
- User Story 2: T032 can run in parallel with backend work
- User Story 3: T040, T041, T042, T043 can run in parallel (different sections/files)
- Polish: All tasks marked [P] can run in parallel (different files, documentation)

---

## Parallel Example: User Story 1

```bash
# Launch HTML, CSS, and JavaScript file creation together:
Task T015: "Create src/web/templates/index.html with basic HTML structure"
Task T016: "Create src/web/static/style.css with minimal styling"
Task T017: "Create src/web/static/script.js with button click handlers"

# These can all be worked on simultaneously as they are different files
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T014) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T015-T031)
4. **STOP and VALIDATE**: Test download functionality independently
5. Deploy/demo if ready - this alone delivers value!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - download via web!)
3. Add User Story 2 → Test independently → Deploy/Demo (full workflow - download + reports!)
4. Add User Story 3 → Test independently → Deploy/Demo (enhanced UX - real-time feedback!)
5. Polish phase → Production ready
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (download UI)
   - Developer B: User Story 2 (reports UI)
   - Developer C: User Story 3 (streaming)
3. Stories integrate smoothly due to modular design

---

## Summary

- **Total Tasks**: 83
- **User Story 1 (P1)**: 17 tasks - Download data via web button
- **User Story 2 (P2)**: 8 tasks - Generate reports via web button
- **User Story 3 (P3)**: 21 tasks - Real-time monitoring
- **Setup + Foundational**: 14 tasks - Required before any stories
- **Polish**: 23 tasks - Production readiness
- **Parallel Opportunities**: 29 tasks marked [P] can run concurrently
- **Suggested MVP Scope**: Setup + Foundational + User Story 1 (31 tasks)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story (US1, US2, US3) for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Manual testing in Git Bash and browser - no automated test framework needed
- Existing scripts (rentcast_homes.py, generate_reports.py) remain UNCHANGED
