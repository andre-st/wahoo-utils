#/bin/bash

# Change to project directory
pushd "$(dirname "$(realpath "$0")")" > /dev/null || exit 1


# Base

mkdir -p routes


# Install dependencies in local project directory:

python -m venv "local"

source "local/bin/activate"

# Indirect deps:
#    shapely <- geopandas
#    pandas  <- geopandas

pip install geopandas gpxpy lxml osmnx geopy pygeohash adbutils

chmod +x *.py *.sh


# Android Debug Bridge:

if [ -d ./local/opt/platform-tools ]
then
	echo "ADB already installed"
else
	zipname=platform-tools-latest-linux.zip
	wget "https://dl.google.com/android/repository/$zipname"
	mkdir -p "local/opt"
	unzip "$zipname" -d "local/opt"  &&  rm "$zipname"
	"./local/opt/platform-tools/adb" version
fi


popd > /dev/null || exit 1


