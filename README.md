# Making the Wahoo ELEMNT Bolt v2 more useful


## Disclaimer

1. Programs and information offered here are not official from Wahoo, but purely a private project
2. Use this project at your own risk.
	Following these instructions may damage your device or cause unexpected issues.
	Do **not** blindly follow instructions from the internet without understanding them — including this one.  
	You are solely responsible for what you do.
3. Programs here are all still in their early stages, 
	not tested everywhere, not particularly optimized or fault-tolerant, 
	not translated into English at all points.



## Overview

- [Basics](#basics)
- [Points of Interest (POI)](#points-of-interest-poi)
- [Screen Recording](#screen-recording)



## Basics

- Bolt runs an old Android operating system which is accessible via USB-Cable and the Android Debug Bridge (ADB) tool
- there is [WebADB](https://app.webadb.com) via Chrome browser (using WebUSB) when you are unable to install ADB for some reason 
	(though some security/privacy risk)
- Bolt authorizes ADB in debug mode:
	1. power up without USB-Cable plugged in, 
	2. press POWER+UP+DOWN simultan.
	3. white Bolt LED flashes for a second if successfully
	4. plug in cable
	5. I had to try this 20+ times until this "official" method finally worked; 
		I also pressed UP+DOWN during Bolt's "warm up" phase when it worked
- Bolt supports file formats: FIT (newer Garmin binary with smaller filesize), TCX (older Garmin plaintext) and GPX (plaintext)



## Points of Interest (POI)

### Motivation

- distance cycling / bikepacking
- requires food, drinking water (cemetery), toilets, shelter (= POI types) along the route
- cyclist might miss nearby POIs, either planned or non-planned
- Bolt v2 POI support is very basic


### What is possible with the Bolt v2?

- native function on the device: "Save my location" = no manual coordinates
- adding POIs manually via smartphone companion app = pain
- adding POIs manually by editing the BoltApp database via ADB and a SQLite client = no POI types (heart-icon only) and might not scale well
	- DB-file: `/data/data/com.wahoofitness.bolt/databases/BoltApp.sqlite`
	- DB-table: `CloudPoiDao`
	- https://www.youtube.com/watch?v=Sl--gcJ95XM
- self generated maps with POI-symbols = best approach but nasty setup and regular generation needs lot of time
	- https://www.heise.de/select/ct/2022/26/2230710050673252243
	- https://github.com/yokuha/Wahoo-maps
- custom CUE hints in FIT or [TCX](https://en.wikipedia.org/wiki/Training_Center_XML) (not GPX) files will give a text warning when approaching the point + water tap icon
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


### Manually adding POIs is cumbersome

- here, I try CUEs and BoltApp DB editing but automate finding POIs along our route via OpenStreetMap (OSM)
- CUEs are aligned and contained with track but uploading new or changed tracks to the bike computer is more complicated now
	1. export from track editor, e.g. Komoot
	2. create new track by running tools in this repo against your track
	3. upload new track to smartphone
	4. import new track via companion app
	5. sync Bolt and app
	6. avoid confusing new and old tracks if autosynced with Komoot
- DB is independent of tracks (you can sync tracks with Komoot) or - negatively - not aligned with changed tracks, and requires separate cleaning/updating
	- good for covering a wider region (shelters?) but not a track



### Tools in this repo

| Filename     | Input                                             | Output             | Comments
|--------------|---------------------------------------------------|--------------------|-------------------------------------
| setup.sh     | -                                                 | /myenv             | installs deps into project-dir, so nothing left on your system after deletion
| gpx2poi.py   | my\_route.gpx file, e.g. from Komoot              | my\_route.json     | collects selected POIs via OpenStreetMap within 100 meter radius along the given route
| poi2kml.py   | my\_route.gpx,<br>my\_route.json from gpx2poi.py  | my\_route.kml      | check results by importing KML-file to Google MyMaps; includes original route plus POIs alongside
| poi2cue.py   | TODO                                              | my\_route.tcx      | TODO

  
  


## Screen Recording

- https://www.youtube.com/watch?v=dSMxnPvunco



