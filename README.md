# LIRR Walking Distance Map

A Python script that generates KML/KMZ files showing 15-minute walking radius circles around Long Island Rail Road (LIRR) stations.

## Overview

This tool creates visual maps showing walkable areas around LIRR stations, useful for:
- Transit-oriented development planning
- Real estate analysis
- Urban planning and accessibility studies
- Understanding walkable catchment areas for public transit

## Features

- Generates 15-minute walking circles (approximately 1,207 meters at 3 mph)
- Creates both KML and KMZ output formats
- Semi-transparent circles with customizable styling
- Works with MTA Rail Stations CSV data

## Requirements

- Python 3.13+
- MTA Rail Stations CSV file ([exported from data.ny.gov](https://data.ny.gov/Transportation/MTA-Rail-Stations/wxmd-5cpm/data_preview))

## Usage

1. Download the MTA Rail Stations CSV file and place it in the project directory
2. Update the `IN_CSV` variable in `generate_kml.py` if your CSV filename differs
3. Run the script:

```bash
pipenv install
pipenv run python generate_kml.py
```

## Configuration

Edit `generate_kml.py` to customize:
- `RADIUS_M`: Walking radius in meters (default: 1,207m ≈ 15 min walk)
- `POINTS`: Circle smoothness (default: 64 points)
- `MAKE_KMZ`: Whether to create KMZ file (default: True)

## Output

The script generates:
- `lirr_15min_walk_circles.kml`: KML file for Google Earth, mapping applications
- `lirr_15min_walk_circles.kmz`: Compressed KMZ version

## File Structure

- `generate_kml.py`: Main script
- `MTA_Rail_Stations_20250913.csv`: Station data (CSV format)
- `Pipfile`: Python dependencies
- Generated output files (KML/KMZ)

## Deployment

The raw CSV and the generated KML/KMZ files can be loaded as layers in Google's [My Maps](https://mymaps.google.com/) tool for visualization.