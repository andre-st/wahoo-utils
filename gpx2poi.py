#!/usr/bin/env ./myenv/bin/python

# Anmerkungen:
# - "Line" und "LineString" sind hier mehrsegmentige/mehrpunktige Linien mit n>=2 Punkten (aka Pfad/Polyline/...)
#


# Standard:
import argparse
from   argparse import RawTextHelpFormatter
import os
import time

# Drittanbieter:
import geopandas as gpd
import gpxpy
import osmnx as ox
from   osmnx._errors import InsufficientResponseError
import pandas as pd
from   shapely.geometry import LineString
from   tqdm import tqdm

# Eigene:



# Programmkonfiguration:
POI_TAGS         = { "amenity": [ "restaurant","cafe","bar","biergarten","fast_food","pub","ice_cream","food_court","bbq","drinking_water","shelter","toilets","water_point","grave_yard","marketplace" ], "landuse": [ "cemetery"] }
BBOX_SIZE_DEG    = 0.025  # 0.010 = 1000m  Kachelbreite/-hoehe fuer OSM-Abfragen (Sweetspot zw. Abfragenmenge und Datenmenge pro Abfrage)
QUERY_DELAY_SECS = 0.500  # Server schonen (fair use), mgl. Blocking vermeiden



def split_by_bbox( points, max_w, max_h, poi_radius ):
	"""
	Wir reduzieren die Menge der Bounding Boxes fuer die OSM-Abfragen,
	indem wir sie ueber mehrere Streckensegmente bilden,
	solange die Box unter einer Maximaldimension bleibt.
	Der naive Algorithmus performt sonst immer den worst case 
	von z.B. 1500 Abfragen fuer 1500 Streckensegmente.
	Wir verringern dadurch die OSM-Server-Last (fair use) und 
	die Gesamtlaufzeit des Programms (CPU < IO).
	"""
	lines, seg = [], []
	for pt in points:
		seg.append( pt )
		
		if len( seg ) > 1:
			buffered = LineString( seg ).buffer( poi_radius )  # mit Umhuellung messen
			minx, miny, maxx, maxy = buffered.bounds
			
			if( maxx - minx > max_w ) or ( maxy - miny > max_h ):
				lines.append( LineString(  seg[:-1] if len( seg ) > 2 else [seg[0], seg[0]]  ))  # Falls nur 1 Punkt
				seg = [seg[-1]]
	
	if seg:
		lines.append( LineString( seg if len( seg ) > 1 else [seg[0], seg[0]] ))  # Falls nur 1 Punkt
	
	return lines



def query_osm_pois( line, poi_radius, poi_tags ):
	"""
	Features-Abfrage beim OSM-Server (Overpass API) fuer ein Strecke
	"""
	try:
		buffered = line.buffer( poi_radius )   # Strecke mit Umhuellung/Padding/Puffer als Grenzbereich fuer POIs
		
		# Statt Punkte sind OSM-POIs manchmal Polygone, dort dann das Zentrum ermitteln:
		# OSM-Koordinaten liegen lat/lon EPSG:4326 vor, 
		# shapely berechnet den Zentroiden aber in den Einheiten der UTM-CRS, 
		# daher umwandeln:
		#
		coords               = list( buffered.exterior.coords )
		mid_lon              = sum( lon for lon, lat in coords ) / len( coords )
		utm_zone             = int( (mid_lon + 180) // 6 ) + 1   # Universal Transverse Mercator unterteilt Erde in 60 Zonen, jede 6 Grad breit in Laengengrad. Die Zonen sind durchnummeriert von 1 bis 60, von West nach Ost, beginnend bei 180 Grad West.
		utm_crs              = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"
		
		pois                 = ox.features_from_bbox( bbox = buffered.bounds, tags = poi_tags )
		pois_utm             = pois.to_crs( utm_crs )
		pois_utm["centroid"] = pois_utm.geometry.centroid
		pois["geometry"]     = pois_utm["centroid"].to_crs( epsg = 4326 )  # zurueck in lat/lon
		pois_nearby          = pois[ pois.geometry.within( buffered )]
		
		return pois_nearby
		
	except InsufficientResponseError:
		return gpd.GeoDataFrame()   # empty



def load_gpx_points( filepath ):
	"""
	Extrahiert die Strecken-Geokoordinaten aus einer GPX-Datei
	"""
	with open( filepath, "r" ) as f:
		gpx = gpxpy.parse( f )
	
	return [(p.longitude, p.latitude) for t in gpx.tracks for s in t.segments for p in s.points]



def main():
	
	# Benutzerkonfiguration:
	parser = argparse.ArgumentParser( 
		description = (
			"Queries OpenStreetMap for points of interest (POI) within a given radius along your route and writes them to a GeoJSON file\n\n"
			"Author: https://github.com/andre-st/wahoo/" 
		),
		epilog          = "License: ?",
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "gpx_file",               help = "load route from the given GPX file path", type = str )
	parser.add_argument( "-o", "--poi-file",       help = "save POIs in GeoJSON format to the given file path (default is your GPX-file path with .geojson extension)", type = str )
	parser.add_argument( "-r", "--poi-radius-deg", help = "max. distance of a POI to your route, defaults to 0.001 (100 meter)", type = float, default = 0.001 )
	args = parser.parse_args()
	
	if args.poi_file is None:
		base, ext     = os.path.splitext( args.gpx_file )
		args.poi_file = base + ".geojson"
	
	
	# Der ThreadPoolExecutor einer frueheren Programmversion wurde entfernt,
	# weil die OSM-Server drosseln (vermutlich anhand der IP-Adresse) und ein 
	# umstaendlicher Code fuer parallele Abfragen dann keinen Nutzen mehr hat.
	# Eher sinnvoll bei Abfragen gegen mehrere unabhaengige Server.
	#
	all_pois = []
	points   = load_gpx_points( args.gpx_file )
	lines    = split_by_bbox( points, BBOX_SIZE_DEG, BBOX_SIZE_DEG, args.poi_radius_deg )
	
	for line in tqdm( lines, desc = "Querying OSM route tiles" ):
		buf_pois = query_osm_pois( line, args.poi_radius_deg, POI_TAGS )
		time.sleep( QUERY_DELAY_SECS )
		
		if not buf_pois.empty:
			all_pois.append( buf_pois )
	
	
	if all_pois:
		gdf_all = pd.concat( all_pois )   # GeoDataFrame
		gdf_all = gdf_all.drop_duplicates()
		gdf_all.to_file( args.poi_file, driver = "GeoJSON" )
		print( f"{len(gdf_all)} POIs saved to {args.poi_file}" )
	else:
		print( "No POIs found!")



if __name__ == "__main__":
	main()
