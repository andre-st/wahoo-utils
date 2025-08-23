#!/usr/bin/env ./myenv/bin/python

# Generiert eine KML-Datei mit der Route und den POIs dazu.
# Diente mir bisher zum Testen von poi.py


import gpxpy
import geopandas as gpd
import simplekml
from   shapely.geometry import LineString


GPX_FILE = "my_route.gpx"
POI_FILE = "my_route.geojson"
KML_FILE = "my_route.kml"


with open( GPX_FILE, "r" ) as f:
	gpx = gpxpy.parse( f )

points = [(p.latitude, p.longitude) for t in gpx.tracks for s in t.segments for p in s.points]
pois   = gpd.read_file( POI_FILE )
kml    = simplekml.Kml()

# GPX-Route als Linie hinzufügen
linestring = kml.newlinestring( name="Route", coords=[ (lon, lat) for lat, lon in points ])
linestring.style.linestyle.width = 4
linestring.style.linestyle.color = simplekml.Color.blue

# POIs als Punkte hinzufügen
for idx, row in pois.iterrows():
	lat, lon = row.geometry.y, row.geometry.x
	amenity  = row.get( "amenity" ) or "POI"
	amenity  = amenity[0].upper() + amenity[1:]  # "Toilets" statt "toilets"
	name     = row.get( "name" ) or ""
	title    = name if name.startswith( amenity ) else amenity + " " + name;  # "Cafe Cafe Schulze"
	title    = title.rstrip();
	p        = kml.newpoint( name=title, coords=[(lon, lat)] )

	# Farbcode
	h = hash( amenity )
	r = (h & 0xFF0000) >> 16
	g = (h & 0x00FF00) >> 8
	b =  h & 0x0000FF
	p.style.iconstyle.color     = simplekml.Color.rgb( r, g, b );
	p.style.iconstyle.icon.href = "https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png"  # Sonst kein color


kml.save( KML_FILE )
print( f"KML-Datei gespeichert als {KML_FILE}" )


