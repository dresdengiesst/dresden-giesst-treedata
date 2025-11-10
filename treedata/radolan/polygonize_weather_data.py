import logging
import os
import platform
import subprocess
from datetime import datetime

ROOT_DIR = os.path.abspath(os.curdir)
path = f"{ROOT_DIR}/resources/radolan/"
buffer_file_folder = f"{ROOT_DIR}/resources/city_shape"


def command_line_start():
    if platform.system() == 'Windows':
        return ['cmd', '/c']
    else:
        return []


def polygonize_asc_file(buffer_file_name, input_file, output_file, file_name):
    buffer_file = f"{buffer_file_folder}/{buffer_file_name}.shp"

    # filter data
    cmdline = command_line_start() + [
        'gdalwarp', input_file, output_file,
        "-s_srs", '+proj=stere +lon_0=10.0 +lat_0=90.0 +lat_ts=60.0 +a=6370040 +b=6370040 +units=m',
        "-t_srs", '+proj=stere +lon_0=10.0 +lat_0=90.0 +lat_ts=60.0 +a=6370040 +b=6370040 +units=m',
        "-r", "near", "-of", "GTiff", "-cutline", buffer_file
    ]
    logging.info("executing " + ' '.join(cmdline))
    returncode_gdalwarp = subprocess.call(cmdline)
    if returncode_gdalwarp != 0:
        raise Exception(f"gdalwarp failed for {buffer_file}")

    # polygonize data
    shape_file = path + f"{file_name}.shp"

    # remove cmd /c when not Windows
    cmdline = command_line_start() + [
        'gdal_polygonize.py', output_file, "-f",
        "ESRI Shapefile", shape_file, file_name, "MYFLD"
    ]
    logging.info("executing " + ' '.join(cmdline))
    # gdal_polygonize.py D:/git/gbl/musterstadt-giesst-treedata/weather_data/data_files/temp.tif -f "ESRI Shapefile" D:/git/gbl/musterstadt-giesst-treedata/weather_data/data_files/temp.shp temp MYFLD
    returncode_polygonize = subprocess.call(cmdline)
    if returncode_polygonize != 0:
        raise Exception(f"gdal_polygonize failed for {shape_file}")



def polygonize_weather_data(buffer_file_name):
    # collecting all the files that need importing in one list
    filelist = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        for dirname in dirnames:
            dpath = path + dirname
            for (ddirpath, ddirnames, ffilenames) in os.walk(dpath):
                for ffilename in ffilenames:
                    if ".asc" in ffilename:
                        filelist.append(dpath + "/" + ffilename)

    last_received = datetime.strptime("1970-01-01 01:00:00", '%Y-%m-%d %H:%M:%S')
    for counter, file in enumerate(filelist):
        input_file = file

        file_split = file.split("/")
        file_name = file_split[len(file_split) - 1].split('.')[0]
        date_time_obj = datetime.strptime(file_name, 'RW_%Y%m%d-%H%M')
        if date_time_obj > last_received:
            last_received = date_time_obj
        logging.info("Processing: {} / {}".format(len(filelist), counter + 1))

        output_file = path + f"{file_name}.tif"

        # for some reason the python gdal bindings are ****.
        # after hours of trying to get this to work in pure python,
        # this has proven to be more reliable and efficient. sorry.

        polygonize_asc_file(buffer_file_name, input_file, output_file, file_name)

    return filelist, last_received
