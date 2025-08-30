#/bin/bash


# Stop script on errors:
set -e


# Check environment:
if ! command -v pip >/dev/null 2>&1; then
	echo "[ERROR] Missing 'pip' on your system. For Ubuntu/Debian run: sudo apt install python3-pip" >&2
	exit 1
fi


# Change to project directory:
pushd "$(dirname "$(realpath "$0")")" > /dev/null || exit 1


# Base:
mkdir -p routes
chmod u+x *.sh *.py


# Install dependencies in local project directory:
python -m venv "local"
source "local/bin/activate"
# Indirect deps:
#    shapely <- geopandas
#    pandas  <- geopandas
pip install geopandas gpxpy lxml osmnx geopy pygeohash adbutils


# Android Debug Bridge:
if [ -d ./local/opt/platform-tools ]
then
	echo "[INFO] ADB already installed"
else
	zipname=platform-tools-latest-linux.zip
	wget "https://dl.google.com/android/repository/$zipname"
	mkdir -p "local/opt"
	unzip "$zipname" -d "local/opt"  &&  rm "$zipname"
	"./local/opt/platform-tools/adb" version
fi


popd > /dev/null || exit 1


