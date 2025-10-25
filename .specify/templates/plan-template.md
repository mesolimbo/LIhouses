# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

**Language/Version**: Python 3.13+
**Package Manager**: pipenv (dependencies pinned in Pipfile)
**Primary Dependencies**: pandas, numpy, matplotlib, seaborn, googlemaps, requests
**Storage**: CSV files in data/, generated outputs in .tmp/
**Testing**: Manual testing in Git Bash + output validation
**Target Platform**: Git Bash (Windows), cross-platform Python
**Execution**: CLI via `pipenv run python src/[module]/[script].py`
**Project Type**: Modular CLI utilities (future: Flask web wrapper)
**Performance Goals**: [Specify if applicable, e.g., process 100 stations in <30s or N/A]
**Constraints**: [Specify if applicable, e.g., API rate limits, memory for visualizations or N/A]
**Scale/Scope**: [Specify feature scope, e.g., handle 50 ZIP codes, 10 LIRR stations or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with [LIhouses Constitution](../.specify/memory/constitution.md):

- [ ] **Module-First Architecture**: Is this implemented as standalone module(s) in `src/`?
- [ ] **Dual Interface**: Can this run via CLI (pipenv run) AND will support future Flask GUI?
- [ ] **Dependencies**: Are all new dependencies pinned in Pipfile with exact versions?
- [ ] **Data Separation**: Does this respect data/ (inputs), .tmp/ (outputs), src/ (code only)?
- [ ] **Git Bash Compatibility**: Uses `os.path.join()` or forward slashes, no Windows-specific commands?
- [ ] **Output Quality**: Does this generate professional, reproducible outputs with metadata?
- [ ] **Minimal Dependencies**: Have simpler stdlib alternatives been rejected with justification?
- [ ] **API Keys**: Are secrets stored in .env (not committed), documented in README?
- [ ] **Code Style**: Follows PEP 8, includes docstrings, comments explain "why"?
- [ ] **Testing**: Includes manual test plan for Git Bash execution?

**Violations requiring justification**: Document in Complexity Tracking table below

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Map feature to appropriate module(s) in LIhouses structure.
  Choose the module category that best fits this feature.
-->

```text
LIhouses/
├── src/
│   ├── core/        # Core utilities (KML generation, data enrichment)
│   │   └── [feature].py
│   ├── homes/       # Property data fetching/processing
│   │   └── [feature].py
│   ├── report/      # Report generation & visualization
│   │   └── [feature].py
│   └── web/         # Flask app (future - GUI wrappers only)
│       ├── app.py
│       ├── templates/
│       └── static/
├── data/            # Input datasets (committed to repo)
│   ├── [input_files].csv
│   └── [config_files].txt
└── .tmp/            # Generated outputs (NOT committed)
    └── YYYYMMDD/
        └── [outputs]
```

**Module Selection**:
- **core/**: Geospatial utilities, data transformation, KML/KMZ generation
- **homes/**: API integration, property data fetching, market analysis
- **report/**: HTML generation, visualizations, report aggregation
- **web/**: Flask routes that call existing modules (no business logic)

**Structure Decision**: [Select the module(s) where this feature belongs and
document any new files to be created]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
