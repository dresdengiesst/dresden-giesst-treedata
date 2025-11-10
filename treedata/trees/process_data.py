import os
import logging
from math import pi
import yaml
import datetime
from dateutil import parser

from .geo_within import get_district

current_year = int(datetime.datetime.now().date().strftime("%Y"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ROOT_DIR = os.path.abspath(os.curdir)


def read_config():
    with open(f"{ROOT_DIR}/resources/conf.yml", 'r') as stream:
        try:
            conf = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logging.exception(f'Error occurred while reading the conf.yml: {e}')
            raise

    schema_mapping_dict = conf['data-schema']['mapping']
    schema_calculated_dict = conf['data-schema']['calculated']

    return schema_mapping_dict, schema_calculated_dict


def read_genus_mapping():
    with open(f"{ROOT_DIR}/resources/genus.yml", 'r', encoding='utf-8') as stream:
        try:
            conf = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logging.exception(f'Error occurred while reading the genus.yml: {e}')
            raise

    return conf['genus']


genus_mapping = read_genus_mapping()


def lookup_genus(inputs):
    if 'species' in inputs:
        return inputs['species'].split(" ")[0]
    else:
        return None


def lookup_genus_german(inputs):
    if 'species' in inputs:
        genus = lookup_genus(inputs)
        if genus in genus_mapping:
            return genus_mapping[genus]
        else:
            logger.info(f'{genus} not in genus mapping')
            return None
    else:
        return None


def calc_plant_year(inputs):
    if 'age' in inputs:
        try:
            age_str = inputs['age']
            if "keine Angabe" in age_str:
                return None
            else:
                age_int = int(inputs['age'])
                if age_int < 0:
                    # assuming spelling issue with leading dash
                    age_int = -1 * age_int
                if age_int >= 1000:
                    # assuming year instead of age given
                    return age_int
                else:
                    return int(current_year - age_int)
        except:
            logging.exception(f"cannot parse {inputs['age']} as number")
            return None
    else:
        return None


def calc_trunc_circumference(inputs):
    if 'diameter' in inputs:
        try:
            diameter_float = float(inputs['diameter'])
            return round(pi * diameter_float, 2)
        except:
            return None
    else:
        return None


def lookup_district(inputs):
    if 'geometry' in inputs and 'city_shape' in inputs:
        geometry = inputs['geometry']
        return get_district(
            round(geometry.x, 5),
            round(geometry.y, 5),
            inputs['city_shape']
        )
    else:
        return None


def calc_update_date(inputs):
    if 'update_data_str' in inputs:
        try:
            given_date = inputs['update_data_str']
            if isinstance(given_date, str):
                date = parser.parse(given_date)
            elif isinstance(given_date, datetime.date):
                date = given_date
            else:
                return None
            return date.date()
        except:
            return None
    else:
        return None


calc_funs = {
    "lookup_genus": lookup_genus,
    "lookup_genus_german": lookup_genus_german,
    "calc_plant_year": calc_plant_year,
    "calc_trunc_circumference": calc_trunc_circumference,
    "lookup_district": lookup_district,
    "calc_update_date": calc_update_date
}


def transform_new_tree_data(new_trees, attribute_list, schema_mapping_dict, schema_calculated_dict, city_shape):
    transformed_trees = new_trees.rename(columns=schema_mapping_dict)
    logger.info(f'Loaded {len(transformed_trees)} trees')

    # transform gml_id here
    transformed_trees['id'] = transformed_trees['standortnr'].str.split(pat=".").str[1]

    # drop not needed columns based on the columns of the old data
    for column in transformed_trees.columns:
        if column == "geometry":
            continue
        else:
            if column not in attribute_list:
                try:
                    transformed_trees = transformed_trees.drop([column], axis=1)
                except:
                    logger.error(f'{column} not found')

    duplicates_count = len(transformed_trees) - len(transformed_trees.drop_duplicates(subset=['id']))

    # drop duplicate features based on gml_id
    transformed_trees = transformed_trees.drop_duplicates(subset=['id'])

    # replace NA values with 'undefined' and transform data formats to string
    for column in transformed_trees.columns:
        if column != "geometry":
            dtype = transformed_trees[column].dtype
            if str(dtype).startswith('datetime64'):
                transformed_trees[column] = transformed_trees[column].astype(str)
            elif dtype != object or column == 'kronedurch':
                # 'kronedurch' is from type object but is loaded to the db as double precision,
                # this is why we have to make this hack here
                transformed_trees[column] = transformed_trees[column].fillna('99999')
                try:
                    transformed_trees[column] = transformed_trees[column].astype(int).astype(str)
                except:
                    logger.error(f'{column} has type {transformed_trees[column].dtype}')
    transformed_trees = transformed_trees.replace(['99999'], None)
    transformed_trees = transformed_trees.replace('', None)

    transformed_trees['lng'] = transformed_trees.geometry.x.round(5).astype(str)
    transformed_trees['lat'] = transformed_trees.geometry.y.round(5).astype(str)

    for key, value in schema_calculated_dict.items():
        if 'inputs' in value:
            input_fields = value['inputs']
            if 'function' in value:
                calc_fun = value['function']
                if calc_fun in calc_funs:
                    def calculate_fun(row):
                        inputs = {}
                        for input_field in input_fields:
                            if input_field in row:
                                inputs[input_fields[input_field]] = row[input_field]
                                if calc_fun == 'lookup_district':
                                    inputs['city_shape'] = city_shape
                                return calc_funs[calc_fun](inputs)
                            else:
                                logger.info(f'Field {input_field} for calculation of {key} not among known columns')
                                return None
                    transformed_trees[key] = new_trees.apply(lambda row: calculate_fun(row), axis=1)
                else:
                    logger.info(f'Function {calc_fun} for calculation of {key} not among known functions')
            else:
                logger.info(f'No function definition in calculation of {key}')
        else:
            logger.info(f'No inputs definition in calculation of {key}')

    logger.info("ℹ️ " + str(duplicates_count) + " trees with a duplicated id were dropped.")
    return transformed_trees


