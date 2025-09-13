import csv, math, zipfile, os

IN_CSV = "MTA_Rail_Stations_20250913.csv"          # path to your downloaded CSV
OUT_KML = "lirr_15min_walk_circles.kml"  # output KML
MAKE_KMZ = True                          # also write a KMZ zip of the KML

RADIUS_M = 1207  # ≈15 min walk at ~3 mph
EARTH_R = 6371000.0
POINTS = 64      # polygon smoothness (more = smoother circle)

def circle_coords(lat, lon, radius_m, n=64):
    # returns list of (lon,lat) pairs
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    d_r = radius_m / EARTH_R
    result = []
    for k in range(n):
        brng = 2 * math.pi * k / n
        lat2 = math.asin(math.sin(lat_r)*math.cos(d_r) +
                         math.cos(lat_r)*math.sin(d_r)*math.cos(brng))
        lon2 = lon_r + math.atan2(math.sin(brng)*math.sin(d_r)*math.cos(lat_r),
                                  math.cos(d_r)-math.sin(lat_r)*math.sin(lat2))
        result.append((math.degrees(lon2), math.degrees(lat2)))
    result.append(result[0])  # close ring
    return result

# Read CSV
rows = []
with open(IN_CSV, newline='', encoding="utf-8") as f:
    for r in csv.DictReader(f):
        name = r.get("Station Name")
        latitude = float(r["Latitude"])
        longitude = float(r["Longitude"])
        rows.append((name, latitude, longitude))

# Write KML
kml_head = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="https://www.opengis.net/kml/2.2">
<Document>
  <name>LIRR 15-minute walking circles</name>
  <Style id="circle">
    <LineStyle><width>1.2</width><color>ff444444</color></LineStyle>
    <!-- aabbggrr (aa = alpha). 66 ~ 40% opacity -->
    <PolyStyle><color>6644aaff</color><fill>1</fill><outline>1</outline></PolyStyle>
  </Style>
"""
kml_tail = "</Document></kml>\n"

with open(OUT_KML, "w", encoding="utf-8") as out:
    out.write(kml_head)
    for name, latitude, longitude in rows:
        coords = circle_coords(latitude, longitude, RADIUS_M, POINTS)
        coord_str = " ".join([f"{x:.7f},{y:.7f},0" for x, y in coords])  # lon,lat,alt
        placemark = f"""
  <Placemark>
    <name>{name}</name>
    <styleUrl>#circle</styleUrl>
    <ExtendedData>
      <Data name="radius_m"><value>{RADIUS_M}</value></Data>
    </ExtendedData>
    <Polygon>
      <extrude>0</extrude>
      <altitudeMode>clampToGround</altitudeMode>
      <outerBoundaryIs><LinearRing><coordinates>
        {coord_str}
      </coordinates></LinearRing></outerBoundaryIs>
    </Polygon>
  </Placemark>
"""
        out.write(placemark)
    out.write(kml_tail)

if MAKE_KMZ:
    kmz_path = OUT_KML[:-4] + ".kmz"
    with zipfile.ZipFile(kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(OUT_KML, arcname=os.path.basename(OUT_KML))
    print("Wrote:", OUT_KML, "and", kmz_path)
else:
    print("Wrote:", OUT_KML)
