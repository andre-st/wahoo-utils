#!/usr/bin/env ./local/bin/python

# Anmerkungen:
# - "Line" und "LineString" sind hier mehrsegmentige/mehrpunktige Linien mit n>=2 Punkten (aka Pfad/Polyline/...)
# - POI-Typ wie 'food' oder 'water' ist eine stabilere Abstraktion uber POI-Tags; 
#   unterstellt wird immer, was ein Distanz-Radfahrer darunter versteht (z.B. Friedhof bietet oft Trinkwasser)


# Standard:
import argparse
from   argparse import RawTextHelpFormatter
import os

# Drittanbieter:
import geopandas as gpd
import gpxpy
import osmnx as ox
from   osmnx._errors import InsufficientResponseError
import pandas as pd
from   shapely.geometry import LineString

# Eigene:


# Feste Programmkonfiguration:
POI_TYPES_TAGS = {
	"water": {  # = i.S.v. Trinkwasser
		"amenity": [ "fuel", "cafe", "bar", "biergarten", "fast_food", "pub", "ice_cream", "food_court", "bbq", "drinking_water", "water_point", "grave_yard", "marketplace" ],
		"landuse": [ "cemetery" ],
		"shop":    [ "supermarket", "coffee", "convenience", "food", "ice_cream", "water" ]
	},
	"food": {
		"amenity": [ "fuel", "restaurant", "cafe", "biergarten", "fast_food", "ice_cream", "food_court", "bbq", "marketplace" ],
		"shop":    [ "supermarket", "bakery", "coffee", "convenience", "food", "ice_cream", "pasta", "water" ]
	},
	"camp": {
		"amenity": [ "shelter" ],
		"tourism": [ "camp_site", "camp_pitch" ]
	},
	"toilet": {
		"amenity": [ "toilets" ]
	}
}



def get_poi_tags( poi_types ):
	"""
	Kombiniert Tags mehrerer POI-Typen ohne Duplikate
	"""
	tags = {}
	for t in poi_types:
		if t in POI_TYPES_TAGS:
			for key, values in POI_TYPES_TAGS[t].items():
				if key not in tags:
					tags[key] = set()
				tags[key].update( values )
		else:
			raise ValueError( f"[ERROR] Given POI type '{t}' is not supported" )
	
	for key in tags:  # Fuer Overpass wieder listen statt duplikatfreie sets
		tags[key] = list( tags[key] )
	
	return tags



def query_osm_pois( points, poi_radius, poi_tags ):
	"""
	Features-Abfrage beim OSM-Server (Overpass API) fuer ein Strecke
	"""
	try:
		# Strecke mit Umhuellung/Padding/Puffer als Grenzbereich fuer POIs:
		line     = LineString( points )
		buffered = line.buffer( poi_radius )
		buffered = buffered.simplify( tolerance = 0.001, preserve_topology = True )  # 0.001 = 100 m
		
		# Statt Punkte sind OSM-POIs manchmal Polygone, dort dann das Zentrum ermitteln:
		# OSM-Koordinaten liegen lat/lon EPSG:4326 vor, 
		# shapely berechnet den Zentroiden aber in den Einheiten der UTM-CRS, daher umwandeln:
		coords               = list( buffered.exterior.coords )
		mid_lon              = sum( lon for lon, lat in coords ) / len( coords )
		utm_zone             = int( (mid_lon + 180) // 6 ) + 1   # Universal Transverse Mercator unterteilt Erde in 60 Zonen, jede 6 Grad breit in Laengengrad. Die Zonen sind durchnummeriert von 1 bis 60, von West nach Ost, beginnend bei 180 Grad West.
		utm_crs              = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"
		
		pois                 = ox.features_from_polygon( buffered, poi_tags )
		pois_utm             = pois.to_crs( utm_crs )
		pois_utm["centroid"] = pois_utm.geometry.centroid
		pois["geometry"]     = pois_utm["centroid"].to_crs( epsg = 4326 )  # zurueck in lat/lon
		
		return pois
		
	except InsufficientResponseError:  # Nichts gefunden
		return gpd.GeoDataFrame()     # .empty



def load_gpx_points( filepath ):
	"""
	Extrahiert die Strecken-Geokoordinaten aus einer GPX-Datei
	"""
	with open( filepath, "r" ) as f:
		gpx = gpxpy.parse( f )
	
	return [(p.longitude, p.latitude) for t in gpx.tracks for s in t.segments for p in s.points]



def get_user_args():
	parser = argparse.ArgumentParser(
		description = (
			"Queries OpenStreetMap for points of interest (POI) within a given radius along your route and writes them to a GeoJSON file\n\n"
			"Author: https://github.com/andre-st/wahoo/" 
		),
		epilog = (
			"Examples:\n"
			"  ./gpx2poi.py --poi-types=water,food  your_route.gpx\n"
			"\n"
			"License: ?"
		),
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "gpx_file",               help = "load route from the given GPX file path", type = str )
	parser.add_argument( "-t", "--poi-types",      help = "comma-separated list: water,food,camp,toilet. Defaults to water,food", default = "water,food", type=lambda s: s.split( "," ))
	parser.add_argument( "-o", "--poi-file",       help = "save POIs in GeoJSON format to the given file path (default is your GPX-file path with .geojson extension)", type = str )
	parser.add_argument( "-r", "--poi-radius-deg", help = "max. distance of a POI to your route, defaults to 0.001 (ca. 100 meter because 1 degree of latitude ~111 km)", type = float, default = 0.001 )
	args = parser.parse_args()
	
	if args.poi_file is None:
		base, ext     = os.path.splitext( args.gpx_file )
		args.poi_file = base + ".geojson"
	
	return args



def main():
	args     = get_user_args()
	points   = load_gpx_points( args.gpx_file )
	poi_tags = get_poi_tags( args.poi_types )
	pois     = query_osm_pois( points, args.poi_radius_deg, poi_tags )
	
	if not pois.empty:
		gdf_all = pd.concat([ pois ])   # GeoDataFrame
		gdf_all.to_file( args.poi_file, driver = "GeoJSON" )
		print( f"[INFO] {len(gdf_all)} points of interest saved to: {args.poi_file}" )
	else:
		print( "[WARN] No points of interest found")



if __name__ == "__main__":
	main()
