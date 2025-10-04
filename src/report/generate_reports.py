#!/usr/bin/env python3
"""
Automated Real Estate Report Generator

This script scans dated directories in .tmp/ and generates professional HTML reports
for each day's data. Also creates/updates an index.html with links to all reports.

Usage:
    python generate_reports.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime
from pathlib import Path
import base64
import io
import glob
import xml.etree.ElementTree as ET
import json

def get_dated_directories(base_tmp_dir):
    """Find all dated directories (YYYYMMDD format) in .tmp/"""
    dated_dirs = []

    if not os.path.exists(base_tmp_dir):
        print(f"Error: {base_tmp_dir} does not exist")
        return dated_dirs

    for item in os.listdir(base_tmp_dir):
        item_path = os.path.join(base_tmp_dir, item)
        # Check if it's a directory and matches YYYYMMDD format
        if os.path.isdir(item_path) and len(item) == 8 and item.isdigit():
            dated_dirs.append((item, item_path))

    # Sort by date (newest first)
    dated_dirs.sort(reverse=True)
    return dated_dirs

def find_homes_csv(directory):
    """Find the homes-*.csv file in a directory"""
    csv_files = glob.glob(os.path.join(directory, "homes-*.csv"))
    return csv_files[0] if csv_files else None

def parse_kml_circles(kml_file):
    """Parse KML file to extract station walking circles (name and radius only)"""
    circles = {}

    try:
        tree = ET.parse(kml_file)
        root = tree.getroot()

        # Handle KML namespace - use HTTPS (not HTTP!)
        ns = {'kml': 'https://www.opengis.net/kml/2.2'}

        # Find all placemarks
        placemarks = root.findall('.//kml:Placemark', ns)
        if not placemarks:
            # Try without namespace
            placemarks = root.findall('.//Placemark')

        for placemark in placemarks:
            # Get name
            name_elem = placemark.find('kml:name', ns)
            if name_elem is None:
                name_elem = placemark.find('name')
            if name_elem is None:
                continue

            station_name = name_elem.text

            # Get radius from ExtendedData
            radius_elem = placemark.find('.//kml:Data[@name="radius_m"]/kml:value', ns)
            if radius_elem is None:
                radius_elem = placemark.find('.//Data[@name="radius_m"]/value')
            if radius_elem is None:
                continue

            radius_m = float(radius_elem.text)

            # Store just the name and radius - we'll get coordinates from stations
            circles[station_name] = {
                'radius_m': radius_m
            }

    except Exception as e:
        print(f"  Warning: Could not parse KML file: {e}")
        import traceback
        traceback.print_exc()

    return circles

def load_station_data(stations_csv, allowed_zips=None):
    """Load station data from CSV"""
    stations = []

    try:
        df = pd.read_csv(stations_csv)
        total_count = 0
        filtered_count = 0

        for _, row in df.iterrows():
            zip_code = str(row.get('Zip Code', '')).strip()
            total_count += 1

            # Filter by allowed zips if provided
            if allowed_zips and zip_code not in allowed_zips:
                filtered_count += 1
                continue

            if zip_code and zip_code not in ['N/A', 'ERROR']:
                stations.append({
                    'name': row.get('Station Name', ''),
                    'lat': float(row.get('Latitude', 0)),
                    'lng': float(row.get('Longitude', 0)),
                    'branch': row.get('Branch', ''),
                    'zip': zip_code
                })

        if allowed_zips:
            print(f"  Station filtering: {total_count} total, {filtered_count} filtered out, {len(stations)} kept")

    except Exception as e:
        print(f"  Warning: Could not load station data: {e}")
        import traceback
        traceback.print_exc()

    return stations

def report_exists(directory):
    """Check if an HTML report already exists in the directory"""
    html_files = glob.glob(os.path.join(directory, "real_estate_report_*.html"))
    return len(html_files) > 0

def clean_data(df, price_col, sqft_col, zip_col):
    """Clean and prepare data for analysis"""
    analysis_df = df.copy()

    # Convert to numeric
    analysis_df[price_col] = pd.to_numeric(analysis_df[price_col], errors='coerce')
    analysis_df[sqft_col] = pd.to_numeric(analysis_df[sqft_col], errors='coerce')

    # Remove rows with missing or invalid data
    initial_count = len(analysis_df)
    analysis_df = analysis_df.dropna(subset=[price_col, sqft_col])
    analysis_df = analysis_df[(analysis_df[price_col] > 0) & (analysis_df[sqft_col] > 0)]
    final_count = len(analysis_df)

    # Calculate price per square foot
    analysis_df['price_per_sqft'] = analysis_df[price_col] / analysis_df[sqft_col]

    print(f"  Data cleaning: {initial_count} -> {final_count} rows ({initial_count - final_count} removed)")

    return analysis_df

def create_graph(df, column, title, color, label_format='${x:,.0f}'):
    """Create a distribution histogram for a given column"""
    data = df[column].dropna()

    # Calculate statistics
    mean_val = data.mean()
    median_val = data.median()

    # Create the histogram
    plt.figure(figsize=(6, 5))

    n, bins, patches = plt.hist(data, bins=20, alpha=0.7, color=color,
                               edgecolor='black', linewidth=0.5)

    # Add vertical lines for mean and median
    plt.axvline(mean_val, color='#E63946', linestyle='--', linewidth=2,
                label=f'Mean: {mean_val:,.0f}')
    plt.axvline(median_val, color='#457B9D', linestyle='--', linewidth=2,
                label=f'Median: {median_val:,.0f}')

    plt.xlabel(title, fontsize=10, fontweight='bold')
    plt.ylabel('Count', fontsize=10)
    plt.title(title, fontsize=12, fontweight='bold', pad=10)
    plt.legend(fontsize=9)

    # Format axis
    if '$' in label_format:
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    else:
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    plt.grid(True, alpha=0.2)
    plt.tight_layout()

    # Convert to base64
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
    img_buffer.seek(0)
    img_b64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    return img_b64, len(data), mean_val, median_val

def generate_report(csv_file, output_dir, date_str, stations, circles, api_key):
    """Generate a professional HTML report for a given CSV file"""
    print(f"  Generating report for {csv_file}")

    # Load data
    df = pd.read_csv(csv_file)

    # Detect columns
    price_col = 'price'
    sqft_col = 'squareFootage'
    zip_col = 'zipCode'

    # Clean data
    df_clean = clean_data(df, price_col, sqft_col, zip_col)

    # Calculate overall statistics
    total_listings = len(df_clean)
    avg_price = df_clean[price_col].mean()
    median_price = df_clean[price_col].median()
    avg_sqft = df_clean[sqft_col].mean()
    median_sqft = df_clean[sqft_col].median()
    avg_price_per_sqft = df_clean['price_per_sqft'].mean()
    median_price_per_sqft = df_clean['price_per_sqft'].median()

    # Generate graphs
    print("  Creating graphs...")
    price_img, price_count, _, _ = create_graph(df_clean, price_col, 'Price', '#6BAED6')
    sqft_img, sqft_count, _, _ = create_graph(df_clean, sqft_col, 'Square Footage', '#74C476', '{x:,.0f}')
    ppsf_img, ppsf_count, _, _ = create_graph(df_clean, 'price_per_sqft', 'Price per Sq Ft', '#FD8D3C')

    # Get top zip codes
    zip_counts = df_clean[zip_col].value_counts().head(5)

    # Format date for display
    try:
        display_date = datetime.strptime(date_str, '%Y%m%d').strftime('%B %d, %Y')
    except:
        display_date = date_str

    # Prepare property markers for map
    properties = []
    for _, row in df_clean.iterrows():
        lat = row.get('latitude')
        lng = row.get('longitude')
        if pd.notna(lat) and pd.notna(lng):
            properties.append({
                'lat': float(lat),
                'lng': float(lng),
                'price': int(row.get('price', 0)),
                'address': str(row.get('formattedAddress', '')),
                'beds': int(row.get('bedrooms', 0)) if pd.notna(row.get('bedrooms')) else 0,
                'baths': float(row.get('bathrooms', 0)) if pd.notna(row.get('bathrooms')) else 0,
                'sqft': int(row.get('squareFootage', 0)) if pd.notna(row.get('squareFootage')) else 0,
                'zillowUrl': str(row.get('zillowUrl', ''))
            })

    # Merge circles with station coordinates
    circles_with_coords = []
    for station in stations:
        station_name = station['name']
        if station_name in circles:
            circles_with_coords.append({
                'lat': station['lat'],
                'lng': station['lng'],
                'radius_m': circles[station_name]['radius_m']
            })

    # Convert to JSON for embedding in HTML
    properties_json = json.dumps(properties)
    stations_json = json.dumps(stations)
    circles_json = json.dumps(circles_with_coords)

    # Debug logging
    print(f"  Map data: {len(properties)} properties, {len(stations)} stations, {len(circles_with_coords)} circles")

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Report - {display_date}</title>
    <script src="https://maps.googleapis.com/maps/api/js?key={api_key}"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 25px 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 5px;
            letter-spacing: -0.5px;
        }}

        .header .date {{
            font-size: 1em;
            opacity: 0.9;
            font-weight: 300;
        }}

        .map-section {{
            padding: 20px 40px;
            background: white;
        }}

        .map-container {{
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            position: relative;
        }}

        #map {{
            width: 100%;
            height: 500px;
        }}

        .fullscreen-control {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            border: 2px solid #fff;
            border-radius: 3px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            cursor: pointer;
            padding: 8px 12px;
            font-size: 14px;
            font-weight: 500;
            color: #1a73e8;
            z-index: 1000;
        }}

        .fullscreen-control:hover {{
            background: #f8f9fa;
        }}

        .map-container.fullscreen {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
            border-radius: 0;
        }}

        .map-container.fullscreen #map {{
            height: 100vh;
        }}

        .stats-section {{
            padding: 20px 40px;
            background: #f8f9fa;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 15px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            transition: transform 0.2s, box-shadow 0.2s;
            border-top: 4px solid #667eea;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: 700;
            color: #1e3c72;
            margin-bottom: 8px;
        }}

        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }}

        .graphs-section {{
            padding: 20px 40px;
            background: white;
        }}

        .section-title {{
            font-size: 1.6em;
            color: #1e3c72;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 700;
        }}

        .graphs-container {{
            display: flex;
            gap: 15px;
            justify-content: space-between;
            flex-wrap: wrap;
        }}

        .graph-card {{
            flex: 1;
            min-width: 300px;
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            transition: transform 0.2s;
        }}

        .graph-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }}

        .graph-card img {{
            width: 100%;
            height: auto;
            border-radius: 6px;
        }}

        .zip-section {{
            padding: 20px 40px;
            background: #f8f9fa;
        }}

        .zip-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }}

        .zip-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .zip-code {{
            font-size: 1.5em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .zip-count {{
            color: #6c757d;
            font-size: 0.9em;
        }}

        .footer {{
            background: #1e3c72;
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .footer a {{
            color: #4ECDC4;
            text-decoration: none;
        }}

        @media (max-width: 768px) {{
            .graphs-container {{
                flex-direction: column;
            }}

            .graph-card {{
                min-width: 100%;
            }}

            .header h1 {{
                font-size: 1.8em;
            }}

            .stat-value {{
                font-size: 1.5em;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Long Island Real Estate Report</h1>
            <div class="date">{display_date}</div>
        </div>

        <div class="map-section">
            <div class="map-container" id="mapContainer">
                <div id="map"></div>
                <button class="fullscreen-control" onclick="toggleFullscreen()">⛶ Fullscreen</button>
            </div>
        </div>

        <div class="stats-section">
            <div class="section-title">Market Overview</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_listings:,}</div>
                    <div class="stat-label">Total Listings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${avg_price:,.0f}</div>
                    <div class="stat-label">Avg Price</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${median_price:,.0f}</div>
                    <div class="stat-label">Median Price</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_sqft:,.0f}</div>
                    <div class="stat-label">Avg Sq Ft</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{median_sqft:,.0f}</div>
                    <div class="stat-label">Median Sq Ft</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${avg_price_per_sqft:.0f}</div>
                    <div class="stat-label">Avg $/Sq Ft</div>
                </div>
            </div>
        </div>

        <div class="graphs-section">
            <div class="section-title">Market Analysis</div>
            <div class="graphs-container">
                <div class="graph-card">
                    <img src="data:image/png;base64,{price_img}" alt="Price Distribution">
                </div>
                <div class="graph-card">
                    <img src="data:image/png;base64,{sqft_img}" alt="Square Footage Distribution">
                </div>
                <div class="graph-card">
                    <img src="data:image/png;base64,{ppsf_img}" alt="Price per Sq Ft Distribution">
                </div>
            </div>
        </div>

        <div class="zip-section">
            <div class="section-title">Top Zip Codes by Inventory</div>
            <div class="zip-grid">
                {''.join([f'<div class="zip-card"><div class="zip-code">{zip_code}</div><div class="zip-count">{count} listings</div></div>' for zip_code, count in zip_counts.items()])}
            </div>
        </div>

        <div class="footer">
            <p><strong>Long Island Real Estate Analysis</strong></p>
            <p>Data from {total_listings:,} active listings • Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p><a href="../index.html">← Back to All Reports</a></p>
        </div>
    </div>

    <script>
        let map;
        let markers = [];

        // Data
        const properties = {properties_json};
        const stations = {stations_json};
        const circles = {circles_json};

        console.log('Map data loaded:', {{
            properties: properties.length,
            stations: stations.length,
            circles: circles.length
        }});
        console.log('Circles:', circles);
        console.log('Stations:', stations);

        function initMap() {{
            // Fixed map center for Long Island (consistent across all reports)
            const centerLat = 40.75;
            const centerLng = -73.4;

            // Initialize map with satellite view
            map = new google.maps.Map(document.getElementById('map'), {{
                center: {{ lat: centerLat, lng: centerLng }},
                zoom: 10,
                mapTypeId: 'satellite'
            }});

            // Layer 1: Add walking circles (lowest layer) - transparent gold/yellow (20% opacity)
            console.log('Adding', circles.length, 'walking circles');
            circles.forEach(circle => {{
                console.log('Adding circle:', circle);
                new google.maps.Circle({{
                    map: map,
                    center: {{ lat: circle.lat, lng: circle.lng }},
                    radius: circle.radius_m,
                    fillColor: '#FFD700',
                    fillOpacity: 0.2,
                    strokeColor: '#FFD700',
                    strokeOpacity: 0.6,
                    strokeWeight: 2,
                    zIndex: 1
                }});
            }});

            // Layer 2: Add station markers (middle layer) - gold/yellow train icons on pale yellow circles
            console.log('Adding', stations.length, 'station markers');

            const trainIcon = {{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="20" height="20">
                        <circle cx="512" cy="512" r="480" fill="#FFF4CC" stroke="#E6C200" stroke-width="16"/>
                        <g transform="translate(512, 512) scale(0.75) translate(-512, -512)">
                            <path fill="#FFD700" stroke="#B8860B" stroke-width="20" d="M512 85.333333C341.333333 85.333333 170.666667 106.666667 170.666667 256v405.333333c0 82.346667 66.986667 149.333333 149.333333 149.333334l-64 64v21.333333h95.146667l85.333333-85.333333H597.333333l85.333334 85.333333h85.333333v-21.333333l-64-64c82.346667 0 149.333333-66.986667 149.333333-149.333334V256c0-149.333333-152.746667-170.666667-341.333333-170.666667z m-192 640c-35.413333 0-64-28.586667-64-64s28.586667-64 64-64 64 28.586667 64 64-28.586667 64-64 64z m149.333333-298.666666H256v-170.666667h213.333333v170.666667z m85.333334 0v-170.666667h213.333333v170.666667H554.666667z m149.333333 298.666666c-35.413333 0-64-28.586667-64-64s28.586667-64 64-64 64 28.586667 64 64-28.586667 64-64 64z"/>
                        </g>
                    </svg>
                `),
                scaledSize: new google.maps.Size(20, 20),
                anchor: new google.maps.Point(10, 10)
            }};

            stations.forEach(station => {{
                console.log('Adding station:', station);
                const marker = new google.maps.Marker({{
                    position: {{ lat: station.lat, lng: station.lng }},
                    map: map,
                    title: station.name,
                    icon: trainIcon,
                    zIndex: 2
                }});

                const infoWindow = new google.maps.InfoWindow({{
                    content: `<div style="padding:8px;"><strong>${{station.name}}</strong><br>${{station.branch}} Line</div>`
                }});

                marker.addListener('click', () => {{
                    infoWindow.open(map, marker);
                }});
            }});

            // Layer 3: Add property markers (top layer) - medium blue house icons on pale blue circles
            const houseIcon = {{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="20" height="20">
                        <circle cx="256" cy="280" r="240" fill="#B3D9FF" stroke="#7AB8E8" stroke-width="8"/>
                        <g transform="translate(256, 280) scale(0.75) translate(-256, -280)">
                            <path fill="#4A90E2" stroke="#2E5A8A" stroke-width="12" d="M293,450v-114h-74v107l-3.06.53.56,6.48-117.02.02c-7.36-1.37-12.46-6.1-15-13l-.42-148.48,2.47-8.53,170.83-140.94,170.48,140.58.17,146.84c-.52,7.24-8.33,23.49-16.51,23.49h-118.5Z"/>
                            <path fill="#4A90E2" stroke="#2E5A8A" stroke-width="12" d="M350,128v-50.5c0-1.11,4.37-8.23,4.11-10.89l5.45-3.55c19.23,1.55,42.19-2.27,60.96-.08,3.09.36,5.24,1.44,6.73,4.27l.73,126.04,67.02,56.2c.79,1.2,1.66,2.83,1.79,4.25.12,1.2-3.22,12.29-3.91,13.64-1.45,2.83-13.5,16.68-16.37,19.63-3.91,4.03-6.39,7.26-12.8,5.78L255.35,120.16l-3.85,1.85L48.71,291.21c-3.92,2.41-8.45,2.8-12.23-.19-2.19-1.73-18.07-20.97-19.45-23.54-4.21-7.84.61-9.52,1.74-17.22,74.08-62.43,148.03-125.92,224.25-185.75,10.91-4.29,23.26-3.39,33.29,2.69l73.7,60.8Z"/>
                        </g>
                    </svg>
                `),
                scaledSize: new google.maps.Size(20, 20),
                anchor: new google.maps.Point(10, 20)
            }};

            properties.forEach(property => {{
                const marker = new google.maps.Marker({{
                    position: {{ lat: property.lat, lng: property.lng }},
                    map: map,
                    title: property.address,
                    icon: houseIcon,
                    zIndex: 3
                }});

                const infoContent = `
                    <div style="padding: 10px; max-width: 250px;">
                        <a href="${{property.zillowUrl}}" target="_blank" style="font-size: 14px; color: #1e3c72; text-decoration: underline; font-weight: 600; display: block; margin-bottom: 8px;">
                            ${{property.address}}
                        </a>
                        <div style="font-size: 16px; font-weight: bold; color: #4CAF50; margin-bottom: 5px;">
                            $${{property.price.toLocaleString()}}
                        </div>
                        <div style="font-size: 13px; color: #666;">
                            ${{property.beds}} beds • ${{property.baths}} baths • ${{property.sqft.toLocaleString()}} sqft
                        </div>
                    </div>
                `;

                const infoWindow = new google.maps.InfoWindow({{
                    content: infoContent
                }});

                marker.addListener('click', () => {{
                    infoWindow.open(map, marker);
                }});

                markers.push(marker);
            }});
        }}

        function toggleFullscreen() {{
            const container = document.getElementById('mapContainer');
            const button = document.querySelector('.fullscreen-control');

            if (container.classList.contains('fullscreen')) {{
                container.classList.remove('fullscreen');
                button.textContent = '⛶ Fullscreen';
            }} else {{
                container.classList.add('fullscreen');
                button.textContent = '⛶ Exit Fullscreen';
            }}

            // Trigger map resize
            google.maps.event.trigger(map, 'resize');
        }}

        // Initialize map when page loads
        window.addEventListener('load', initMap);
    </script>
</body>
</html>
"""

    # Save report (no timestamp since we only generate one per day)
    output_file = os.path.join(output_dir, f"real_estate_report_{date_str}.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✓ Report saved to: {output_file}")
    return output_file

