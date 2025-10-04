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

def generate_report(csv_file, output_dir, date_str):
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

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Report - {display_date}</title>
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
        }}

        .map-container iframe {{
            width: 100%;
            height: 500px;
            border: none;
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
            <div class="map-container">
                <iframe src="https://www.google.com/maps/d/embed?mid=1Rt2pjUqZVFtj6RIsmJacyrPwHY0gULg&ehbc=2E312F"></iframe>
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
</body>
</html>
"""

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"real_estate_report_{timestamp}.html")
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

    print(f"Scanning for dated directories in: {base_tmp_dir}\n")

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
            generate_report(csv_file, dir_path, date_str)
        except Exception as e:
            print(f"  ✗ Error generating report: {e}")
            continue

    # Generate index
    generate_index_html(base_tmp_dir, dated_dirs)

    print("\n✅ All reports generated successfully!")

if __name__ == "__main__":
    main()
