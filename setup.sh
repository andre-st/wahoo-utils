#/bin/bash

# Change to project directory
pushd "$(dirname "$(realpath "$0")")" > /dev/null || exit 1

python -m venv myenv

source myenv/bin/activate

# shapely <- geopandas
# pandas  <- geopandas
pip install geopandas gpxpy lxml osmnx tqdm 

chmod +x *.py *.sh

popd > /dev/null || exit 1


