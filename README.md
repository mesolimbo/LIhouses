# Long Island Houses

A modular Python toolkit for real estate analysis and transit-oriented development research in Long Island. Generate geospatial visualizations, fetch property data, and create professional reports combining transit accessibility with real estate metrics.

## Overview

This project provides standalone utilities for analyzing the intersection of public transit accessibility and real estate markets in Long Island, with focus on LIRR (Long Island Rail Road) station areas.

**Key Capabilities:**
- Generate walking radius maps around transit stations (KML/KMZ)
- Enrich geographic data with ZIP codes and location information
- Fetch and analyze property/rental market data by ZIP code
- Create professional HTML reports with embedded visualizations
- Automated report generation with historical tracking
- Web interface for easy data management (new!)

## Quick Start (Web Interface)

The easiest way to use LIhouses is through the web interface:

```bash
# 1. Install dependencies
make install

# 2. Configure API keys
cp .env.example .env
# Edit .env and add your actual API keys

# 3. Start the web interface
make web
```

Browser opens automatically at http://localhost:8080

**Makefile Commands:**
- `make web` or `make start` - Start the web interface
- Press `Ctrl+C` to stop the server
- `make install` - Install dependencies
- `make clean` - Remove temporary files

**Required Environment Variables (.env file):**
```bash
# RentCast API Key (for downloading property data)
RENTCAST_API_KEY=your_key_here

# Google Maps API Key (for generating reports)
GOOGLE_MAPS_API_KEY=your_key_here
```

Get keys from:
- RentCast: https://www.rentcast.io/
- Google Maps: https://console.cloud.google.com/

## Project Structure

```
LIhouses/
├── src/
│   ├── core/        # Core geospatial utilities
│   ├── homes/       # Property data fetching and processing
│   ├── report/      # Report generation and visualization
│   └── web/         # Web interface (Flask app)
├── data/            # Input datasets (MTA stations, ZIP codes, etc.)
├── .tmp/            # Generated outputs (reports, temp files)
├── Makefile         # Convenient commands
└── Pipfile          # Python dependencies
```

## Requirements

- **Python**: 3.13+
- **Environment**: Git Bash (Windows) or any Unix-like shell
- **Package Manager**: pipenv
- **API Keys**:
  - Google Maps API (for geocoding/ZIP enrichment)
  - Rentcast API (for property data, optional)

## Setup

1. **Clone the repository** (or navigate to project directory)

2. **Install dependencies:**
   ```bash
   pipenv install
   ```

3. **Configure API keys:**
   Create a `.env` file in the project root:
   ```bash
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   RENTCAST_API_KEY=your_rentcast_api_key_here
   ```

