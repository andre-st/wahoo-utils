# Making the Wahoo ELEMNT Bolt v2 more useful


## Disclaimer

1. Use this project at your own risk.
	Following these instructions may damage your device or cause unexpected issues.
	Do **not** blindly follow instructions from the internet without understanding them — including this one.  
	You are solely responsible for what you do.
2. The programs here are all still in their early stages, 
	fulfill my purpose (playground), 
	but are not necessarily comfortable for everyone 
	or tested everywhere, particularly optimized or fault-tolerant, 
	or translated into English at all points.


## Basics

- Bolt runs an old Android operating system and is accessible via ADB over USB cable
- there is app.webadb.com via Chrome and WebUSB when you are unable to install adb for some reason (some securtiy/privacy risk though)
- Bolt authorizes ADB in debug mode:
	1. power up without USB-Cable plugged in, 
	2. press POWER+UP+DOWN simultan.
	3. white Bolt LED flashes for a second if successfully
	4. plug in cable
	5. I had to try this 20+ times until this "official" method finally worked; 
		I also pressed UP+DOWN during Bolt's "warm up" phase when it worked



## Point of Interests (POI)

### What's there?

- native function on the device: "Save my location" = no manual coordinates
- adding POIs manually via smartphone companion app = pain
- self generated maps with POI-symbols = best approach but nasty setup and regular (re-)generation needs lot of time
	- https://www.heise.de/select/ct/2022/26/2230710050673252243
	- https://github.com/yokuha/Wahoo-maps
- custom CUE hints in TCX (not GPX) files will give a text warning when approaching the point + water tap icon
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
- replace with a more expensive Garmin device
- adding POIs manually by editing the BoltApp database via ADB and a SQLite client
	- https://www.youtube.com/watch?v=Sl--gcJ95XM
	- **we will try this approach but automate finding POIs along our route**



### Tools in this repo

| Filename     | Input                                             | Output             | Comments
|--------------|---------------------------------------------------|--------------------|-------------------------------------
| setup.sh     | -                                                 | /myenv             | installs deps into project dir, so nothing left on your sys after deletion
| gpx2poi.py   | my\_route.gpx file, e.g. from Komoot              | my\_route.json     | collects food/drinking water/toilets/shelter POIs via OpenStreetMap within 100 meter radius along the route
| poi2kml.py   | my\_route.gpx,<br>my\_route.json from gpx2poi.py  | my\_route.kml      | I import the KML-file to Google My Maps to check results, it includes the original route plus POIs alongside
| poi2cue.py   | TODO                                              | my\_route.tcx      | TODO



## Screen Recording

- https://www.youtube.com/watch?v=dSMxnPvunco



