#!/usr/bin/env ./local/bin/python

# Standard:
import argparse
from   argparse import RawTextHelpFormatter
import json
import subprocess
from   uuid import uuid4
import os
import tempfile
from   time import time

# Drittanbieter:
import adbutils
import sqlite3
import pygeohash as pgh

# Eigene:


# Feste Programmkonfiguration:
PROG_ID         = "[poi2db]"  # Magic number to identify database rows added by this program
ADB_DB_DIR      = "/data/data/com.wahoofitness.bolt/databases"
ADB_DB_FILENAME = "BoltApp.sqlite"



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
			"  ./poi2db.py route1.geojson route2.geojson route3.geojson \n"
			"  ./poi2db.py --adb  routes/*.geojson\n"
			"  ./poi2db.py --db_file=BoltAppTest.sqlite --delete\n"
			"\n"
			"License: ?"
		),
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "poi_files",        help =  "rebuild POI database entirely from scratch from the given list of GeoJSON files", nargs = "*" )
	parser.add_argument( "-d", "--delete",   help =  "delete old POIs from database only; only required when there are no POI files", action = "store_true" )
	parser.add_argument( "-a", "--adb",      help =  "directly update database on bike computer via ADB instead of a local database file", action = "store_true" )
	parser.add_argument( "-o", "--db_file",  help = f"path to SQLite database. Defaults to '{ADB_DB_FILENAME}' (ignored if --adb)",  type = str )
	args = parser.parse_args()
	
	if not args.delete and not args.poi_files:
		parser.error( "Missing POI file argument. See --help parameter.")
	
	if args.db_file is None:
		args.db_file = ADB_DB_FILENAME
	
	return args



def main():
	args       = get_user_args()
	adb_device = None
	
	
	##########################################################################
	#
	#  Get bike computer BoltApp database
	#
	
	if( args.adb ):
		tmpfname     = "poi2db_" + next( tempfile._get_candidate_names() ) + ".sqlite"
		tmpfpath     = os.path.join( tempfile.gettempdir(), tmpfname )
		args.db_file = tmpfpath
		print( f"[INFO] ADB: Copying database from bike computer to '{args.db_file}'" )
		subprocess.run([ "local/opt/platform-tools/adb", "start-server" ], check = True )  # or exception  TODO fixed string
		adb_device   = adbutils.adb.device()                             # First device, or exception
		adb_device.sync.pull( ADB_DB_DIR + "/" + ADB_DB_FILENAME, args.db_file )  # or exception

	
	##########################################################################
	#
	#  Update local BoltApp database
	#
	
	
	db_conn   = sqlite3.connect( args.db_file )
	db_cursor = db_conn.cursor()
	
	# Get user id:
	db_cursor.execute( "SELECT userCloudId FROM CloudBikingProfileDao WHERE isDeleted = 0 ORDER BY id DESC LIMIT 1" )  # largest ID
	result = db_cursor.fetchone();
	if( not result ):
		print( f"[ERROR] Could not retrieve user id from {args.db_file}" )
		exit( 1 )
	else:
		ucloudid = result[0];
		print( f"[DEBUG] userCloudId = {ucloudid}" )
	
	
	# Reset POI database table:
	print( f"[INFO] Deleting all POIs containing '{PROG_ID}' from {args.db_file} to prepare a clean slate" )
	db_cursor.execute( "DELETE FROM CloudPoiDao WHERE address LIKE ?", ( f"%{PROG_ID}%", ))
	
	
	for poi_file in args.poi_files:
		print( f"[INFO] Adding POIs from file '{poi_file}' to '{args.db_file}'" );
		with open( poi_file, 'r' ) as f:
			geojson = json.load( f )
		
		for feature in geojson.get( "features", [] ):
			
			if feature.get( "geometry", {} ).get( "type" ) == "Point":
				props    = feature.get( "properties", {} )
				addr     = f"{PROG_ID}"
				lon, lat = feature["geometry"]["coordinates"][:2]
				name     = cue_title( props )
				custom   = bytes.fromhex( "ACED0005737200116A6176612E7574696C2E486173684D61700507DAC1C31660D103000246000A6C6F6164466163746F724900097468726573686F6C6478703F400000000000007708000000100000000078" )  # Serialisierte leere Java-HashMap:
				
				db_cursor.execute((
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
	
	print( f"[INFO] Committing changes to local database '{args.db_file}'" )
	db_conn.commit()
	db_conn.close()
	
	
	##########################################################################
	# 
	#  Update bike computer database via ADB
	#
	
	if( adb_device ):
		# Upload new and rename = filehandle of the running app still points to the old data;
		# delete wal/shm journal files otherwise it will overwrite our data after reboot
		
		print( f"[INFO] ADB: Copying local database '{args.db_file}' to bike computer and rebooting" )
		adb_device.sync.push( args.db_file, ADB_DB_DIR + "/" + ADB_DB_FILENAME + "-poi2db" );  # Exception otherwise
		
		cmd = ( 
			f"cd '{ADB_DB_DIR}' "
			f"&& chown $(stat -c %u:%g '{ADB_DB_FILENAME}') '{ADB_DB_FILENAME}-poi2db'  "  # chown --reference=orgfile newfile  not avail
			f"&& chmod $(stat -c %a    '{ADB_DB_FILENAME}') '{ADB_DB_FILENAME}-poi2db'  "  # chmod --reference=orgfile newfile  not avail
			f"&& cp '{ADB_DB_FILENAME}'                     '{ADB_DB_FILENAME}.bak'     "
			f"&& mv '{ADB_DB_FILENAME}-poi2db'              '{ADB_DB_FILENAME}'         "
			f"&& mv '{ADB_DB_FILENAME}-wal'                 '{ADB_DB_FILENAME}-wal.bak' "
			f"&& mv '{ADB_DB_FILENAME}-shm'                 '{ADB_DB_FILENAME}-shm.bak' "
			f"&& reboot  "
		)
		out = adb_device.shell( cmd )
		print( out )


if __name__ == "__main__":
	main()
