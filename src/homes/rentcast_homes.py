import os, requests, json, csv, sys
from datetime import datetime
import time

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

def fetch_rentcast_data(zip_code, api_key, max_price=600000):
    """Fetch homes for sale data from RentCast API for a given zip code"""
    url = "https://api.rentcast.io/v1/listings/sale"

    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }

    params = {
        "zipCode": zip_code,
        "status": "Active",
        "maxPrice": max_price,
        "limit": 500  # Get all available listings
    }

    try:
        print(f"Fetching data for zip code {zip_code}...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        print(f"Found {len(data)} listings in {zip_code}")
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
                print(f"Skipping {filename} - not in Long Island zip codes")
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

def convert_to_csv(homes, output_file):
    """Convert the homes data to CSV format for mapping"""
    if not homes:
        print("No homes data to convert")
        return

    # Define the CSV columns we want for mapping
    fieldnames = [
        'id', 'formattedAddress', 'addressLine1', 'city', 'state', 'zipCode',
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

def main():
    # Configuration
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    stations_csv = f"{data_dir}/MTA_Rail_Stations_with_zip.csv"
    zip_codes_file = f"{data_dir}/zipcodes.txt"
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', '.tmp')
    max_price = 600000  # $600k budget

    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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

    # Check if API key is available for fetching new data
    if "RENTCAST_API_KEY" not in os.environ:
        print("Warning: RENTCAST_API_KEY environment variable not set")
        print("Skipping API calls and using existing JSON files only...")
        print("Get your API key from https://www.rentcast.io/ to fetch new data")
        api_key = None
    else:
        api_key = os.environ["RENTCAST_API_KEY"]

        # Get unique zip codes from stations (filtered by Long Island)
        print("Extracting zip codes from MTA stations...")
        zip_codes = get_unique_zip_codes(stations_csv, allowed_zips)
        print(f"Found {len(zip_codes)} Long Island zip codes: {', '.join(zip_codes)}")

        # Fetch data for each zip code (if not already cached)
        for zip_code in zip_codes:
            json_file = os.path.join(output_dir, f"{zip_code}.json")

            if os.path.exists(json_file):
                print(f"Data for {zip_code} already exists, skipping...")
                continue

            data = fetch_rentcast_data(zip_code, api_key, max_price)
            save_json_data(data, zip_code, output_dir)

            # Rate limiting - be nice to the API
            time.sleep(1)

    # Load all data and process (filtered by Long Island zip codes)
    print("\nLoading and combining Long Island JSON data...")
    all_homes = load_all_json_data(output_dir, allowed_zips)
    print(f"Total Long Island homes loaded: {len(all_homes)}")

    # Filter by price, bathrooms, bedrooms, and property type
    filtered_homes = filter_homes_by_criteria(all_homes, max_price, min_bathrooms=1.5, min_bedrooms=3)
    print(f"Long Island homes under ${max_price:,} (3+ bedrooms, 1.5+ bathrooms, no land): {len(filtered_homes)}")

    # Generate report
    generate_report(all_homes, max_price)

    # Convert to CSV for mapping
    print(f"\nConverting to CSV format...")
    convert_to_csv(filtered_homes, csv_output_file)

    print(f"\nComplete! Filtered homes saved to: {csv_output_file}")
    print(f"Raw JSON data saved in: {output_dir}")

if __name__ == "__main__":
    main()
