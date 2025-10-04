import os, requests, json, csv, sys
from datetime import datetime
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

def load_allowed_zip_codes(zip_file):
    """Load allowed Long Island zip codes from file"""
    allowed_zips = set()

    if not os.path.exists(zip_file):
        print(f"Warning: {zip_file} not found, will process all zip codes")
        return None

    with open(zip_file, 'r', encoding='utf-8') as f:
        for line in f:
            zip_code = line.strip()
            if zip_code:
                allowed_zips.add(zip_code)

    return allowed_zips

def get_unique_zip_codes(csv_file, allowed_zips=None):
    """Extract unique zip codes from the MTA stations CSV, filtered by allowed zips"""
    zip_codes = set()

    with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            zip_code = row.get('Zip Code', '').strip()
            if zip_code and zip_code not in ['N/A', 'ERROR']:
                # Only include if in allowed list (if provided)
                if allowed_zips is None or zip_code in allowed_zips:
                    zip_codes.add(zip_code)

    return sorted(list(zip_codes))

def get_zip_code_coordinates(csv_file, allowed_zips=None):
    """Extract zip code coordinates from MTA stations CSV, returning all stations per zip"""
    zip_coords = {}

    with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            zip_code = row.get('Zip Code', '').strip()
            station_name = row.get('Station Name', '').strip()
            latitude = row.get('Latitude', '').strip()
            longitude = row.get('Longitude', '').strip()

            # Check if we have valid data
            if (zip_code and zip_code not in ['N/A', 'ERROR'] and
                station_name and latitude and longitude):

                # Only include if in allowed list (if provided)
                if allowed_zips is None or zip_code in allowed_zips:
                    try:
                        # Collect all stations for each zip code
                        if zip_code not in zip_coords:
                            zip_coords[zip_code] = []

                        zip_coords[zip_code].append({
                            'latitude': float(latitude),
                            'longitude': float(longitude),
                            'station_name': station_name
                        })
                    except ValueError:
                        print(f"Warning: Invalid coordinates for {station_name}, skipping")

    return zip_coords

def get_zip_code_to_station_mapping(csv_file, allowed_zips=None):
    """Create a mapping from zip codes to station names from MTA stations CSV"""
    zip_to_stations = {}

    with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            zip_code = row.get('Zip Code', '').strip()
            station_name = row.get('Station Name', '').strip()

            # Check if we have valid data
            if (zip_code and zip_code not in ['N/A', 'ERROR'] and station_name):
                # Only include if in allowed list (if provided)
                if allowed_zips is None or zip_code in allowed_zips:
                    # Collect all stations for each zip code
                    if zip_code not in zip_to_stations:
                        zip_to_stations[zip_code] = []
                    if station_name not in zip_to_stations[zip_code]:
                        zip_to_stations[zip_code].append(station_name)

    # Convert lists to comma-delimited strings
    zip_to_station = {}
    for zip_code, stations in zip_to_stations.items():
        zip_to_station[zip_code] = ', '.join(sorted(stations))

    return zip_to_station

def fetch_rentcast_data(zip_code, latitude, longitude, station_name, api_key, max_price=600000, radius=1.5):
    """Fetch homes for sale data from RentCast API for a zip code using station coordinates with radius"""
    url = "https://api.rentcast.io/v1/listings/sale"

    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "status": "Active",
        "maxPrice": max_price,
        "limit": 500  # Get all available listings
    }

    try:
        print(f"Fetching data for zip {zip_code} using {station_name} coordinates (lat: {latitude}, lng: {longitude}, radius: {radius} miles)...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        print(f"Found {len(data)} listings within {radius} miles of {station_name} for zip {zip_code}")
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for zip code {zip_code}: {e}")
        return []

def save_json_data(data, zip_code, output_dir):
    """Save the JSON data to a file"""
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"{zip_code}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} listings to {filename}")

