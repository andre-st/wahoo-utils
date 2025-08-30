#!/usr/bin/env ./local/bin/python

# Anmerkungen:
# - "Line" und "LineString" sind hier mehrsegmentige/mehrpunktige Linien mit n>=2 Punkten (aka Pfad/Polyline/...)
# - POI-Typ wie 'food' oder 'water' ist eine stabilere Abstraktion uber POI-Tags; 
#   unterstellt wird immer, was ein Distanz-Radfahrer darunter versteht (z.B. Friedhof bietet oft Trinkwasser)
#
# TODO:
# - POIs mit unpassenden Oeffnungszeiten entfernen
# - POIs mit niedrigen Google/Foursquare-Bewertungen entfernen?
# - 



# Standard:
import argparse
from   argparse import RawTextHelpFormatter
import math
import os
import time

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
	# "repair":   radwerkstatt
	# "firstaid": apotheken
}

OSM_QUERY_DELAY_SECS = 2



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
			raise ValueError( f"[ERROR] Given POI type '{t}' is not supported. See --help parameter" )
	
	for key in tags:  # Fuer Overpass wieder listen statt duplikatfreie sets
		tags[key] = list( tags[key] )
	
	return tags



def query_osm_pois( points, poi_radius_m, poi_tags ):
	"""
	Features-Abfrage beim OSM-Server (Overpass API) fuer ein Strecke
	"""
	try:
		# Buffer-Radius berechnen
		mid_lon    = sum( p[0] for p in points ) / len( points )   # Durchschnitt
		mid_lat    = sum( p[1] for p in points ) / len( points )   # Durchschnitt
		lat_deg    = poi_radius_m /  111320                                        # Abstand zw. 2 Breitenkreisen, deren geogr. Breite sich um 1 Grad unterscheidet, betraegt immer 111,320 Meter
		lon_deg    = poi_radius_m / (111320 * math.cos( math.radians( mid_lat )))  # Abstand zw. 2 Laengenkreisen haengt vom Breitengrad ab, laufen am Pol zusammen
		radius_deg = max( lat_deg, lon_deg )  # Buffer in beide Richtungen mind.gewuenschte Groesse, auch wenn Laengengrad kleiner ist
		
		# Strecke mit Umhuellung/Padding/Puffer als Grenzbereich fuer POIs:
		line     = LineString( points )
		buffered = line.buffer( radius_deg )
		buffered = buffered.simplify( tolerance = 0.001, preserve_topology = True )  # 0.001 = 100 m
		
		# Statt Punkte sind OSM-POIs manchmal Polygone, dort dann das Zentrum ermitteln:
		# OSM-Koordinaten liegen lat/lon EPSG:4326 vor, 
		# shapely berechnet den Zentroiden aber in den Einheiten der UTM-CRS, daher umwandeln:
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
			"Author: https://github.com/andre-st/" 
		),
		epilog = (
			"Examples:\n"
			"  ./gpx2poi.py --poi-types=water,food  routes/*.gpx\n"
			"\n"
			"License:\n"
			"   MIT License"
		),
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "gpx_files",          help = "load route from the given GPX file path", nargs = "+" )
	parser.add_argument( "-t", "--poi-types",  help = "comma-separated list: water,food,camp,toilet. Defaults to water,food", default = "water,food", type=lambda s: s.split( "," ))
	parser.add_argument( "-r", "--poi-radius", help = "max. distance of a POI to your route in meter, defaults to 100", type = int, default = 100 )
	args = parser.parse_args()
	
	return args



def main():
	args     = get_user_args()
	poi_tags = get_poi_tags( args.poi_types )
	
	for i, gpx_file in enumerate( args.gpx_files ):
		print( f"[INFO] Processing GPX file: {gpx_file}" )
		
		base, ext  = os.path.splitext( gpx_file )
		poi_file   = base + ".geojson"
		points     = load_gpx_points( gpx_file )
		pois       = query_osm_pois( points, args.poi_radius, poi_tags )
		
		if not pois.empty:
			gdf_all = pd.concat([ pois ])   # GeoDataFrame
			gdf_all.to_file( poi_file, driver = "GeoJSON" )
			print( f"[INFO] {len(gdf_all)} points of interest saved to: {poi_file}" )
		else:
			print( "[WARN] No points of interest found for: {gpx_file}" )
		
		if i != len( args.gpx_files ) - 1:
			time.sleep( OSM_QUERY_DELAY_SECS )


if __name__ == "__main__":
	main()