def generate_index_html(base_tmp_dir, dated_dirs):
    """Generate an index.html with links to all reports"""
    print("\nGenerating index.html...")

    # Build list of reports (limit to 4 most recent)
    reports = []
    for date_str, dir_path in dated_dirs[:4]:
        # Find the most recent report in this directory
        html_files = sorted(glob.glob(os.path.join(dir_path, "real_estate_report_*.html")), reverse=True)
        if html_files:
            # Get relative path
            rel_path = os.path.relpath(html_files[0], base_tmp_dir)
            try:
                display_date = datetime.strptime(date_str, '%Y%m%d').strftime('%B %d, %Y')
            except:
                display_date = date_str

            reports.append({
                'date_str': date_str,
                'display_date': display_date,
                'path': rel_path.replace('\\', '/')
            })

    # Generate HTML
    report_cards = '\n'.join([
        f"""
        <div class="report-card">
            <div class="report-date">{r['display_date']}</div>
            <div class="report-id">Report ID: {r['date_str']}</div>
            <a href="{r['path']}" class="view-button">View Report →</a>
        </div>
        """ for r in reports
    ])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Long Island Real Estate Reports</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }}

        .header h1 {{
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .reports-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 25px;
            margin-bottom: 40px;
        }}

        .report-card {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .report-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }}

        .report-date {{
            font-size: 1.5em;
            font-weight: 700;
            color: #1e3c72;
            white-space: nowrap;
        }}

        .report-id {{
            color: #6c757d;
            font-size: 0.9em;
        }}

        .view-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            text-align: center;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .view-button:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}

        .footer {{
            text-align: center;
            color: white;
            margin-top: 50px;
            opacity: 0.8;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2em;
            }}

            .reports-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Long Island Real Estate Reports</h1>
            <p>Daily market analysis and property insights</p>
        </div>

        <div class="reports-grid">
            {report_cards}
        </div>

        <div class="footer">
            <p>Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>Total reports: {len(reports)}</p>
        </div>
    </div>