def fetch_and_combine_data_for_zip(zip_code, stations, api_key, max_price=600000, radius=1.5):
    """Fetch data from all stations in a zip code and combine results"""
    all_data = []
    seen_ids = set()

    # Process stations sequentially within this zip code
    # (since each thread handles a unique zip code, we don't need concurrency here)
    for station in stations:
        station_name = station['station_name']
        latitude = station['latitude']
        longitude = station['longitude']

        try:
            data = fetch_rentcast_data(zip_code, latitude, longitude, station_name, api_key, max_price, radius)
            print(f"  {station_name}: {len(data)} listings")

            # Add unique listings only (deduplicate by ID)
            for listing in data:
                listing_id = listing.get('id')
                if listing_id and listing_id not in seen_ids:
                    seen_ids.add(listing_id)
                    all_data.append(listing)
                elif not listing_id:
                    # If no ID, use address + price as fallback identifier
                    address = listing.get('formattedAddress', '')
                    price = listing.get('price', 0)
                    fallback_id = f"{address}|{price}"
                    if fallback_id not in seen_ids:
                        seen_ids.add(fallback_id)
                        all_data.append(listing)

        except Exception as e:
            print(f"  Error fetching data for {station_name}: {e}")

    print(f"Combined data for zip {zip_code}: {len(all_data)} unique listings from {len(stations)} stations")
    return all_data

