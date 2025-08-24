#!/usr/bin/env ./myenv/bin/python

# Anmerkungen:
# - TCX-Schema: https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd


# Standard:
import argparse
from   argparse import RawTextHelpFormatter
import json
import os

# Drittanbieter:
import gpxpy
from   lxml import etree as ET

# Eigene:



# Feste Programmkonfiguration:
TAGS_FOOD     = { "fuel", "restaurant", "cafe", "bar", "biergarten", "fast_food", "pub", "ice_cream", "food_court", "bbq", "marketplace", "supermarket", "bakery", "convenience", "food", "pasta" }
TAGS_WATER    = { "drinking_water", "toilets", "water_point", "water", "cemetery", "grave_yard" }
TAGS_DANGER   = {}
TAGS_FIRSTAID = { "shelter", "camp_site", "camp_pitch" }



def cue_title( props ):
	name    = props.get( "name"    ) or ""
	amenity = props.get( "amenity" ) or ""
	
	if amenity:
		amenity = amenity.replace( '_', ' ' )       # "fast_food" -> "fast food"
		amenity = amenity[0].upper() + amenity[1:]  # "toilets"   -> "Toilets" 
	
	title = name if name.startswith( amenity ) else amenity + " " + name;  # "Cafe Cafe Schulze"
	title = title.rstrip();
	return title



def map_point_type( props ):
	tags = { 
		(props.get( "amenity" ) or "").lower(),
		(props.get( "landuse" ) or "").lower(),
		(props.get( "shop"    ) or "").lower(),
		(props.get( "tourism" ) or "").lower()
	}
	
	# TCX kennt nur eine handvoll sinnvoller PointTypes (Food, Water, Danger, First Aid),
	# die auch ein eigenes Icon haben. Der Rest bezieht sich auf Steigungen (Kat. 1-4, Hors)
	
	# Schnittmengen mit tags:
	if   tags & set( TAGS_FOOD ):
		return "Food"
	elif tags & set( TAGS_WATER ):
		return "Water"
	elif tags & set( TAGS_DANGER ):
		return "Danger"
	elif tags & set( TAGS_FIRSTAID ):
		return "First Aid"
	else:
		return "Generic"



def gpx_geojson_to_tcx( gpx_file, poi_file, tcx_file ):
	
	with open( gpx_file, 'r' ) as f:
		gpx = gpxpy.parse( f )
	
	with open( poi_file, 'r' ) as f:
		geojson = json.load( f )
	
	ns  = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
	tcx = ET.Element("{%s}TrainingCenterDatabase" % ns, nsmap={None: ns})
	
	# Instead of <Activities>, use <Courses> for planned routes with CoursePoints
	courses = ET.SubElement( tcx,     "Courses" )
	course  = ET.SubElement( courses, "Course"  )
	ET.SubElement( course, "Name" ).text = "Komoot Route"
	
	# Trackpoints:
	track_elem = ET.SubElement( course, "Track" )
	for track in gpx.tracks:
		for segment in track.segments:
			for point in segment.points:
				tp  = ET.SubElement( track_elem, "Trackpoint" )
				pos = ET.SubElement( tp,         "Position"   )
				ET.SubElement( pos, "LatitudeDegrees"  ).text = str( point.latitude  )
				ET.SubElement( pos, "LongitudeDegrees" ).text = str( point.longitude )
				if point.elevation is not None:
					ET.SubElement( tp, "AltitudeMeters" ).text = str( point.elevation )
	
	# Cue Sheet:
	for feature in geojson.get( "features", [] ):
		if feature.get( "geometry", {} ).get( "type" ) == "Point":
			lon, lat = feature["geometry"]["coordinates"][:2]
			props    = feature.get( "properties", {} )
			
			cp = ET.SubElement( course, "CoursePoint" )
			ET.SubElement( cp, "Name"      ).text = cue_title( props )
			ET.SubElement( cp, "PointType" ).text = map_point_type( props )
			
			pos = ET.SubElement( cp, "Position" )
			ET.SubElement( pos, "LatitudeDegrees"  ).text = str( lat )
			ET.SubElement( pos, "LongitudeDegrees" ).text = str( lon )
			
			# TODO <Notes></Notes> ?
			
			if "description" in props:
				ET.SubElement( cp, "Notes" ).text = props["description"]
	
	
	tree = ET.ElementTree( tcx )
	tree.write( tcx_file, pretty_print = True, xml_declaration = True, encoding = "UTF-8" )



def get_user_config():
	parser = argparse.ArgumentParser(
		description = (
			"Creates a Wahoo-compatible Garmin TCX track file from a GPX and POIs-GeoJSON file.\n"
			"This converter is limited to _planned_ rides from Komoot (does not convert heart rate, cadence etc. data)\n\n"
			"Author: https://github.com/andre-st/wahoo/" 
		),
		epilog          = "License: ?",
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "gpx_file",         help = "load route from the given GPX file path", type = str )
	parser.add_argument( "-p", "--poi-file", help = "load POIs from the given GeoJSON file path (default is your GPX-file path with .geojson extension)", type = str )
	parser.add_argument( "-o", "--tcx-file", help = "save to the given file path (default is your GPX-file path with .tcx extension)", type = str )
	
	args      = parser.parse_args()
	base, ext = os.path.splitext( args.gpx_file )
	
	if args.poi_file is None:
		args.poi_file = base + ".geojson"
	
	if args.tcx_file is None:
		args.tcx_file = base + ".tcx"
	
	return args



def main():
	args = get_user_config()
	gpx_geojson_to_tcx( args.gpx_file, args.poi_file, args.tcx_file )
	print( f"[INFO] Original track + POIs written to: {args.tcx_file}" )


if __name__ == "__main__":
	main()
