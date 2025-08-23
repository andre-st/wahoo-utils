#/bin/bash

# Change to project directory
pushd "$(dirname "$(realpath "$0")")" > /dev/null || exit 1

python -m venv myenv

source myenv/bin/activate

pip install gpxpy geopandas shapely osmnx simplekml tqdm

chmod +x *.py *.sh

popd > /dev/null || exit 1