def load_all_json_data(json_dir, allowed_zips=None):
    """Load all JSON files from the directory and combine them, filtered by allowed zip codes"""
    all_homes = []

    if not os.path.exists(json_dir):
        print(f"Directory {json_dir} does not exist")
        return all_homes

    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            # Extract zip code from filename
            zip_code = filename.replace('.json', '')

            # Skip if not in allowed list
            if allowed_zips is not None and zip_code not in allowed_zips:
                print(f"Skipping {filename} - not in approved Long Island zip codes")
                continue

            filepath = os.path.join(json_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_homes.extend(data)
                    else:
                        print(f"Warning: {filename} does not contain a list")
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return all_homes

def deduplicate_homes(homes):
    """Remove duplicate homes based on unique identifiers"""
    seen_homes = set()
    unique_homes = []

    for home in homes:
        # Create a unique identifier for each home
        # Use ID if available, otherwise fall back to address + price combination
        home_id = home.get('id')
        if home_id:
            identifier = str(home_id)
        else:
            # Fallback: use formatted address + price as identifier
            address = home.get('formattedAddress', '')
            price = home.get('price', 0)
            identifier = f"{address}|{price}"

        if identifier not in seen_homes:
            seen_homes.add(identifier)
            unique_homes.append(home)

    duplicate_count = len(homes) - len(unique_homes)
    if duplicate_count > 0:
        print(f"Removed {duplicate_count} duplicate listings")

    return unique_homes

def filter_homes_by_criteria(homes, max_price=600000, min_bathrooms=1.5, min_bedrooms=3):
    """Filter homes by price, bathrooms, bedrooms, and property type"""
    filtered = []

    for home in homes:
        # Filter by price
        price = home.get('price', 0)
        if price > max_price:
            continue

        # Filter by property type - exclude empty lots
        property_type = home.get('propertyType', '').lower()
        if property_type == 'land':
            continue

        # Filter by bathrooms - must have 1.5+ if not null
        bathrooms = home.get('bathrooms')
        if bathrooms is not None and bathrooms < min_bathrooms:
            continue

        # Filter by bedrooms - must have 3+ (hard requirement, exclude nulls)
        bedrooms = home.get('bedrooms')
        if bedrooms is None or bedrooms < min_bedrooms:
            continue

        filtered.append(home)

    return filtered

def generate_zillow_url(address_line1, city, state, zip_code):
    """Generate a Zillow URL from address components"""
    if not address_line1 or not city or not state or not zip_code:
        return ""

    # Create the address slug: "24-Kennedy-Rd-Port-Jefferson-Station-NY-11776"
    # Replace spaces with dashes and URL encode special characters
    address_parts = []

    # Process address line (e.g., "24 Kennedy Road" -> "24-Kennedy-Rd")
    if address_line1:
        # Replace common street suffixes with abbreviations
        address_clean = address_line1.replace(" Road", " Rd").replace(" Street", " St").replace(" Avenue", " Ave").replace(" Drive", " Dr").replace(" Lane", " Ln").replace(" Court", " Ct").replace(" Place", " Pl").replace(" Boulevard", " Blvd")
        address_parts.append(address_clean.replace(" ", "-"))

    # Process city (e.g., "Port Jefferson Station" -> "Port-Jefferson-Station")
    if city:
        address_parts.append(city.replace(" ", "-"))

    # Add state and zip code
    if state:
        address_parts.append(state)
    if zip_code:
        address_parts.append(str(zip_code))

    # Join all parts with dashes
    address_slug = "-".join(address_parts)

    # URL encode the slug to handle any special characters
    encoded_slug = quote(address_slug, safe="-")

    return f"https://www.zillow.com/homes/for_sale/{encoded_slug}_rb/"

def convert_to_csv(homes, output_file):
    """Convert the homes data to CSV format for mapping"""
    if not homes:
        print("No homes data to convert")
        return

    # Define the CSV columns we want for mapping
    fieldnames = [
        'zillowUrl', 'id', 'formattedAddress', 'addressLine1', 'city', 'state', 'zipCode',
        'latitude', 'longitude', 'propertyType', 'bedrooms', 'bathrooms',
        'squareFootage', 'lotSize', 'yearBuilt', 'price', 'status',
        'listingType', 'listedDate', 'daysOnMarket', 'mlsNumber',
        'listingAgent_name', 'listingAgent_phone', 'county'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for home in homes:
            # Flatten the nested data for CSV
            row = {
                'id': home.get('id', ''),
                'formattedAddress': home.get('formattedAddress', ''),
                'addressLine1': home.get('addressLine1', ''),
                'city': home.get('city', ''),
                'state': home.get('state', ''),
                'zipCode': home.get('zipCode', ''),
                'latitude': home.get('latitude', ''),
                'longitude': home.get('longitude', ''),
                'propertyType': home.get('propertyType', ''),
                'bedrooms': home.get('bedrooms', ''),
                'bathrooms': home.get('bathrooms', ''),
                'squareFootage': home.get('squareFootage', ''),
                'lotSize': home.get('lotSize', ''),
                'yearBuilt': home.get('yearBuilt', ''),
                'price': home.get('price', ''),
                'status': home.get('status', ''),
                'listingType': home.get('listingType', ''),
                'listedDate': home.get('listedDate', ''),
                'daysOnMarket': home.get('daysOnMarket', ''),
                'mlsNumber': home.get('mlsNumber', ''),
                'county': home.get('county', '')
            }

            # Extract agent info if available
            listing_agent = home.get('listingAgent', {})
            if listing_agent:
                row['listingAgent_name'] = listing_agent.get('name', '')
                row['listingAgent_phone'] = listing_agent.get('phone', '')

            # Generate Zillow URL
            row['zillowUrl'] = generate_zillow_url(
                home.get('addressLine1', ''),
                home.get('city', ''),
                home.get('state', ''),
                home.get('zipCode', '')
            )

            writer.writerow(row)

    print(f"Saved {len(homes)} homes to {output_file}")

def generate_report(homes, max_price=600000):
    """Generate a summary report of the findings"""
    if not homes:
        print("No homes data for report")
        return

    # Group by zip code
    zip_stats = {}
    for home in homes:
        zip_code = home.get('zipCode', 'Unknown')
        price = home.get('price', 0)

        if zip_code not in zip_stats:
            zip_stats[zip_code] = {
                'count': 0,
                'total_value': 0,
                'min_price': float('inf'),
                'max_price': 0,
                'under_budget': 0
            }

        zip_stats[zip_code]['count'] += 1
        zip_stats[zip_code]['total_value'] += price
        zip_stats[zip_code]['min_price'] = min(zip_stats[zip_code]['min_price'], price)
        zip_stats[zip_code]['max_price'] = max(zip_stats[zip_code]['max_price'], price)

        if price <= max_price:
            zip_stats[zip_code]['under_budget'] += 1

    print(f"\n=== HOMES FOR SALE REPORT ===")
    print(f"Total homes found: {len(homes)}")
    print(f"Budget limit: ${max_price:,}")
    print(f"Criteria: 3+ bedrooms, 1.5+ bathrooms, no land/empty lots")
    print(f"Homes meeting criteria: {len(homes)}")

    print(f"\n=== BY ZIP CODE ===")
    for zip_code in sorted(zip_stats.keys()):
        stats = zip_stats[zip_code]
        avg_price = stats['total_value'] / stats['count'] if stats['count'] > 0 else 0

        print(f"\nZip {zip_code}:")
        print(f"  Total listings: {stats['count']}")
        print(f"  Under budget: {stats['under_budget']}")
        print(f"  Price range: ${stats['min_price']:,} - ${stats['max_price']:,}")
        print(f"  Average price: ${avg_price:,.0f}")

        if stats['under_budget'] == 0:
            print(f"  WARNING: No homes under ${max_price:,} in this zip code!")

def generate_zip_code_inventory_report(filtered_homes, output_dir, zip_to_station=None):
    """Generate a CSV report showing inventory counts by zip code from filtered homes"""
    zip_data = {}

    # Collect data by zip code
    for home in filtered_homes:
        zip_code = home.get('zipCode', 'Unknown')
        price = home.get('price', 0)
        square_footage = home.get('squareFootage', 0)

        if zip_code not in zip_data:
            zip_data[zip_code] = {
                'count': 0,
                'prices': [],
                'square_footages': []
            }

        zip_data[zip_code]['count'] += 1

        # Only include valid prices and square footages for statistics
        if price and price > 0:
            zip_data[zip_code]['prices'].append(price)
        if square_footage and square_footage > 0:
            zip_data[zip_code]['square_footages'].append(square_footage)

    # Create CSV report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"zip_code_inventory-{timestamp}.csv")

    with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['zip_code', 'station_name', 'total_listings', 'avg_price', 'median_price', 'avg_sqft', 'median_sqft']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Sort by count (descending) then by zip code
        sorted_zips = sorted(zip_data.items(), key=lambda x: (-x[1]['count'], x[0]))

        for zip_code, data in sorted_zips:
            # Get station name if mapping is provided
            station_name = ''
            if zip_to_station and zip_code in zip_to_station:
                station_name = zip_to_station[zip_code]

            # Calculate statistics
            avg_price = statistics.mean(data['prices']) if data['prices'] else 0
            median_price = statistics.median(data['prices']) if data['prices'] else 0
            avg_sqft = statistics.mean(data['square_footages']) if data['square_footages'] else 0
            median_sqft = statistics.median(data['square_footages']) if data['square_footages'] else 0

            writer.writerow({
                'zip_code': zip_code,
                'station_name': station_name,
                'total_listings': data['count'],
                'avg_price': round(avg_price, 0) if avg_price else '',
                'median_price': round(median_price, 0) if median_price else '',
                'avg_sqft': round(avg_sqft, 0) if avg_sqft else '',
                'median_sqft': round(median_sqft, 0) if median_sqft else ''
            })

    print(f"Zip code inventory report saved to: {report_file}")
    print(f"Total zip codes with listings: {len([d for d in zip_data.values() if d['count'] > 0])}")
    print(f"Top 5 zip codes by inventory:")
    for zip_code, data in sorted_zips[:5]:
        station_name = zip_to_station.get(zip_code, '') if zip_to_station else ''
        station_info = f" ({station_name})" if station_name else ""
        avg_price = statistics.mean(data['prices']) if data['prices'] else 0
        print(f"  {zip_code}{station_info}: {data['count']} listings, avg price: ${avg_price:,.0f}" if avg_price else f"  {zip_code}{station_info}: {data['count']} listings")

    return report_file

def main():
    # Configuration
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    stations_csv = f"{data_dir}/MTA_Rail_Stations_with_zip.csv"
    zip_codes_file = f"{data_dir}/zipcodes.txt"
    base_tmp_dir = os.path.join(os.path.dirname(__file__), '..', '..', '.tmp')
    max_price = 600000  # $600k budget

    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create dated directory path (YYYYMMDD format)
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(base_tmp_dir, date_str)

    # Check if dated directory already exists - exit early if work is done for today
    if os.path.exists(output_dir):
        print(f"Work already completed for today - {date_str} directory exists at {output_dir}")
        print("Exiting early.")
        sys.exit(0)

    # Create the dated directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory for today: {output_dir}")

    csv_output_file = f"{output_dir}/homes-{timestamp}.csv"

    # Check for required files
    if not os.path.exists(stations_csv):
        print(f"Error: {stations_csv} not found. Run zipenrich.py first.")
        sys.exit(1)

    # Load allowed Long Island zip codes
    print("Loading Long Island zip codes...")
    allowed_zips = load_allowed_zip_codes(zip_codes_file)
    if allowed_zips:
        print(f"Loaded {len(allowed_zips)} Long Island zip codes")
    else:
        print("No zip code filter applied - processing all zip codes")

    # Create zip code to station mapping
    print("Creating zip code to station mapping...")
    zip_to_station = get_zip_code_to_station_mapping(stations_csv, allowed_zips)
    print(f"Found {len(zip_to_station)} zip codes with associated stations")

    # Check if API key is available for fetching new data
    if "RENTCAST_API_KEY" not in os.environ:
        print("Warning: RENTCAST_API_KEY environment variable not set")
        print("Skipping API calls and using existing JSON files only...")
        print("Get your API key from https://www.rentcast.io/ to fetch new data")
        api_key = None
    else:
        api_key = os.environ["RENTCAST_API_KEY"]

        # Get zip code coordinates (filtered by Long Island zip codes)
        print("Extracting zip code coordinates from MTA stations CSV...")
        zip_coords = get_zip_code_coordinates(stations_csv, allowed_zips)
        print(f"Found {len(zip_coords)} Long Island zip codes with coordinates")

        # Filter out zip codes that already have data
        zip_codes_to_fetch = {}
        for zip_code, stations in zip_coords.items():
            json_file = os.path.join(output_dir, f"{zip_code}.json")
            if os.path.exists(json_file):
                print(f"Data for {zip_code} already exists, skipping...")
            else:
                zip_codes_to_fetch[zip_code] = stations

        if zip_codes_to_fetch:
            print(f"Fetching data for {len(zip_codes_to_fetch)} zip codes...")

            # Sort zip codes by station count (descending) for better load balancing
            # This ensures zip codes with more stations are processed first
            sorted_zip_codes = sorted(
                zip_codes_to_fetch.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )

            # Show distribution for debugging
            station_counts = [len(stations) for _, stations in sorted_zip_codes]
            print(f"Station distribution: max={max(station_counts)}, min={min(station_counts)}, avg={sum(station_counts)/len(station_counts):.1f}")

            # Process zip codes concurrently - each thread handles one complete zip code
            def fetch_zip_data(zip_code_and_stations):
                zip_code, stations = zip_code_and_stations
                print(f"Fetching data for zip {zip_code} from {len(stations)} stations...")
                combined_data = fetch_and_combine_data_for_zip(zip_code, stations, api_key, max_price)
                save_json_data(combined_data, zip_code, output_dir)
                return zip_code, len(combined_data)

            # Use ThreadPoolExecutor - each thread processes a unique zip code
            # Up to 6 zip codes can be processed simultaneously
            # Zip codes are ordered by station count (most stations first)
            with ThreadPoolExecutor(max_workers=6) as executor:
                future_to_zip = {
                    executor.submit(fetch_zip_data, (zip_code, stations)): zip_code
                    for zip_code, stations in sorted_zip_codes
                }

                for future in as_completed(future_to_zip):
                    zip_code = future_to_zip[future]
                    try:
                        zip_code, listing_count = future.result()
                        print(f"Completed zip {zip_code}: {listing_count} listings")
                    except Exception as e:
                        print(f"Error processing zip {zip_code}: {e}")
        else:
            print("All zip codes already have cached data.")

    # Load all data and process (filtered by Long Island zip codes)
    print("\nLoading and combining Long Island JSON data...")
    all_homes = load_all_json_data(output_dir, allowed_zips)
    print(f"Total Long Island homes loaded: {len(all_homes)}")

    # Remove duplicates (homes near multiple stations)
    print("Removing duplicate listings...")
    unique_homes = deduplicate_homes(all_homes)
    print(f"Unique Long Island homes after deduplication: {len(unique_homes)}")

    # Filter by price, bathrooms, bedrooms, and property type
    filtered_homes = filter_homes_by_criteria(unique_homes, max_price, min_bathrooms=1.5, min_bedrooms=3)
    print(f"Long Island homes under ${max_price:,} (3+ bedrooms, 1.5+ bathrooms, no land): {len(filtered_homes)}")

    # Generate report
    generate_report(unique_homes, max_price)

    # Convert to CSV for mapping
    print(f"\nConverting to CSV format...")
    convert_to_csv(filtered_homes, csv_output_file)

    # Generate zip code inventory report
    print(f"\nGenerating zip code inventory report...")
    inventory_report_file = generate_zip_code_inventory_report(filtered_homes, output_dir, zip_to_station)

    print(f"\nComplete! Filtered homes saved to: {csv_output_file}")
    print(f"Zip code inventory report saved to: {inventory_report_file}")
    print(f"Raw JSON data saved in: {output_dir}")

if __name__ == "__main__":
    main()
