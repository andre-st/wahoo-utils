#!/usr/bin/env ./local/bin/python

# ./local/opt/platform-tools/
#    adb push erst unter einem neuen Namen hochladen (z. B. neue.db) statt direkt ersetzen
#    adb shell mv neue.db alte.db           # Filehandle laufender App zeigt weiterhin auf alte Daten
#    adb shell rm alte.db-wal alte.db-shm   # Journal usw. entfernen
#    adb shell reboot


# Standard:
import argparse
from   argparse import RawTextHelpFormatter
import json
from   uuid import uuid4
from   time import time

# Drittanbieter:
import sqlite3
import pygeohash as pgh

# Eigene:



def cue_title( props ):
	name    = props.get( "name"    ) or ""
	amenity = props.get( "amenity" ) or ""
	
	if amenity:
		amenity = amenity.replace( '_', ' ' )       # "fast_food" -> "fast food"
		amenity = amenity[0].upper() + amenity[1:]  # "toilets"   -> "Toilets" 
	
	title = name if name.startswith( amenity ) else amenity + " " + name;  # "Cafe Cafe Schulze"
	title = title.rstrip();
	return title



def get_user_args():
	parser = argparse.ArgumentParser(
		description = (
			"Adds points of interest from a GeoJSON file to a BoltApp SQLite database\n\n"
			"Author: https://github.com/andre-st/wahoo/" 
		),
		epilog = (
			"Examples:\n"
			"  $ ./poi2db.py route1.geojson route2.geojson route3.geojson \n"
			"  $ ./poi2db.py *.geojson\n"
			"  $ ./poi2db.py --delete\n"
			"\nLicense: ?"
		),
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "poi_files",        help = "Rebuild POI database entirely from scratch from the given list of GeoJSON files", nargs = "*" )
	parser.add_argument( "--delete",         help = "Delete old POIs from database only; only required when there are no POI files", action = "store_true" )
	parser.add_argument( "-o", "--db_file",  help = "path to SQLite database. Defaults to BoltApp.sqlite",  type = str )
	args = parser.parse_args()
	
	if not args.delete and not args.poi_files:
		parser.error( "Missing POI file argument. See --help parameter.")
	
	if args.db_file is None:
		args.db_file = "BoltApp.sqlite"
	
	return args



def main():
	args    = get_user_args()
	conn    = sqlite3.connect( args.db_file )
	cursor  = conn.cursor()
	prog_id = "[poi2db]"
	
	
	# Get user id:
	cursor.execute( "SELECT userCloudId FROM CloudBikingProfileDao WHERE isdeleted = 0 ORDER BY id DESC LIMIT 1" )  # largest ID
	result   = cursor.fetchone();
	if( not result ):
		print( f"[ERROR] Could not retrieve user id from {args.db_file}" )
		exit( 1 )
	else:
		ucloudid = result[0];
		print( f"[DEBUG] User ID = {ucloudid}" )
	
	
	# Reset POI database table:
	print( f"[INFO] Deleting all POIs containing '{prog_id}' from {args.db_file} to prepare a clean slate" )
	cursor.execute( "DELETE FROM CloudPoiDao WHERE address LIKE ?", ( f"%{prog_id}%", ))
	
	
	for poi_file in args.poi_files:
		
		print( f"[INFO] Adding POIs from {poi_file}" );
		
		with open( poi_file, 'r' ) as f:
			geojson = json.load( f )
		
		for feature in geojson.get( "features", [] ):
			
			if feature.get( "geometry", {} ).get( "type" ) == "Point":
				props    = feature.get( "properties", {} )
				addr     = f"{prog_id}"
				lon, lat = feature["geometry"]["coordinates"][:2]
				name     = cue_title( props )
				custom   = bytes.fromhex( "ACED0005737200116A6176612E7574696C2E486173684D61700507DAC1C31660D103000246000A6C6F6164466163746F724900097468726573686F6C6478703F400000000000007708000000100000000078" )  # Serialisierte leere Java-HashMap:
				
				cursor.execute((
						"INSERT INTO CloudPoiDao (address,        custom,        geoHash,      "
						"                         isDeleted,      latDeg,        lonDeg,       "
						"                         name,           poiToken,      poiType,      "
						"                         objectCloudId,  updateTimeMs,  userCloudId ) "
						"VALUES                  (?,              ?,             ?,            "
						"                         ?,              ?,             ?,            "
						"                         ?,              ?,             ?,            "
						"                         ?,              ?,             ?           ) " ),
						# ----------------------------------------------------------------------
						(                         addr,           custom,        pgh.encode( lat, lon, precision = 12 ),
						                          0,              lat,           lon,
						                          name,           str(uuid4()),  0,
						                          0,              time()*1000,   ucloudid    ))
	
	conn.commit()
	conn.close()
	print( f"[INFO] Local database {args.db_file} updated." )
		
	
	# TODO Update database via ADB
	
	



if __name__ == "__main__":
	main()
