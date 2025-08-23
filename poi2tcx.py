#!/usr/bin/env ./myenv/bin/python

# Minimal GPX->TCX converter for _planned_ rides from Komoot (does not convert heart rate, cadence etc. data)
# Adds POIs as CUEs
#
# TCX-Schema: https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd



import gpxpy
import json
from lxml import etree as ET


GPX_FILE = "my_route.gpx"
POI_FILE = "my_route.geojson"
TCX_FILE = "my_route.tcx"


FOOD_AMENITIES     = { "restaurant", "cafe", "bar", "biergarten", "fast_food", "pub", "ice_cream", "food_court", "bbq", "marketplace" }
WATER_AMENITIES    = { "drinking_water", "toilets", "water_point" }
DANGER_AMENITIES   = {}
FIRSTAID_AMENITIES = {}



def cue_title( props ):
	name    = props.get( "name"    ) or ""
	amenity = props.get( "amenity" ) or "POI"
	amenity = amenity.replace( '_', ' ' )       # "fast_food" -> "fast food"
	amenity = amenity[0].upper() + amenity[1:]  # "toilets"   -> "Toilets" 
	title   = name if name.startswith( amenity ) else amenity + " " + name;  # "Cafe Cafe Schulze"
	title   = title.rstrip();
	return title



def map_point_type( props ):
	amenity = (props.get( "amenity" ) or "").lower()
	landuse = (props.get( "landuse" ) or "").lower()
	if amenity in FOOD_AMENITIES:
		return "Food"
	elif amenity in WATER_AMENITIES or landuse == "cemetery":
		return "Water"
	elif amenity in DANGER_AMENITIES:
		return "Danger"
	elif amenity in FIRSTAID_AMENITIES:
		return "First Aid"
	else:
		return "Generic"



def gpx_geojson_to_tcx( gpx_file, poi_file, tcx_file ):
	
	with open( gpx_file, 'r' ) as f:
		gpx = gpxpy.parse(f)
	
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



gpx_geojson_to_tcx( GPX_FILE, POI_FILE, TCX_FILE )



