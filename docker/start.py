#!/usr/bin/env python

from os import listdir, execvp
from os import environ
from os.path import isdir, join
import argparse

from ukbrest.config import logger, GENOTYPE_PATH_ENV, PHENOTYPE_PATH, PHENOTYPE_CSV_ENV, DB_URI_ENV


parser = argparse.ArgumentParser()
parser.add_argument('--start', dest='start', action='store_true', required=False, help='Specifies whether the HTTP server should be started.', default=True)
parser.add_argument('--load', dest='load', action='store_true', required=False, help='Specifies whether data should be loaded into the DB.', default=False)

args, unknown = parser.parse_known_args()


def _setup_genotype_path():
    genotype_path = environ.get(GENOTYPE_PATH_ENV, None)

    if not isdir(genotype_path):
        logger.warning('The genotype directory does not exist. You have to mount it using '
                       'the option "-v hostDir:{}" of "docker run"'.format(genotype_path))
        return

    bgen_files = [f for f in listdir(genotype_path) if f.lower().endswith('.bgen')]
    if len(bgen_files) == 0:
        logger.warning('No .bgen files were found in the genotype directory')

    bgi_files = [f for f in listdir(genotype_path) if f.lower().endswith('.bgi')]
    if len(bgi_files) == 0:
        logger.warning('No .bgi files were found in the genotype directory')


def _setup_phenotype_path():
    phenotype_path = environ.get(PHENOTYPE_PATH, None)

    if not isdir(phenotype_path):
        parser.error('The phenotype directory does not exist. You have to mount it using '
                     'the option "-v hostDir:{}" of "docker run"'.format(phenotype_path))

    # check whether there is at least one and only one csv file
    phenotype_csv_file = sorted([f for f in listdir(phenotype_path) if f.lower().endswith('.csv')])

    if len(phenotype_csv_file) == 0:
        parser.error('No .csv files were found in the phenotype directory')

    environ[PHENOTYPE_CSV_ENV] = ';'.join([join(phenotype_path, csv_file) for csv_file in phenotype_csv_file])


def _setup_db_uri():
    db_uri = environ.get(DB_URI_ENV, None)

    if db_uri is None:
        parser.error('No DB URI was specified. You have to set it using the environment variable UKBREST_DB_URI. For '
                     'example, for PostgreSQL, the format is: postgresql://user:pass@host:port/dbname')

if args.load:
    _setup_phenotype_path()
    _setup_db_uri()

    commands = ('python', ['python', '/opt/ukbrest/load_data.py'])

elif args.start:
    _setup_genotype_path()
    _setup_db_uri()
    # TODO: check if data was loaded into PostgreSQL

    commands = ('gunicorn', ['gunicorn', 'ukbrest.wsgi:app'])

execvp(*commands)
