import os, time, googlemaps, csv, sys

gmaps = googlemaps.Client(key=os.environ["GOOGLE_MAPS_API_KEY"])

def parse_address_components(components):
    """Parse Google Maps address components into a dictionary"""
    result = {
        "postal_code": None,
        "locality": None,
        "administrative_area_level_1": None,
        "country": None,
        "street_number": None,
        "route": None
    }

    for component in components:
        for comp_type in component["types"]:
            if comp_type in result:
                result[comp_type] = component["long_name"]

    return result

def reverse_geocode_gmclient(lat, lng):
    """Get address information including zip code from lat/lng coordinates"""
    try:
        res = gmaps.reverse_geocode((lat, lng))
        if not res:
            return None
        result = res[0]
        comps = parse_address_components(result.get("address_components", []))
        return {
            "formatted_address": result.get("formatted_address"),
            "postal_code": comps["postal_code"],
            "city": comps["locality"],
            "state": comps["administrative_area_level_1"],
            "country": comps["country"],
            "street_number": comps["street_number"],
            "route": comps["route"]
        }
    except Exception as e:
        print(f"Error geocoding {lat}, {lng}: {e}")
        return None

def enrich_csv_with_zip_codes(input_file, output_file):
    """Read CSV file and add zip code column based on lat/lng"""
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['Zip_Code']

        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                try:
                    lat = float(row['Latitude'])
                    lng = float(row['Longitude'])

                    print(f"Processing {row['Station Name']}...")
                    geocode_result = reverse_geocode_gmclient(lat, lng)

                    if geocode_result and geocode_result['postal_code']:
                        row['Zip Code'] = geocode_result['postal_code']
                    else:
                        row['Zip Code'] = 'N/A'

                    writer.writerow(row)

                    # Add delay to respect API rate limits
                    time.sleep(0.1)

                except (ValueError, KeyError) as e:
                    print(f"Error processing row for {row.get('Station Name', 'Unknown')}: {e}")
                    row['Zip Code'] = 'ERROR'
                    writer.writerow(row)

if __name__ == "__main__":
    input_file = "MTA_Rail_Stations_20250913.csv"
    output_file = "MTA_Rail_Stations_with_zip.csv"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        sys.exit(1)

    if "GOOGLE_MAPS_API_KEY" not in os.environ:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        sys.exit(1)

    print(f"Enriching {input_file} with zip codes...")
    enrich_csv_with_zip_codes(input_file, output_file)
    print(f"Complete! Output saved to {output_file}")