</body>
</html>
"""

    index_path = os.path.join(base_tmp_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Index saved to: {index_path}")
    return index_path

def main():
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_tmp_dir = os.path.join(script_dir, '..', '..', '.tmp')
    base_tmp_dir = os.path.abspath(base_tmp_dir)
    data_dir = os.path.join(script_dir, '..', '..', 'data')
    data_dir = os.path.abspath(data_dir)

    # Check for Google Maps API key
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set!")
        print("Please set it with: export GOOGLE_MAPS_API_KEY='your-api-key'")
        sys.exit(1)

    print(f"Scanning for dated directories in: {base_tmp_dir}\n")

    # Load station data and walking circles (once for all reports)
    print("Loading station data and walking circles...")
    stations_csv = os.path.join(data_dir, 'MTA_Rail_Stations_with_zip.csv')
    kml_file = os.path.join(data_dir, 'lirr_15min_walk_circles.kml')
    zipcodes_file = os.path.join(data_dir, 'zipcodes.txt')

    # Load allowed zip codes
    allowed_zips = None
    if os.path.exists(zipcodes_file):
        with open(zipcodes_file, 'r') as f:
            allowed_zips = set(line.strip() for line in f if line.strip())
        print(f"  Loaded {len(allowed_zips)} allowed zip codes")

    # Load stations (don't filter by zip - show all LIRR stations)
    stations = load_station_data(stations_csv, allowed_zips=None)
    print(f"  Loaded {len(stations)} stations")

    # Load walking circles
    circles = parse_kml_circles(kml_file)
    print(f"  Loaded {len(circles)} walking circles\n")

    # Find all dated directories
    dated_dirs = get_dated_directories(base_tmp_dir)

    if not dated_dirs:
        print("No dated directories found!")
        sys.exit(1)

    print(f"Found {len(dated_dirs)} dated directories\n")

    # Process each directory
    for date_str, dir_path in dated_dirs:
        print(f"Processing {date_str}...")

        # Check if report already exists
        if report_exists(dir_path):
            print(f"  ✓ Report already exists, skipping")
            continue

        # Find homes CSV
        csv_file = find_homes_csv(dir_path)
        if not csv_file:
            print(f"  ✗ No homes CSV found, skipping")
            continue

        # Generate report
        try:
            generate_report(csv_file, dir_path, date_str, stations, circles, api_key)
        except Exception as e:
            print(f"  ✗ Error generating report: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Generate index
    generate_index_html(base_tmp_dir, dated_dirs)

    print("\n✅ All reports generated successfully!")

if __name__ == "__main__":
    main()
