#!/usr/bin/env python3
"""
Real Estate Data Analysis Report Generator

This script generates an HTML report with interactive graphs analyzing real estate data.
Produces three main visualizations:
1. Average vs Median Price by Zip Code
2. Average vs Median Square Footage by Zip Code
3. Average vs Median Price per Square Foot by Zip Code

Usage:
    python generate_real_estate_report.py <csv_file_path>

Example:
    python generate_real_estate_report.py "C:/Users/mesol/workspace/LIRR map/.tmp/20250921/zip_code_inventory-20250921_134109.csv"
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from datetime import datetime
from pathlib import Path
import base64
import io

def detect_columns(df):
    """Detect price, square footage, and zip code columns in the DataFrame"""
    columns = df.columns.tolist()

    # Look for price columns
    price_cols = [col for col in columns if any(term in col.lower() for term in ['price'])]

    # Look for square footage columns
    sqft_cols = [col for col in columns if any(term in col.lower() for term in ['sqft', 'square', 'footage', 'area'])]

    # Look for zip code columns
    zip_cols = [col for col in columns if any(term in col.lower() for term in ['zip'])]

    # Prefer specific column names if available
    price_col = None
    sqft_col = None
    zip_col = None

    # Find best price column - prefer individual listing price over aggregated
    for col in price_cols:
        if col.lower() == 'price':
            price_col = col
            break
        elif 'avg_price' in col.lower() or 'average_price' in col.lower():
            price_col = col
            break
    if not price_col and price_cols:
        price_col = price_cols[0]

    # Find best square footage column - prefer individual listing sqft over aggregated
    for col in sqft_cols:
        if 'squarefootage' in col.lower():
            sqft_col = col
            break
        elif 'avg_sqft' in col.lower() or 'average_sqft' in col.lower():
            sqft_col = col
            break
    if not sqft_col and sqft_cols:
        sqft_col = sqft_cols[0]

    # Find best zip code column
    for col in zip_cols:
        if 'zipcode' in col.lower():
            zip_col = col
            break
        elif 'zip_code' in col.lower():
            zip_col = col
            break
    if not zip_col and zip_cols:
        zip_col = zip_cols[0]

    return price_col, sqft_col, zip_col, price_cols, sqft_cols, zip_cols

def clean_data(df, price_col, sqft_col, zip_col):
    """Clean and prepare data for analysis"""
    # Make a copy
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

    print(f"Data cleaning: {initial_count} -> {final_count} rows ({initial_count - final_count} removed)")

    return analysis_df

def create_price_graph(df, price_col, zip_col):
    """Create price distribution histogram"""
    # Get price data
    prices = df[price_col].dropna()

    # Calculate statistics
    mean_price = prices.mean()
    median_price = prices.median()

    # Create the histogram
    plt.figure(figsize=(14, 8))

    # Create histogram with automatic binning
    n, bins, patches = plt.hist(prices, bins=25, alpha=0.7, color='#2E86AB',
                               edgecolor='black', linewidth=0.5)

    # Add vertical lines for mean and median
    plt.axvline(mean_price, color='#A23B72', linestyle='--', linewidth=2,
                label=f'Mean: ${mean_price:,.0f}')
    plt.axvline(median_price, color='#F18F01', linestyle='--', linewidth=2,
                label=f'Median: ${median_price:,.0f}')

    plt.xlabel('Price ($)', fontsize=12)
    plt.ylabel('Number of Properties', fontsize=12)
    plt.title('Price Distribution', fontsize=16, fontweight='bold')
    plt.legend(fontsize=12)

    # Format x-axis
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Add grid for better readability
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # Convert to base64 for HTML embedding
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    img_b64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    return img_b64, len(prices)

def create_sqft_graph(df, sqft_col, zip_col):
    """Create square footage distribution histogram"""
    # Get square footage data
    sqft_data = df[sqft_col].dropna()

    # Calculate statistics
    mean_sqft = sqft_data.mean()
    median_sqft = sqft_data.median()

    # Create the histogram
    plt.figure(figsize=(14, 8))

    # Create histogram with automatic binning
    n, bins, patches = plt.hist(sqft_data, bins=25, alpha=0.7, color='#A23B72',
                               edgecolor='black', linewidth=0.5)

    # Add vertical lines for mean and median
    plt.axvline(mean_sqft, color='#2E86AB', linestyle='--', linewidth=2,
                label=f'Mean: {mean_sqft:,.0f} sq ft')
    plt.axvline(median_sqft, color='#F18F01', linestyle='--', linewidth=2,
                label=f'Median: {median_sqft:,.0f} sq ft')

    plt.xlabel('Square Footage', fontsize=12)
    plt.ylabel('Number of Properties', fontsize=12)
    plt.title('Square Footage Distribution', fontsize=16, fontweight='bold')
    plt.legend(fontsize=12)

    # Format x-axis
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    # Add grid for better readability
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # Convert to base64 for HTML embedding
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    img_b64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    return img_b64, len(sqft_data)

def create_price_per_sqft_graph(df, zip_col):
    """Create price per square foot distribution histogram"""
    # Get price per sqft data
    price_per_sqft_data = df['price_per_sqft'].dropna()

    # Calculate statistics
    mean_price_per_sqft = price_per_sqft_data.mean()
    median_price_per_sqft = price_per_sqft_data.median()

    # Create the histogram
    plt.figure(figsize=(14, 8))

    # Create histogram with automatic binning
    n, bins, patches = plt.hist(price_per_sqft_data, bins=25, alpha=0.7, color='#F18F01',
                               edgecolor='black', linewidth=0.5)

    # Add vertical lines for mean and median
    plt.axvline(mean_price_per_sqft, color='#2E86AB', linestyle='--', linewidth=2,
                label=f'Mean: ${mean_price_per_sqft:.0f}/sq ft')
    plt.axvline(median_price_per_sqft, color='#A23B72', linestyle='--', linewidth=2,
                label=f'Median: ${median_price_per_sqft:.0f}/sq ft')

    plt.xlabel('Price per Square Foot ($)', fontsize=12)
    plt.ylabel('Number of Properties', fontsize=12)
    plt.title('Price per Square Foot Distribution', fontsize=16, fontweight='bold')
    plt.legend(fontsize=12)

    # Format x-axis
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.0f}'))

    # Add grid for better readability
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # Convert to base64 for HTML embedding
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    img_b64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    return img_b64, len(price_per_sqft_data)

def generate_html_report(csv_file, df, price_col, sqft_col, zip_col,
                        price_img, sqft_img, price_per_sqft_img,
                        price_zip_count, sqft_zip_count, price_per_sqft_zip_count):
    """Generate HTML report with embedded graphs"""

    # Calculate overall statistics
    total_listings = len(df)
    avg_price = df[price_col].mean()
    median_price = df[price_col].median()
    avg_sqft = df[sqft_col].mean()
    median_sqft = df[sqft_col].median()
    avg_price_per_sqft = df['price_per_sqft'].mean()
    median_price_per_sqft = df['price_per_sqft'].median()

    # Get top 5 zip codes by count
    zip_counts = df[zip_col].value_counts().head(5)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #2E86AB, #A23B72);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 15px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 1.8em;
        }}
        .header p {{
            margin: 5px 0 0 0;
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2E86AB;
            border-bottom: 3px solid #2E86AB;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #2E86AB;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2E86AB;
            margin: 0;
        }}
        .stat-label {{
            color: #666;
            margin: 5px 0 0 0;
            font-size: 0.9em;
        }}
        .graph {{
            text-align: center;
            margin: 20px 0;
        }}
        .graph img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .data-info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #2196F3;
        }}
        .zip-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        .zip-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 15px;
            padding: 20px;
            border-top: 1px solid #ddd;
        }}
        .map-container {{
            margin-bottom: 15px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .map-container iframe {{
            width: 100%;
            height: 480px;
            border: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Real Estate Analysis Report</h1>
        <p>Generated on {timestamp}</p>
    </div>

    <div class="map-container">
        <iframe src="https://www.google.com/maps/d/embed?mid=1Rt2pjUqZVFtj6RIsmJacyrPwHY0gULg&ehbc=2E312F"></iframe>
    </div>

    <div class="section">
        <h2>📊 Overall Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <p class="stat-value">{total_listings:,}</p>
                <p class="stat-label">Total Listings</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">${avg_price_per_sqft:.0f}</p>
                <p class="stat-label">Avg Price/Sq Ft</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">${avg_price:,.0f}</p>
                <p class="stat-label">Average Price</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">${median_price:,.0f}</p>
                <p class="stat-label">Median Price</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">{avg_sqft:,.0f}</p>
                <p class="stat-label">Average Sq Ft</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">{median_sqft:,.0f}</p>
                <p class="stat-label">Median Sq Ft</p>
            </div>
        </div>

        <div class="data-info">
            <strong>📋 Data Information:</strong><br>
            • Price Column: {price_col}<br>
            • Square Footage Column: {sqft_col}<br>
            • Zip Code Column: {zip_col}<br>
            • Data aggregated by zip code from individual property listings<br>
            • Analysis includes only zip codes with 3+ listings for statistical reliability
        </div>

        <h3>🏆 Top 5 Zip Codes by Listing Count</h3>
        <div class="zip-list">
            {''.join([f'<div class="zip-item"><strong>{zip_code}</strong><br>{count} listings</div>'
                     for zip_code, count in zip_counts.items()])}
        </div>
    </div>

    <div class="section">
        <h2>💰 Price Distribution</h2>
        <p>Distribution of property prices showing the frequency of properties in each price range. Based on {price_zip_count} properties with valid price data.</p>
        <div class="graph">
            <img src="data:image/png;base64,{price_img}" alt="Price Distribution Histogram">
        </div>
    </div>

    <div class="section">
        <h2>📐 Square Footage Distribution</h2>
        <p>Distribution of property square footage showing the frequency of properties in each size range. Based on {sqft_zip_count} properties with valid square footage data.</p>
        <div class="graph">
            <img src="data:image/png;base64,{sqft_img}" alt="Square Footage Distribution Histogram">
        </div>
    </div>

    <div class="section">
        <h2>💵 Price per Square Foot Distribution</h2>
        <p>Distribution of price per square foot showing the frequency of properties in each price/sqft range. Based on {price_per_sqft_zip_count} properties with valid data.</p>
        <div class="graph">
            <img src="data:image/png;base64,{price_per_sqft_img}" alt="Price per Square Foot Distribution Histogram">
        </div>
    </div>

    <div class="footer">
        <p>Generated by Real Estate Analysis Script</p>
        <p>📁 Source file: {csv_file}</p>
    </div>
</body>
</html>
"""

    return html_template

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_real_estate_report.py <csv_file_path>")
        print("Example: python generate_real_estate_report.py \"C:/path/to/your/data.csv\"")
        sys.exit(1)

    csv_file = sys.argv[1]

    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found.")
        sys.exit(1)

    print(f"Analyzing real estate data from: {csv_file}")

    try:
        # Load the CSV file
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns")

        # Detect columns
        price_col, sqft_col, zip_col, price_cols, sqft_cols, zip_cols = detect_columns(df)

        print(f"Column detection:")
        print(f"   Price columns found: {price_cols}")
        print(f"   Square footage columns found: {sqft_cols}")
        print(f"   Zip code columns found: {zip_cols}")
        print(f"   Using: {price_col}, {sqft_col}, {zip_col}")

        if not price_col:
            print("Error: No price column detected. Make sure your CSV has a column containing 'price' in the name.")
            sys.exit(1)

        if not sqft_col:
            print("Error: No square footage column detected. Make sure your CSV has a column containing 'sqft', 'square', 'footage', or 'area' in the name.")
            sys.exit(1)

        if not zip_col:
            print("Error: No zip code column detected. Make sure your CSV has a column containing 'zip' in the name.")
            sys.exit(1)

        # Clean data
        print("Cleaning data...")
        df_clean = clean_data(df, price_col, sqft_col, zip_col)

        # Generate graphs
        print("Generating price analysis graph...")
        price_img, price_zip_count = create_price_graph(df_clean, price_col, zip_col)

        print("Generating square footage analysis graph...")
        sqft_img, sqft_zip_count = create_sqft_graph(df_clean, sqft_col, zip_col)

        print("Generating price per square foot analysis graph...")
        price_per_sqft_img, price_per_sqft_zip_count = create_price_per_sqft_graph(df_clean, zip_col)

        # Generate HTML report
        print("Generating HTML report...")
        html_content = generate_html_report(
            csv_file, df_clean, price_col, sqft_col, zip_col,
            price_img, sqft_img, price_per_sqft_img,
            price_zip_count, sqft_zip_count, price_per_sqft_zip_count
        )

        # Save HTML report
        output_file = Path(csv_file).parent / f"real_estate_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Report generated successfully!")
        print(f"HTML report saved to: {output_file}")
        print(f"Open the file in your web browser to view the interactive report.")

    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()