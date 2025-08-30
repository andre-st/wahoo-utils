# Wahoo Elemnt Bolt v2 Utils

![Maintenance](https://img.shields.io/maintenance/yes/2025.svg)


## Disclaimer

1. The programs and information provided here are not official Wahoo products; this is a private, non-commercial project.
2. Use at your own risk: It may void your warranty, damage your device, or cause unexpected issues.
3. The programs have not been tested in all environments and are not specifically optimized or fault-tolerant.


## Auto-generated Points of Interest with gpx2poi & poi2db

![Automated POIs on a Wahoo Bolt bike computer](poi2db.jpg)  
(my Bolt with a rubber protective cover)

A distance or bikepacking cyclist could miss nearby food and water if POIs aren’t marked on their map.

- Finding POIs within a 100-meter `--poi-radius-deg` along the route:  
	OpenStreetMap servers can be queried for features within a geographic polygon using the Overpass API.
	`Gpx2poi` constructs a simplified polygon (a buffered line) from all route points in a GPX file downloaded from Komoot or similar services.
	It retrieves hundreds of features within this polygon and writes them to `your_route.geojson`. 
- Getting POIs onto the Bolt:  
	`Poi2db` adds these features as POIs to the Bolt’s "Save my location" table on the device.
	The SQLite database file is accessible via Android Debug Bridge (ADB) (credit: [AndroidAndyUK](https://www.youtube.com/watch?v=Sl--gcJ95XM)).
	Poi2db always recreates the entire auto-POIs list from scratch using a list of GeoJSON files.
	The program parameter `--delete` removes all auto-POIs without adding new ones. 
	Manual POIs are not affected.
- Pros:
	- POI generation and updating the Bolt takes only a few seconds (tested on 60 km tours) and uses very little disk space.
	- no additional POI-capable device is required
- Cons / Known issues:
	- the Bolt uses a single heart icon for all POI types, 
		so different types aren’t visually distinguished. 
		Setting poiType to 1 instead of 0 in the database has no effect (Reversing the Bolt app might reveal why.)
	- currently, it's better to restrict to either `--poi-types=food,water` or `--poi-types=camp` &ndash; not both &ndash; 
		so the heart icon meaning is predictable
	- extra step required: when updating routes in Komoot or similar, you must copy them to this project and rebuild the POI list
	- no auto-POIs available when detouring
- Requires:
	- Linux
	- Python 3 (with pip)
	- USB data cable connecting Bolt
	- `setup.sh` downloads all dependencies  (ADB, python-libs, ...) to the project's subdirectory `local`, so your system stays clean after deletion
- Other approaches:
	- adding POIs manually via smartphone companion app = pain
	- **self generated maps** with POI-symbols = best approach but nasty setup and 
		regular generation requires significant time and disk space.
		Additionally, as of September 2025, it appears to be broken (if I’m not mistaken).
		- https://www.heise.de/select/ct/2022/26/2230710050673252243
		- https://github.com/yokuha/Wahoo-maps
		- https://www.rennrad-news.de/forum/threads/aktuelles-kartenmaterial-f%C3%BCr-wahoo-elemnt-bolt-roam-elemnt-selbst-generieren.175315/
	- custom CUE hints in FIT or TCX (not GPX) files will give a text warning when approaching the point + water tap icon  
		- I can NEITHER reproduce that with FIT nor TCX on my Bolt (in non-riding route-map overview mode)
		- I read that the appearance of icons is limited to a specific short distance from the route (poi2db isn't limited)
		- RwGPS premium feature? $$$
		- ```xml
			<CoursePoint> 
				<Name>Water</Name> 
				<Time>2023-10-19T17:13:09Z</Time> 
				<Position> 
					<LatitudeDegrees>x.xxxx</LatitudeDegrees> 
					<LongitudeDegrees>y.yyyy</LongitudeDegrees> 
				</Position> 
				<PointType>Water</PointType>   <!-- or: Food, Danger -->
				<Notes>Water!</Notes> 
			</CoursePoint>
			```
	- navigate to POIs with your smartphone when hungry/thirsty



## Wahoo Basics

- Bolt runs an old Android operating system which is accessible via USB-Cable and the _Android Debug Bridge_ (ADB) tool
- consider [WebADB](https://app.webadb.com) via Chrome browser (using WebUSB) when unable to install or run ADB for some reason 
	(though some security/privacy risk)
- Bolt authorizes ADB in debug mode:
	1. power up without USB-Cable plugged in, 
	2. press POWER+UP+DOWN simultan. (1 or 2 times)
	3. plug in cable
	4. check with `adb devices`
- Bolt supports file formats: 
	- FIT (newer Garmin binary with smaller filesize), annoyingly requires Garmin FIT SDK
	- [TCX](https://en.wikipedia.org/wiki/Training_Center_XML) (older easy Garmin plaintext XML)
	- GPX (easy plaintext XML)



## See Also

- my stared cycling tools on GitHub: https://github.com/stars/andre-st/lists/cycling
- screen recording on Wahoo devices: https://www.youtube.com/watch?v=dSMxnPvunco


