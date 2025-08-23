#!/usr/bin/env ./myenv/bin/python

import gpxpy
import geopandas as gpd
from shapely.geometry import LineString, Point
import osmnx as ox
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time


SEGMENT_POI_RADIUS   = 0.001  # 0.001 = 100m
GPX_FILE             = "my_route.gpx"
POI_FILE             = "my_route_pois.json"
POI_TAGS             = { "amenity": [ "restaurant","cafe","bar","biergarten","fast_food","pub","ice_cream","food_court","bbq","drinking_water","shelter","toilets","water_point","grave_yard","marketplace" ], "landuse": [ "cemetery"] }
WORKERS_COUNT        = 2
WORKERS_DELAY_SECS   = 0.0
WORKERS_TIMEOUT_SECS = 10


def query_osm_pois( buffer ):
	try:
		time.sleep( WORKERS_DELAY_SECS )
		# Statt Punkte sind OSM-POIs manchmal Polygone, dort dann das Zentrum ermitteln:
		# OSM-Koordinaten liegen lat/lon EPSG:4326 vor, 
		# shapely berechnet den Zentroiden aber in den Einheiten der UTM-CRS, 
		# daher umwandeln:
		coords               = list( buffer.exterior.coords )
		mid_lon              = sum( lon for lon, lat in coords ) / len( coords )
		utm_zone             = int( (mid_lon + 180) // 6 ) + 1   # Universal Transverse Mercator unterteilt Erde in 60 Zonen, jede 6 Grad breit in Laengengrad. Die Zonen sind durchnummeriert von 1 bis 60, von West nach Ost, beginnend bei 180 Grad West.
		utm_crs              = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"
		pois                 = ox.features_from_bbox( bbox=buffer.bounds, tags=POI_TAGS )
		pois_utm             = pois.to_crs( utm_crs )
		pois_utm["centroid"] = pois_utm.geometry.centroid
		pois["geometry"]     = pois_utm["centroid"].to_crs( epsg=4326 )  # zurueck in lat/lon
		pois_nearby          = pois[ pois.geometry.within( buffer )]
		return pois_nearby
	except Exception as e:
		return gpd.GeoDataFrame()   # empty



def main():
	with open( GPX_FILE, "r" ) as f:
		gpx = gpxpy.parse( f )
	
	all_pois = []
	
	
	with ThreadPoolExecutor( max_workers=WORKERS_COUNT ) as executor:
		futures = []
		points  = [(p.longitude, p.latitude) for t in gpx.tracks for s in t.segments for p in s.points]
		# Streckensegmente bei OpenStreetMap parallel abfragen (bringt nicht viel dank IP-Drosselung):
		for i in range( len( points ) - 1 ):
			lon1, lat1 = points[i]
			lon2, lat2 = points[i+1]
			segment    = LineString( [(lon1, lat1), (lon2, lat2)] )  # Linie fuer Segment
			buffer     = segment.buffer( SEGMENT_POI_RADIUS )        # Linie mit Umhuellung/Padding/Puffer
			future     = executor.submit( query_osm_pois, buffer )
			futures.append( future )
		
		for future in tqdm( as_completed( futures ), total=len( futures )):  # tqdm fuer Fortschrittsbalken
			buf_pois = future.result( timeout=WORKERS_TIMEOUT_SECS )
			if not buf_pois.empty:
				all_pois.append( buf_pois )  # Zusammenfuehren
	
	
	if all_pois:
		
		
		
		gdf_all = pd.concat( all_pois )   # GeoDataFrame
		gdf_all = gdf_all.drop_duplicates()
		gdf_all.to_file( POI_FILE, driver="GeoJSON" )
		print( f"{len(gdf_all)} POIs entlang der Route gespeichert!" )
	else:
		print( "Keine POIs gefunden!")



if __name__ == "__main__":
	main()
