# Musterstadt Gießt – Tree Data

Please review the content of the `README.md` and adjust it to the project.

## Prerequisites
 * [Python 3.11](https://www.python.org/downloads/)

## Install & Development

### Windows
#### QGIS
 * https://qgis.org/en/site/forusers/download.html
 * this will install also `OSGeo4W Shell` where gdal is available (check `gdalinfo --version`)
 
### Local PostgreSQL
 * Download latest (15.3) and install: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads 
 * Download latest PostGIS and install in before installed Postgres folder: https://download.osgeo.org/postgis/windows/pg15/ 
 * Connect to database and execute:
```
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```
 * alternatives 
   * with Docker: `docker run --name treedata-postgis -e POSTGRES_PASSWORD=treedata -d postgis/postgis`
   * with Supabase (see below)
 
#### Miniconda
 * https://docs.conda.io/en/latest/miniconda.html#windows-installers
 * Open `Anaconda prompt (miniconda3)` from Quick start

### Linux
#### Miniconda

```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh
rm ./Miniconda3-latest-Linux-x86_64.sh
```

### All
#### Miniconda
 * change to folder containing this locally checked out Git repo

```
conda update conda
conda create -n treedata
conda activate treedata
conda install pip
pip install -r requirements.txt
```

* install GDAL
```
conda install -c conda-forge gdal
```

* support for gdalwarp
```
conda install -c conda-forge krb5
pip install gssapi
gdalwarp -v
```

### Troubleshooting
 * error when executing `gdalwarp -v`: `gdalwarp: error while loading shared libraries: libpoppler.so.126: cannot open shared object file: No such file or directory`
   * **solution**: `conda install -c conda-forge gdal libgdal tiledb=2.2`
 * error while converting WFS XML to GeoJSON (e.g. city shape): `fiona._err.CPLE_AppDefinedError: PROJ: internal_proj_create: no database context specified`
   * **solution**: remove environments via `unset PROJ_LIB` and `unset GDAL_DATA` as they conflict 

### PyCharm
 * Download Community Edition: https://www.jetbrains.com/pycharm/
 * https://www.jetbrains.com/help/pycharm/conda-support-creating-conda-virtual-environment.html#create-a-conda-environment
   * select existing environment `treedata`
 * open new terminal to see activated conda environment `treedata`

### Next steps
 * copy `resources/sample.env` to `resources/.env`
   * set your (locally) PostgreSQL connection data

### Local Supabase
 * follow https://github.com/greenbluelab/musterstadt-giesst-api#supabase-local
   (resp. https://supabase.com/docs/guides/self-hosting/docker for general approach) 
 * then adapt ./resources/.env to match supabase/docker/.env settings for Supabase PostgreSQL
 * in http://localhost:54323/project/default/database/extensions extension POSTGIS should be 
   already enabled, when used the general approach: enable extensions POSTGIS in 
   http://localhost:3000/project/default/database/extensions 
   (see also https://supabase.com/docs/guides/database/extensions/postgis)
 * the initial tables and indexes should be already created within musterstadt-giesst-api

resources/.env
```
PG_SERVER=localhost
PG_PORT=54322
PG_USER=postgres
PG_PASS=postgres
PG_DB=postgres
```

 * run `supabase status` in `musterstadt-giesst-api` and add the values 

```
SUPABASE_URL=<API URL, e.g. http://localhost:54321>
SUPABASE_BUCKET_NAME=<create new public bucket under http://localhost:54323/project/default/storage/buckets and name it e.g. "radolan_data" and use this name here>
SUPABASE_SERVICE_ROLE_KEY=<service role key)
```

and 

```
MAPBOXUSERNAME=<username as displayed in https://account.mapbox.com/ under "Account" on the right upper side>
MAPBOXTOKEN=<create secret access token as described here https://docs.mapbox.com/help/tutorials/upload-curl/#getting-started>
MAPBOXTILESET=<create new tileset under https://studio.mapbox.com/tilesets/ and the copy tile set id and use it here>
```

## Demo
 * Download city shape WFS file to geojson: `python ./treedata/main.py city_shape`
   * command with all options: `python ./treedata/main.py city_shape --wfs-url <WFS-URL> --source-encoding iso-8859-1 --xml-file-name wfs --geojson-file-name city_shape --skip-download-wfs-xml --skip-convert-to-geojson`
 * Download trees WFS file to geojson: `python ./treedata/main.py trees`
   * command with all options: `python ./treedata/main.py trees --wfs-url <WFS-URL> --source-encoding iso-8859-1 --xml-file-name wfs --geojson-file-name trees --skip-download-wfs-xml --skip-convert-to-geojson`
 * Process trees: `python ./treedata/main.py trees_process`
   * process specific trees geojson (from resources/trees): `python ./treedata/main.py trees_process --trees-geojson-file-name s_wfs_baumbestand_2023-07-23`
   * command with all options: `python ./treedata/main.py trees_process --city-shape-geojson-file-name city_shape --trees-geojson-file-name trees --geojson-file-name trees-transformed --database-table-name trees_tmp --skip-transform --skip-store-as-geojson --skip-upload-to-db`
   * store as file only: `python ./treedata/main.py trees_process --city-shape-geojson-file-name city_shape --skip-upload-to-db --trees-geojson-file-name s_wfs_baumbestand_2023-07-15`
   * store in db only: `python ./treedata/main.py trees_process --skip-transform --skip-store-as-geojson --trees-geojson-file-name trees_transformed --database-table-name trees_tmp`
 * skip remaining??
 * Process weather data (under Windows run these commands in Anaconda Prompt (miniconda3) console): `python ./treedata/main.py weather`
   * command with all options: `python ./treedata/main.py weather --start-days-offset 2 --end-days-offset 1 --city-shape-geojson-file-name city_shape-small --city-shape-buffer-file-name city_shape-small-buffered --city-shape-buffer 2000 --city-shape-simplify 1000  --skip-buffer-city-shape --skip-download-weather-data --skip-polygonize-weather-data --skip-join-radolan-data --skip-upload-radolan-data --skip-update-tree-radolan-days --skip-upload-geojsons-to-s3 --skip-upload-csvs-to-s3 --skip-upload-csvs-to-mapbox`
   * only join radolan shp files: `python ./treedata/main.py weather --skip-download-weather-data --skip-unzip-weather-data --skip-buffer-city-shape --skip-polygonize-weather-data`
   * only upload radolan geojson file: `python ./treedata/main.py weather --skip-download-weather-data --skip-unzip-weather-data --skip-buffer-city-shape --skip-polygonize-weather-data --skip-join-radolan-data`