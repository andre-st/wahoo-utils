# Wahoo Elemnt Bolt v2 Utils

![Maintenance](https://img.shields.io/maintenance/yes/2025.svg)


## Disclaimer

1. The programs and information provided here are not official Wahoo products; this is a private, non-commercial project.
2. Use at your own risk: It may void your warranty, damage your device, or cause unexpected issues.
3. The programs have not been tested in all environments and are not specifically fault-tolerant.


## Auto-generated Points of Interest with gpx2poi & poi2db

![Automated POIs on a Wahoo Bolt bike computer](poi2db.jpg)  
_Fig: my Bolt (w/ rubber protective cover): low zoom level of the entire island of Bornholm (588 km²) plus street-level view as if riding_

A distance or bikepacking cyclist could miss nearby food and water if POIs aren’t marked on their map.

- Finding `--poi-types=water,food` within a 500-meter `--poi-radius` along your route:  
	OpenStreetMap servers can be queried for features within a geographic polygon using the Overpass API.
	`Gpx2poi` constructs a simplified polygon (a buffered line) from all route points in a GPX file downloaded from Komoot or similar services.
	It retrieves hundreds of features within this polygon and writes them to `your_route.geojson`. 
	I test results with `poi2tcx` and [a TCX viewer](https://www.gpsvisualizer.com/) 
- Getting POIs onto the Bolt:  
	`Poi2db` adds these features as POIs to the Bolt’s "Save my location" table on the device.
	The SQLite database file is accessible via Android Debug Bridge (credit: [AndroidAndyUK](https://www.youtube.com/watch?v=Sl--gcJ95XM)).  
	Manual POIs are not affected.
- Pros:
	- POI generation and updating the Bolt takes only a few seconds and uses very little disk space  
		(tested in real life with several 60 km tours; 
		usually recommended to split long distances for smoother re-routing on a bike computer)
	- POI visibility is independent of the zoom level
	- no additional POI-capable device is required
	- freely definable POI radius in contrast to navigation cues
	- easy installation (probably), zero configuration and hardly any RTFM
- Cons / Known issues:
	- the Bolt uses &hearts; for all POI types, 
		so different types aren’t visually distinguished. 
		(_poiType_ in the database seems either 0=SAVED_LOCATION or 1=PREVIOUS_SEARCH or n>1 UNKNOWN_\$n, that is app logic / not problem domain; 
			too, the resource directory _with the &hearts; icon_ 'map_poi_\{color,light\}.webp' does not contain any other POI icon)
	- currently, it's better to restrict to either `--poi-types=food,water` or `--poi-types=camp` for example &ndash; not both &ndash; 
		so the meaning of &hearts; is more predictable (still you cannot tell a restaurant apart from a fuel station); 
		I've excluded bars/pubs from `water` because of bike safety, you might want to re-add it.
	- extra step required: when updating routes in Komoot or similar, 
		you must [copy them](https://github.com/pieterclaerhout/export-komoot) 
		to this project and rebuild the POI list
	- no auto-POIs available when detouring (outside the specified POI radius)
	- at low zoom levels, too many POIs can clutter the map, though this isn’t an issue at street level. 
		Not sure if Bolt allows you to hide all POIs.
	- manual POIs added before auto-generation get buried under hundreds of auto-POIs. 
		However, manual ‘save-my-location’ POIs added during rides 
		(e.g., ‘bring me back to this tent pitch after checking out the city for food’) 
		appear at the top and are easy to find.
- Installation:
	```sh
		$ ./setup.sh     # installs ADB, python-libs etc to the project's subdir 'local', so your system stays clean
		$                # requires Linux, Python 3 with pip
		$ ./gpx2poi.py --help
		$ ./poi2db.py  --help
		$                # 1. download _selected_ GPX files to "routes"-directory
		$                # 2. enable Bolt's debug mode and connect USB cable
		$ ./gpx2poi.py routes/*.gpx      # Saves POIs for all GPX tracks to local geojson-files
		$ ./poi2db.py  routes/*.geojson  # Recreates POI-list on the Bolt
	```
- Other approaches:
	- adding POIs manually via smartphone companion app = pain, only works for a few selected points
	- **self generated maps** with POI-symbols = best approach but nasty setup without a container and 
		regular generation requires some time and disk space (Germany w/o neighb.: 2 hours, 13 GB)
		- https://github.com/treee111/wahooMapsCreator
		- https://github.com/vti/wahooMapsCreator-docker (!)
		- https://github.com/vti/elemntary   (user friendly maps upload)
		- https://github.com/yokuha/Wahoo-maps
		- https://www.rennrad-news.de/forum/threads/aktuelles-kartenmaterial-f%C3%BCr-wahoo-elemnt-bolt-roam-elemnt-selbst-generieren.175315/
	- custom navigation cues in FIT, TCX (`<CursePoint>`), GPX (`<wpt>` waypoints) files may give a text warning when approaching the point + water tap icon  
		- I could not detect any icon with FIT or TCX on my Bolt in non-riding route-map overview mode, GPX not tested iirc
			(TCX food and water icons showed up in GPSVisualizer)
		- Q: Are icons just visible on the Bolt when actually riding in proximity/small radius? (poi2db isn't limited)
		- online-tool to enrich GPX track with waypoints (tested with Garmin): https://waypoints.sippsolutions.de/  
		- RwGPS premium feature? $$$
	- navigate to POIs with your smartphone when hungry/thirsty = increased battery usage; 
		needs mounting options on the handlebar; increased risk of damage



## Wahoo Basics

- Bolt runs an old Android operating system which is accessible via USB-Cable and the _Android Debug Bridge_ (ADB) tool
- consider [WebADB](https://app.webadb.com) via Chrome browser (using WebUSB) when unable to install or run ADB for some reason 
	(though some security/privacy risk)
- Bolt authorizes ADB in debug mode:
	1. power up without USB-Cable plugged in, 
	2. press POWER+UP+DOWN simultan. (2 times)
	3. plug in cable
	4. check with `./local/opt/platform-tools/adb devices`  (remove cable and repeat 2. if 'unauthorized')
- Bolt supports file formats: 
	- FIT (newer Garmin binary with smaller filesize), annoyingly requires Garmin FIT SDK
	- TCX (older easy Garmin plaintext XML)
	- GPX (easy plaintext XML)



## See Also

- my stared cycling tools on GitHub: https://github.com/stars/andre-st/lists/cycling
- screen recording on Wahoo devices: https://www.youtube.com/watch?v=dSMxnPvunco


