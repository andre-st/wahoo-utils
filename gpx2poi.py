#!/usr/bin/env ./myenv/bin/python

# TODO: Entferne Parallelverarbeitung: verkompliziert Code ohne echten Vorteil, da OSM-Server drosselt und eh alles wartet


import gpxpy
import geopandas as gpd
from shapely.geometry import LineString, Point
import osmnx as ox
import pandas as pd
from tqdm import tqdm
import time


GPX_FILE         = "my_route.gpx"
POI_FILE         = "my_route.geojson"
POI_TAGS         = { "amenity": [ "restaurant","cafe","bar","biergarten","fast_food","pub","ice_cream","food_court","bbq","drinking_water","shelter","toilets","water_point","grave_yard","marketplace" ], "landuse": [ "cemetery"] }
POI_RADIUS_DEG   = 0.001  # 0.001 =  100m
BBOX_MAX_W_DEG   = 0.010  # 0.010 = 1000m
BBOX_MAX_H_DEG   = 0.010
QUERY_DELAY_SECS = 0



def split_by_bbox( points, max_w, max_h, poi_radius ):
	"""
	Wir versuchen die bounding boxes fuer die OSM-Abfragen zu reduzieren,
	um die OSM-Server-Last (fair use) und Programmlaufzeit zu verringern,
	also 1 Abfrage fuer mehrere Teilstuecke statt z.B. 1500 Abfragen fuer 1500 Teilstuecke.
	"""
	lines, seg = [], []
	for pt in points:
		seg.append( pt )
		if len( seg ) > 1:
			buffered = LineString( seg ).buffer( poi_radius )  # mit Umhuellung messen
			minx, miny, maxx, maxy = buffered.bounds
			if( maxx - minx > max_w ) or ( maxy - miny > max_h ):
				lines.append( LineString( seg[:-1] ))
				seg = [seg[-1]]
	
	if len( seg ) > 1:
		lines.append( LineString( seg ))
	
	return lines




def query_osm_pois( buffer ):
	"""
	Features-Abfrage beim OSM-Server (Overpass API).
	Das buffer-Argument ist uebrigens kein LineString: buffer() liefert ein Polygon in shapely
	"""
	try:
		time.sleep( QUERY_DELAY_SECS )  # Server schonen/evtl. Blocking verhindern
		
		# Statt Punkte sind OSM-POIs manchmal Polygone, dort dann das Zentrum ermitteln:
		# OSM-Koordinaten liegen lat/lon EPSG:4326 vor, 
		# shapely berechnet den Zentroiden aber in den Einheiten der UTM-CRS, 
		# daher umwandeln:
		#
		coords               = list( buffer.exterior.coords )
		mid_lon              = sum( lon for lon, lat in coords ) / len( coords )
		utm_zone             = int( (mid_lon + 180) // 6 ) + 1   # Universal Transverse Mercator unterteilt Erde in 60 Zonen, jede 6 Grad breit in Laengengrad. Die Zonen sind durchnummeriert von 1 bis 60, von West nach Ost, beginnend bei 180 Grad West.
		utm_crs              = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"
		
		pois                 = ox.features_from_bbox( bbox = buffer.bounds, tags = POI_TAGS )
		pois_utm             = pois.to_crs( utm_crs )
		pois_utm["centroid"] = pois_utm.geometry.centroid
		pois["geometry"]     = pois_utm["centroid"].to_crs( epsg = 4326 )  # zurueck in lat/lon
		pois_nearby          = pois[ pois.geometry.within( buffer )]
		
		return pois_nearby
		
	except Exception as e:
		return gpd.GeoDataFrame()   # empty



def load_gpx_points( filepath ):
	"""
	Extrahiert die Strecken-Geokoordinaten aus einer GPX-Datei
	"""
	with open( filepath, "r" ) as f:
		gpx = gpxpy.parse( f )
	return [(p.longitude, p.latitude) for t in gpx.tracks for s in t.segments for p in s.points]



def main():
	# Eine fruehere Version hat ThreadPoolExecutor verwendet, wurde aber wieder entfernt,
	# weil der OSM-Server drosselt und der umstaendlichere Code dann keinen Vorteil hatte.
	# Eher sinnvoll bei Abfragen gegen mehrere unabhaengige Server.
	
	all_pois = []
	points  = load_gpx_points( GPX_FILE )
	lines   = split_by_bbox( points, BBOX_MAX_W_DEG, BBOX_MAX_H_DEG, POI_RADIUS_DEG )
	
	for line in tqdm( lines, desc="Verarbeite" ):
		buffer   = line.buffer( POI_RADIUS_DEG )        # Linie mit Umhuellung/Padding/Puffer
		buf_pois = query_osm_pois( buffer )
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
