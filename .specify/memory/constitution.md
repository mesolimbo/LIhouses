# LIhouses Project Constitution

## Core Principles

### I. Module-First Architecture
Every feature starts as a standalone, executable module in `src/`:
- Modules must be self-contained with clear single responsibility
- Each module runnable independently via command line
- Organize by function (core/, homes/, report/, etc.)
- Clear purpose required - no organizational-only modules
- Module dependencies must be explicit and minimal

### II. Dual Interface Pattern
All functionality accessible via both CLI and web GUI:
- **CLI**: Direct script execution via pipenv for automation/batch processing
- **Web GUI**: Flask-based single-page app for interactive use
- Same business logic shared between both interfaces
- Web interface wraps existing modules, doesn't duplicate logic

### III. Environment & Dependencies (NON-NEGOTIABLE)
Strict dependency management using pipenv:
- Python 3.13+ required
- All dependencies pinned with exact versions in Pipfile
- Use `pipenv install` for setup, `pipenv run` for execution
- NO global Python package installations
- Dev dependencies separated from production dependencies
- Lock file (Pipfile.lock) must be committed

### IV. Data Separation
Clear boundary between code, data, and outputs:
- **data/**: Input files (CSV, external datasets) - committed to repo
- **.tmp/**: Generated outputs, reports, temp files - NOT committed
- **src/**: Source code only, no hardcoded data
- Use relative paths from module location for portability
- Configuration via environment variables or config files when needed

### V. Git Bash Compatibility
Windows Git Bash as primary development environment:
- Use forward slashes or `os.path.join()` for paths
- Scripts must work in Git Bash shell
- Avoid Windows-specific commands in scripts
- Test all automation in Git Bash before committing
- Use `#!/usr/bin/env python3` shebangs for CLI executables

### VI. Output Quality & Reproducibility
Generated artifacts must be professional and reproducible:
- HTML reports with embedded visualizations (no external file dependencies)
- KML/KMZ files follow standard specifications
- Consistent file naming: `{type}_{date}.{ext}` format
- Include metadata (generation timestamp, parameters used)
- Visualizations use seaborn/matplotlib with consistent styling

### VII. Minimal External Dependencies
Prefer standard library when possible:
- Use built-in modules (csv, json, os, pathlib) over third-party when adequate
- Only add dependencies that provide significant value
- Document why each external dependency is necessary
- Regularly audit and remove unused dependencies

## Development Workflow

### Version Control
- **main** branch is stable, always deployable
- Feature branches for development work
- Descriptive commit messages following conventional commits style
- .gitignore must exclude:
  - `.tmp/` (generated outputs)
  - `.idea/` (IDE settings)
  - `__pycache__/`, `*.pyc` (Python artifacts)
  - `.env` (environment secrets)
  - Any API keys or credentials

### Code Organization
```
LIhouses/
├── src/
│   ├── core/        # Core utilities (KML generation, data enrichment)
│   ├── homes/       # Property data fetching/processing
│   ├── report/      # Report generation
│   └── web/         # Flask app
├── data/            # Input datasets (committed)
├── .tmp/            # Generated outputs (NOT committed)
├── Pipfile          # Dependency specifications
└── README.md        # Project documentation
```

### Testing Strategy
- Manual testing in Git Bash before committing
- Test with real data samples in data/
- Verify generated outputs in .tmp/
- Check cross-platform path handling
- Validate HTML/KML output in target applications (browsers, Google Earth, My Maps)

### Flask Web Application (When Implemented)
- Single-page application in `src/web/`
- Templates in `src/web/templates/`
- Static assets in `src/web/static/`
- Routes call existing module functions (no business logic duplication)
- Development server only (not for production deployment)
- Simple, accessible UI for running utilities with parameters

## API & External Services

### API Key Management
- Store API keys in `.env` file (NOT committed)
- Use `python-dotenv` for environment variable loading
- Document required API keys in README
- Provide `.env.example` template without actual keys
- Never hardcode keys in source files

### Data Sources
- Document data source URLs and update frequency
- Cache external API responses appropriately
- Handle API rate limits gracefully
- Provide fallback for offline development when possible

## Quality Standards

### Code Style
- Follow PEP 8 style guidelines
- Use descriptive variable names
- Add docstrings to modules and functions
- Comments explain "why", not "what"
- Keep functions focused and under 50 lines when possible

### Error Handling
- Graceful failure with informative error messages
- Validate inputs before processing
- Log errors to stderr, outputs to stdout
- Provide helpful usage messages for CLI scripts

### Documentation
- README.md kept current with features and usage
- Inline comments for complex algorithms
- Document assumptions about data formats
- Include example commands and expected outputs

## Governance

This constitution defines the architectural principles and development standards for the LIhouses project. All code contributions, refactoring, and new features must align with these principles.

### Amendment Process
- Constitution changes require updating this document
- Breaking changes to module interfaces need migration plan
- Document rationale for any principle violations

### Review Checklist
Before committing code, verify:
- [ ] Works in Git Bash environment
- [ ] Dependencies properly specified in Pipfile
- [ ] Generated files excluded via .gitignore
- [ ] No hardcoded paths or credentials
- [ ] Module can run independently
- [ ] README updated if user-facing changes

**Version**: 1.0.0 | **Ratified**: 2025-10-24 | **Last Amended**: 2025-10-24
