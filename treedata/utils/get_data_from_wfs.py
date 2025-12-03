import os
import ssl
import logging
import geopandas as gpd
from owslib.wfs import WebFeatureService
from requests import Request, get

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def get_wfs_request_url(wfs_url):
    wfs = WebFeatureService(url=wfs_url)
    layer = f"cls:{list(wfs.contents)[-1].split(':')[-1]}"
    logger.info(f"Found layer {layer}")
    params = dict(service='WFS', version="2.0.0", request='GetFeature', typeNames=layer
                  # , outputFormat='text/xml; subtype="gml/3.2.1"'
                  )
    return Request('GET', wfs_url, params=params).prepare().url


def download_wfs_to_xml(wfs_url, source_encoding, outfile_path):
    logger.info(f"Request WFS from {wfs_url}")
    r = get(wfs_url)
    with open(f"{outfile_path}.xml", 'w', encoding=source_encoding) as fd:
        fd.write(r.text)


def convert_xml_to_geojson(infile_path, source_encoding, outfile_path):
    logger.info(f'Load XML {infile_path}.xml')
    data = gpd.read_file(f"{infile_path}.xml", encoding='utf-8', crs_wkt='2100')
    store_as_geojson(data, outfile_path)


def store_as_geojson(data, outfile_name):
    geojson_str = data.to_json(to_wgs84=True)
    with open(f"{outfile_name}.geojson", 'w', encoding='utf-8') as fd:
        fd.write(geojson_str)
    logger.info(f"WFS was written to file {outfile_name}.geojson")


def read_geojson(infile_name):
    return gpd.read_file(infile_name, encoding='utf-8') # (..., rows=50) for testing