4. **Verify data files:**
   Ensure required data files exist in `data/`:
   - `MTA_Rail_Stations_20250913.csv` (or download latest from [data.ny.gov](https://data.ny.gov/Transportation/MTA-Rail-Stations/wxmd-5cpm/data_preview))
   - `zipcodes.txt` (optional: filter for specific ZIP codes)

## Modules

### 1. KML/KMZ Generation (`src/core/generate_kml.py`)

Generate walking radius circles around transit stations for visualization in Google Earth or My Maps.

**Features:**
- Creates 15-minute walking circles (configurable radius)
- Outputs both KML and KMZ formats
- Semi-transparent styled polygons

**Usage:**
```bash
pipenv run python src/core/generate_kml.py
```

**Configuration** (edit script constants):
- `RADIUS_M`: Walking radius in meters (default: 1207m ≈ 15 min)
- `POINTS`: Circle smoothness (default: 64)
- `MAKE_KMZ`: Create compressed KMZ file (default: True)

**Output:** `data/lirr_15min_walk_circles.{kml,kmz}`

---

### 2. ZIP Code Enrichment (`src/core/zipenrich.py`)

Enrich CSV data with ZIP codes using reverse geocoding from latitude/longitude coordinates.

**Features:**
- Google Maps API integration
- Adds ZIP code, city, state, formatted address
- Batch processing with rate limiting

**Usage:**
```bash
pipenv run python src/core/zipenrich.py
```

**Requirements:**
- Input CSV must have `Latitude` and `Longitude` columns
- `GOOGLE_MAPS_API_KEY` environment variable

**Output:** `data/MTA_Rail_Stations_with_zip.csv`

---

### 3. Property Data Fetching (`src/homes/rentcast_homes.py`)

Fetch rental and property market data for ZIP codes using the Rentcast API.

**Features:**
- Parallel API requests for performance
- ZIP code filtering (Long Island focus)
- Comprehensive property metrics (listings, prices, trends)
- CSV output with timestamped filenames

**Usage:**
```bash
pipenv run python src/homes/rentcast_homes.py
```

**Requirements:**
- `RENTCAST_API_KEY` environment variable
- `data/MTA_Rail_Stations_with_zip.csv` (enriched station data)
- `data/zipcodes.txt` (optional filter)

**Output:** `.tmp/YYYYMMDD/homes-{timestamp}.csv`

---

### 4. Report Generation (`src/report/generate_reports.py`)

Generate professional HTML reports with embedded visualizations from property data.

**Features:**
- Automated scanning of dated directories in `.tmp/`
- Matplotlib/Seaborn visualizations (embedded as base64)
- Interactive maps with property markers
- Statistics and trend analysis
- Index page with links to all reports

**Usage:**
```bash
pipenv run python src/report/generate_reports.py
```

**Input:** Looks for `homes-*.csv` files in `.tmp/YYYYMMDD/` directories

**Output:**
- `.tmp/YYYYMMDD/real_estate_report_YYYYMMDD.html` (per-date reports)
- `.tmp/index.html` (index of all reports)

## Typical Workflow

1. **Generate transit station KML** (one-time or when data updates):
   ```bash
   pipenv run python src/core/generate_kml.py
   ```

2. **Enrich stations with ZIP codes** (if not already done):
   ```bash
   pipenv run python src/core/zipenrich.py
   ```

3. **Fetch current property data:**
   ```bash
   pipenv run python src/homes/rentcast_homes.py
   ```

4. **Generate HTML reports:**
   ```bash
   pipenv run python src/report/generate_reports.py
   ```

5. **View reports:** Open `.tmp/index.html` in your browser

## Data Sources

- **MTA Rail Stations**: [data.ny.gov](https://data.ny.gov/Transportation/MTA-Rail-Stations/wxmd-5cpm/data_preview)
- **Geocoding**: Google Maps Geocoding API
- **Property Data**: Rentcast API

## Configuration

### Environment Variables

Create `.env` file in project root:
```bash
GOOGLE_MAPS_API_KEY=your_key_here
RENTCAST_API_KEY=your_key_here
```

### Customization

Each module can be customized by editing constants at the top of the script:
- Walking radius and circle styling (generate_kml.py)
- API rate limits and batch sizes (rentcast_homes.py)
- Visualization styles and colors (generate_reports.py)

## Output Files

All generated files are stored in `.tmp/` and excluded from git:

- **KML/KMZ files**: `data/` (committed for reuse)
- **Property data CSVs**: `.tmp/YYYYMMDD/homes-*.csv`
- **HTML reports**: `.tmp/YYYYMMDD/real_estate_report_YYYYMMDD.html`
- **Report index**: `.tmp/index.html`

## Deployment

The generated KML/KMZ files and CSV data can be:
- Loaded into Google My Maps for visualization
- Imported into GIS applications (QGIS, ArcGIS)
- Shared as downloadable assets
- Used in web mapping applications

## Development

See [`.specify/memory/constitution.md`](.specify/memory/constitution.md) for architectural principles and development standards.

**Key Principles:**
- Module-first architecture (each script runs independently)
- pipenv for dependency management
- Git Bash compatibility
- Data/output separation
- Professional, reproducible outputs

## License

See LICENSE file for details.

## Notes

- All modules designed to run independently via CLI
- API keys required for Google Maps and Rentcast integration
- Generated outputs are timestamped for historical tracking
- ZIP code filtering focuses on Long Island region
