import os
import unittest
import tempfile

import numpy as np
import pandas as pd
from nose.tools import nottest
from sqlalchemy import create_engine

from tests.settings import POSTGRESQL_ENGINE, SQLITE_ENGINE
from tests.utils import get_repository_path
from ukbrest.common.pheno2sql import Pheno2SQL


class Pheno2SQLTest(unittest.TestCase):
    def setUp(self):
        # wipe postgresql tables
        sql_st = """
        select 'drop table if exists "' || tablename || '" cascade;' from pg_tables where schemaname = 'public';
        """
        db_engine = create_engine(POSTGRESQL_ENGINE)
        tables = pd.read_sql(sql_st, db_engine)

        with db_engine.connect() as con:
            for idx, drop_table_st in tables.iterrows():
                con.execute(drop_table_st.iloc[0])

    def test_sqlite_default_values(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'sqlite'

        ## Check table exists
        tmp = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert not tmp.empty

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0","c31_0_0","c34_0_0","c46_0_0","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[1, 'c31_0_0'] == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert tmp.loc[1, 'c48_0_0'] == '2011-08-14'
        assert tmp.loc[2, 'c21_0_0'] == 'Option number 2'
        assert pd.isnull(tmp.loc[2, 'c21_1_0'])
        assert tmp.loc[2, 'c21_2_0'] == 'No'
        assert tmp.loc[2, 'c31_0_0'] == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        assert int(tmp.loc[2, 'c46_0_0']) == -2
        assert tmp.loc[2, 'c47_0_0'].round(5) == -0.55461
        assert tmp.loc[2, 'c48_0_0'] == '2010-03-29'

    def test_postgresql_default_values(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check table exists
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0","c31_0_0","c34_0_0","c46_0_0","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[1, 'c31_0_0'].strftime('%Y-%m-%d') == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert tmp.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
        assert tmp.loc[2, 'c21_0_0'] == 'Option number 2'
        assert pd.isnull(tmp.loc[2, 'c21_1_0'])
        assert tmp.loc[2, 'c21_2_0'] == 'No'
        assert tmp.loc[2, 'c31_0_0'].strftime('%Y-%m-%d') == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        assert int(tmp.loc[2, 'c46_0_0']) == -2
        assert tmp.loc[2, 'c47_0_0'].round(5) == -0.55461
        assert tmp.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-03-29'

    def test_exit(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = POSTGRESQL_ENGINE
        temp_dir = tempfile.mkdtemp()

        # Run
        with Pheno2SQL(csv_file, db_engine, tmpdir=temp_dir) as p2sql:
            p2sql.load_data()

        # Validate
        ## Check table exists
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0","c31_0_0","c34_0_0","c46_0_0","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2

        ## Check that temporary files were deleted
        assert len(os.listdir(temp_dir)) == 0

    def test_sqlite_less_columns_per_table(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'sqlite'

        ## Check tables exist
        table = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert not table.empty

        table = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('ukb_pheno_0_01'), create_engine(db_engine))
        assert not table.empty

        table = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('ukb_pheno_0_02'), create_engine(db_engine))
        assert not table.empty

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine))
        expected_columns = ["eid","c31_0_0","c34_0_0","c46_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine))
        expected_columns = ["eid","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[2, 'c21_0_0'] == 'Option number 2'
        assert pd.isnull(tmp.loc[2, 'c21_1_0'])
        assert tmp.loc[2, 'c21_2_0'] == 'No'

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c31_0_0'] == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[2, 'c31_0_0'] == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        assert int(tmp.loc[2, 'c46_0_0']) == -2

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert tmp.loc[1, 'c48_0_0'] == '2011-08-14'
        assert tmp.loc[2, 'c47_0_0'].round(5) == -0.55461
        assert tmp.loc[2, 'c48_0_0'] == '2010-03-29'

    def test_postgresql_less_columns_per_table(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check tables exist
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert table.iloc[0, 0]

        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_01'), create_engine(db_engine))
        assert table.iloc[0, 0]

        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_02'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine))
        expected_columns = ["eid","c31_0_0","c34_0_0","c46_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine))
        expected_columns = ["eid","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[2, 'c21_0_0'] == 'Option number 2'
        assert pd.isnull(tmp.loc[2, 'c21_1_0'])
        assert tmp.loc[2, 'c21_2_0'] == 'No'

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c31_0_0'].strftime('%Y-%m-%d') == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[2, 'c31_0_0'].strftime('%Y-%m-%d') == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        assert int(tmp.loc[2, 'c46_0_0']) == -2

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 2
        assert tmp.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert tmp.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
        assert tmp.loc[2, 'c47_0_0'].round(5) == -0.55461
        assert tmp.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-03-29'

    def test_custom_tmpdir(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = POSTGRESQL_ENGINE

        with Pheno2SQL(csv_file, db_engine, tmpdir='/tmp/custom/directory/here') as p2sql:
            # Run
            p2sql.load_data()

            # Validate
            ## Check table exists
            table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_00'), create_engine(db_engine))
            assert table.iloc[0, 0]

            ## Check columns are correct
            tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
            expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0","c31_0_0","c34_0_0","c46_0_0","c47_0_0","c48_0_0"]
            assert len(tmp.columns) == len(expected_columns)
            assert all(x in expected_columns for x in tmp.columns)

            ## Check data is correct
            tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
            assert not tmp.empty
            assert tmp.shape[0] == 2

            ## Check that temporary are still there
            assert len(os.listdir('/tmp/custom/directory/here')) > 0

        ## Check that temporary is now clean
        assert len(os.listdir('/tmp/custom/directory/here')) == 0

    def test_sqlite_auxiliary_table_is_created(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'sqlite'

        ## Check tables exist
        table = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert not table.empty

        table = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('ukb_pheno_0_01'), create_engine(db_engine))
        assert not table.empty

        table = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('ukb_pheno_0_02'), create_engine(db_engine))
        assert not table.empty

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine))
        expected_columns = ["eid","c31_0_0","c34_0_0","c46_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine))
        expected_columns = ["eid","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check auxiliary table existance
        table = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format('fields'), create_engine(db_engine))
        assert not table.empty

        ## Check columns are correct
        tmp = pd.read_sql('select * from fields', create_engine(db_engine))
        expected_columns = ["column_name", "table_name"]
        assert len(tmp.columns) >= len(expected_columns)
        assert all(x in tmp.columns for x in expected_columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from fields', create_engine(db_engine), index_col='column_name')
        assert not tmp.empty
        assert tmp.shape[0] == 8
        assert tmp.loc['c21_0_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c21_1_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c21_2_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c31_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c34_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c46_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c47_0_0', 'table_name'] == 'ukb_pheno_0_02'
        assert tmp.loc['c48_0_0', 'table_name'] == 'ukb_pheno_0_02'

    def test_postgresql_auxiliary_table_is_created_and_has_minimum_data_required(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check tables exist
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert table.iloc[0, 0]

        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_01'), create_engine(db_engine))
        assert table.iloc[0, 0]

        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_02'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine))
        expected_columns = ["eid","c31_0_0","c34_0_0","c46_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine))
        expected_columns = ["eid","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check auxiliary table existance
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('fields'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        tmp = pd.read_sql('select * from fields', create_engine(db_engine))
        expected_columns = ["column_name", "table_name"]
        assert len(tmp.columns) >= len(expected_columns)
        assert all(x in tmp.columns for x in expected_columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from fields', create_engine(db_engine), index_col='column_name')
        assert not tmp.empty
        assert tmp.shape[0] == 8
        assert tmp.loc['c21_0_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c21_1_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c21_2_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c31_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c34_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c46_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c47_0_0', 'table_name'] == 'ukb_pheno_0_02'
        assert tmp.loc['c48_0_0', 'table_name'] == 'ukb_pheno_0_02'

    def test_postgresql_auxiliary_table_with_more_information(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example01.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check tables exist
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert table.iloc[0, 0]

        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_01'), create_engine(db_engine))
        assert table.iloc[0, 0]

        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_02'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check auxiliary table existance
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('fields'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        tmp = pd.read_sql('select * from fields', create_engine(db_engine))
        expected_columns = ["column_name", "field_id", "inst", "arr", "coding", "table_name", "type", "description"]
        assert len(tmp.columns) == len(expected_columns), len(tmp.columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from fields', create_engine(db_engine), index_col='column_name')
        assert not tmp.empty
        assert tmp.shape[0] == 8
        assert tmp.loc['c21_0_0', 'field_id'] == '21'
        assert tmp.loc['c21_0_0', 'inst'] == 0
        assert tmp.loc['c21_0_0', 'arr'] == 0
        assert tmp.loc['c21_0_0', 'coding'] == 100261
        assert tmp.loc['c21_0_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c21_0_0', 'type'] == 'Categorical (single)'
        assert tmp.loc['c21_0_0', 'description'] == 'An string value'

        assert tmp.loc['c21_1_0', 'field_id'] == '21'
        assert tmp.loc['c21_1_0', 'inst'] == 1
        assert tmp.loc['c21_1_0', 'arr'] == 0
        assert tmp.loc['c21_1_0', 'coding'] == 100261
        assert tmp.loc['c21_1_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c21_1_0', 'type'] == 'Categorical (single)'
        assert tmp.loc['c21_1_0', 'description'] == 'An string value'

        assert tmp.loc['c21_2_0', 'field_id'] == '21'
        assert tmp.loc['c21_2_0', 'inst'] == 2
        assert tmp.loc['c21_2_0', 'arr'] == 0
        assert tmp.loc['c21_2_0', 'coding'] == 100261
        assert tmp.loc['c21_2_0', 'table_name'] == 'ukb_pheno_0_00'
        assert tmp.loc['c21_2_0', 'type'] == 'Categorical (single)'
        assert tmp.loc['c21_2_0', 'description'] == 'An string value'

        assert tmp.loc['c31_0_0', 'field_id'] == '31'
        assert tmp.loc['c31_0_0', 'inst'] == 0
        assert tmp.loc['c31_0_0', 'arr'] == 0
        assert pd.isnull(tmp.loc['c31_0_0', 'coding'])
        assert tmp.loc['c31_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c31_0_0', 'type'] == 'Date'
        assert tmp.loc['c31_0_0', 'description'] == 'A date'

        assert tmp.loc['c34_0_0', 'field_id'] == '34'
        assert tmp.loc['c34_0_0', 'inst'] == 0
        assert tmp.loc['c34_0_0', 'arr'] == 0
        assert tmp.loc['c34_0_0', 'coding'] == 9
        assert tmp.loc['c34_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c34_0_0', 'type'] == 'Integer'
        assert tmp.loc['c34_0_0', 'description'] == 'Some integer'

        assert tmp.loc['c46_0_0', 'field_id'] == '46'
        assert tmp.loc['c46_0_0', 'inst'] == 0
        assert tmp.loc['c46_0_0', 'arr'] == 0
        assert pd.isnull(tmp.loc['c46_0_0', 'coding'])
        assert tmp.loc['c46_0_0', 'table_name'] == 'ukb_pheno_0_01'
        assert tmp.loc['c46_0_0', 'type'] == 'Integer'
        assert tmp.loc['c46_0_0', 'description'] == 'Some another integer'

        assert tmp.loc['c47_0_0', 'field_id'] == '47'
        assert tmp.loc['c47_0_0', 'inst'] == 0
        assert tmp.loc['c47_0_0', 'arr'] == 0
        assert pd.isnull(tmp.loc['c47_0_0', 'coding'])
        assert tmp.loc['c47_0_0', 'table_name'] == 'ukb_pheno_0_02'
        assert tmp.loc['c47_0_0', 'type'] == 'Continuous'
        assert tmp.loc['c47_0_0', 'description'] == 'Some continuous value'

        assert tmp.loc['c48_0_0', 'field_id'] == '48'
        assert tmp.loc['c48_0_0', 'inst'] == 0
        assert tmp.loc['c48_0_0', 'arr'] == 0
        assert pd.isnull(tmp.loc['c48_0_0', 'coding'])
        assert tmp.loc['c48_0_0', 'table_name'] == 'ukb_pheno_0_02'
        assert tmp.loc['c48_0_0', 'type'] == 'Time'
        assert tmp.loc['c48_0_0', 'description'] == 'Some time'

    def test_postgresql_two_csv_files(self):
        # Prepare
        csv01 = get_repository_path('pheno2sql/example08_01.csv')
        csv02 = get_repository_path('pheno2sql/example08_02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL((csv01, csv02), db_engine)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check tables exist
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_0_00'), create_engine(db_engine))
        assert table.iloc[0, 0]

        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('ukb_pheno_1_00'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine))
        expected_columns = ["eid","c21_0_0","c21_1_0","c21_2_0","c31_0_0","c34_0_0","c46_0_0","c47_0_0","c48_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        tmp = pd.read_sql('select * from ukb_pheno_1_00', create_engine(db_engine))
        expected_columns = ["eid","c100_0_0", "c100_1_0", "c100_2_0", "c110_0_0", "c120_0_0", "c130_0_0", "c140_0_0", "c150_0_0"]
        assert len(tmp.columns) == len(expected_columns)
        assert all(x in expected_columns for x in tmp.columns)

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 5
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[1, 'c31_0_0'].strftime('%Y-%m-%d') == '2011-03-07'
        assert int(tmp.loc[1, 'c34_0_0']) == -33
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[1, 'c47_0_0'].round(5) == 41.55312
        assert tmp.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-07-14'

        assert tmp.loc[5, 'c21_0_0'] == 'Option number 5'
        assert tmp.loc[5, 'c21_1_0'] == 'Maybe'
        assert tmp.loc[5, 'c21_2_0'] == 'Probably'
        assert pd.isnull(tmp.loc[5, 'c31_0_0'])
        assert int(tmp.loc[5, 'c34_0_0']) == -4
        assert int(tmp.loc[5, 'c46_0_0']) == 1
        assert pd.isnull(tmp.loc[5, 'c47_0_0'])
        assert tmp.loc[5, 'c48_0_0'].strftime('%Y-%m-%d') == '1999-10-11'

        tmp = pd.read_sql('select * from ukb_pheno_1_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 3
        assert int(tmp.loc[1, 'c100_0_0']) == -9
        assert int(tmp.loc[1, 'c100_1_0']) == 3
        assert pd.isnull(tmp.loc[1, 'c100_2_0'])
        assert tmp.loc[1, 'c110_0_0'].round(5) == 42.55312
        assert int(tmp.loc[1, 'c120_0_0']) == -33
        assert tmp.loc[1, 'c130_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c140_0_0'].strftime('%Y-%m-%d') == '2011-03-07'
        assert tmp.loc[1, 'c150_0_0'].strftime('%Y-%m-%d') == '2010-07-14'

        assert pd.isnull(tmp.loc[3, 'c100_0_0'])
        assert int(tmp.loc[3, 'c100_1_0']) == -4
        assert int(tmp.loc[3, 'c100_2_0']) == -10
        assert tmp.loc[3, 'c110_0_0'].round(5) == -35.31471
        assert int(tmp.loc[3, 'c120_0_0']) == 0
        assert tmp.loc[3, 'c130_0_0'] == 'Option number 3'
        assert tmp.loc[3, 'c140_0_0'].strftime('%Y-%m-%d') == '1997-04-15'
        assert pd.isnull(tmp.loc[3, 'c150_0_0'])

    def test_sqlite_query_single_table(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=999999)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c48_0_0']

        query_result = next(p2sql.query(columns))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 4
        assert all(x in query_result.index for x in range(1, 4 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 4
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])

        assert query_result.loc[1, 'c48_0_0'] == '2011-08-14'
        assert query_result.loc[2, 'c48_0_0'] == '2016-11-30'
        assert query_result.loc[3, 'c48_0_0'] == '2010-01-01'
        assert query_result.loc[4, 'c48_0_0'] == '2011-02-15'

    def test_postgresql_query_single_table(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=999999)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c48_0_0']

        query_result = next(p2sql.query(columns))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 4
        assert all(x in query_result.index for x in range(1, 4 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 4
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])

        assert query_result.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
        assert query_result.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2016-11-30'
        assert query_result.loc[3, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-01-01'
        assert query_result.loc[4, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-02-15'

    def test_postgresql_two_csv_files_query_single_table(self):
        # Prepare
        csv01 = get_repository_path('pheno2sql/example08_01.csv')
        csv02 = get_repository_path('pheno2sql/example08_02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL((csv01, csv02), db_engine, n_columns_per_table=999999)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c48_0_0']

        query_result = next(p2sql.query(columns))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 5
        assert all(x in query_result.index for x in range(1, 5 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 5
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'
        assert query_result.loc[5, 'c21_0_0'] == 'Option number 5'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])
        assert query_result.loc[5, 'c21_2_0'] == 'Probably'

        assert query_result.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-07-14'
        assert query_result.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2017-11-30'
        assert query_result.loc[3, 'c48_0_0'].strftime('%Y-%m-%d') == '2020-01-01'
        assert query_result.loc[4, 'c48_0_0'].strftime('%Y-%m-%d') == '1990-02-15'
        assert query_result.loc[5, 'c48_0_0'].strftime('%Y-%m-%d') == '1999-10-11'

    @nottest
    def test_sqlite_query_multiple_tables(self):
        # RIGHT and FULL OUTER JOINs are not currently supported

        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c48_0_0']

        query_result = p2sql.query(columns)

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 4
        assert all(x in query_result.index for x in range(1, 4 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 4
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])

        assert query_result.loc[1, 'c48_0_0'] == '2011-08-14'
        assert query_result.loc[2, 'c48_0_0'] == '2016-11-30'
        assert query_result.loc[3, 'c48_0_0'] == '2010-01-01'
        assert query_result.loc[4, 'c48_0_0'] == '2011-02-15'

    def test_postgresql_query_multiple_tables(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c48_0_0']

        query_result = next(p2sql.query(columns))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 4
        assert all(x in query_result.index for x in range(1, 4 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 4
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])

        assert query_result.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
        assert query_result.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2016-11-30'
        assert query_result.loc[3, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-01-01'
        assert query_result.loc[4, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-02-15'

    def test_postgresql_two_csv_files_query_multiple_tables(self):
        # Prepare
        csv01 = get_repository_path('pheno2sql/example08_01.csv')
        csv02 = get_repository_path('pheno2sql/example08_02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL((csv01, csv02), db_engine, n_columns_per_table=999999)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c110_0_0', 'c150_0_0']

        query_result = next(p2sql.query(columns))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 5
        assert all(x in query_result.index for x in range(1, 5 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 5
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'
        assert query_result.loc[5, 'c21_0_0'] == 'Option number 5'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])
        assert query_result.loc[5, 'c21_2_0'] == 'Probably'

        assert query_result.loc[1, 'c110_0_0'].round(5) == 42.55312
        assert pd.isnull(query_result.loc[2, 'c110_0_0'])
        assert query_result.loc[3, 'c110_0_0'].round(5) == -35.31471
        assert pd.isnull(query_result.loc[4, 'c110_0_0'])
        assert pd.isnull(query_result.loc[5, 'c110_0_0'])

        assert query_result.loc[1, 'c150_0_0'].strftime('%Y-%m-%d') == '2010-07-14'
        assert query_result.loc[2, 'c150_0_0'].strftime('%Y-%m-%d') == '2017-11-30'
        assert pd.isnull(query_result.loc[3, 'c150_0_0'])
        assert pd.isnull(query_result.loc[4, 'c150_0_0'])
        assert pd.isnull(query_result.loc[5, 'c150_0_0'])

    def test_postgresql_two_csv_files_flipped_query_multiple_tables(self):
        # Prepare
        # In this test the files are just flipped
        csv01 = get_repository_path('pheno2sql/example08_01.csv')
        csv02 = get_repository_path('pheno2sql/example08_02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL((csv02, csv01), db_engine, n_columns_per_table=999999)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c110_0_0', 'c150_0_0']

        query_result = next(p2sql.query(columns))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 5
        assert all(x in query_result.index for x in range(1, 5 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 5
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'
        assert query_result.loc[5, 'c21_0_0'] == 'Option number 5'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])
        assert query_result.loc[5, 'c21_2_0'] == 'Probably'

        assert query_result.loc[1, 'c110_0_0'].round(5) == 42.55312
        assert pd.isnull(query_result.loc[2, 'c110_0_0'])
        assert query_result.loc[3, 'c110_0_0'].round(5) == -35.31471
        assert pd.isnull(query_result.loc[4, 'c110_0_0'])
        assert pd.isnull(query_result.loc[5, 'c110_0_0'])

        assert query_result.loc[1, 'c150_0_0'].strftime('%Y-%m-%d') == '2010-07-14'
        assert query_result.loc[2, 'c150_0_0'].strftime('%Y-%m-%d') == '2017-11-30'
        assert pd.isnull(query_result.loc[3, 'c150_0_0'])
        assert pd.isnull(query_result.loc[4, 'c150_0_0'])
        assert pd.isnull(query_result.loc[5, 'c150_0_0'])

    @nottest
    def test_sqlite_query_custom_columns(self):
        # SQLite is very limited when selecting variables, renaming, doing math operations, etc
        pass

    def test_postgresql_query_custom_columns(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c47_0_0', '(c47_0_0 ^ 2.0) as c47_squared']

        query_result = next(p2sql.query(columns))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 4
        assert all(x in query_result.index for x in range(1, 4 + 1))

        assert len(query_result.columns) == len(columns)
        assert all(x in ['c21_0_0', 'c21_2_0', 'c47_0_0', 'c47_squared'] for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 4
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'
        assert query_result.loc[3, 'c21_0_0'] == 'Option number 3'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'
        assert query_result.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])

        assert query_result.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert query_result.loc[2, 'c47_0_0'].round(5) == -0.55461
        assert query_result.loc[3, 'c47_0_0'].round(5) == -5.32471
        assert query_result.loc[4, 'c47_0_0'].round(5) == 55.19832

        assert query_result.loc[1, 'c47_squared'].round(5) == round(45.55412 ** 2, 5)
        assert query_result.loc[2, 'c47_squared'].round(5) == round((-0.55461) ** 2, 5)
        assert query_result.loc[3, 'c47_squared'].round(5) == round((-5.32471) ** 2, 5)
        assert query_result.loc[4, 'c47_squared'].round(5) == round(55.19832 ** 2, 5)

    @nottest
    def test_sqlite_query_single_filter(self):
        # RIGHT and FULL OUTER JOINs are not currently supported

        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c47_0_0']
        filter = ['c47_0_0 > 0']

        query_result = p2sql.query(columns, filter)

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 2
        assert all(x in query_result.index for x in (1, 4))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 2
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])

        assert query_result.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert query_result.loc[4, 'c47_0_0'].round(5) == 55.19832

    def test_postgresql_query_single_filter(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c47_0_0']
        filter = ['c47_0_0 > 0']

        query_result = next(p2sql.query(columns, filterings=filter))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 2
        assert all(x in query_result.index for x in (1, 4))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 2
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[4, 'c21_0_0'] == 'Option number 4'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert pd.isnull(query_result.loc[4, 'c21_2_0'])

        assert query_result.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert query_result.loc[4, 'c47_0_0'].round(5) == 55.19832

    @nottest
    def test_sqlite_query_multiple_and_filter(self):
        # 'RIGHT and FULL OUTER JOINs are not currently supported'

        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c47_0_0', 'c48_0_0']
        filter = ["c48_0_0 > '2011-01-01'", "c21_2_0 <> ''"]

        query_result = p2sql.query(columns, filter)

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 2
        assert all(x in query_result.index for x in (1, 2))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 2
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'

        assert query_result.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert query_result.loc[2, 'c47_0_0'].round(5) == -0.55461

    def test_postgresql_query_multiple_and_filter(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c47_0_0', 'c48_0_0']
        filter = ["c48_0_0 > '2011-01-01'", "c21_2_0 <> ''"]

        query_result = next(p2sql.query(columns, filterings=filter))

        # Validate
        assert query_result is not None

        assert query_result.index.name == 'eid'
        assert len(query_result.index) == 2
        assert all(x in query_result.index for x in (1, 2))

        assert len(query_result.columns) == len(columns)
        assert all(x in columns for x in query_result.columns)

        assert not query_result.empty
        assert query_result.shape[0] == 2
        assert query_result.loc[1, 'c21_0_0'] == 'Option number 1'
        assert query_result.loc[2, 'c21_0_0'] == 'Option number 2'

        assert query_result.loc[1, 'c21_2_0'] == 'Yes'
        assert query_result.loc[2, 'c21_2_0'] == 'No'

        assert query_result.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert query_result.loc[2, 'c47_0_0'].round(5) == -0.55461

        assert query_result.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
        assert query_result.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2016-11-30'

    def test_sqlite_float_is_empty(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example03.csv')
        db_engine = SQLITE_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'sqlite'

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[2, 'c21_0_0'] == 'Option number 2'
        assert pd.isnull(tmp.loc[2, 'c21_1_0'])
        assert tmp.loc[2, 'c21_2_0'] == 'No'
        assert tmp.loc[3, 'c21_0_0'] == 'Option number 3'
        assert tmp.loc[3, 'c21_1_0'] == 'Of course'
        assert tmp.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(tmp.loc[4, 'c21_2_0'])

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c31_0_0'] == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[2, 'c31_0_0'] == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        assert int(tmp.loc[2, 'c46_0_0']) == -2
        assert tmp.loc[3, 'c31_0_0'] == '2007-03-19'
        assert int(tmp.loc[3, 'c34_0_0']) == 1
        assert int(tmp.loc[3, 'c46_0_0']) == -7

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        # FIXME: this is strange, data type in this particular case needs np.round
        assert np.round(tmp.loc[1, 'c47_0_0'], 5) == 45.55412
        assert tmp.loc[1, 'c48_0_0'] == '2011-08-14'
        assert tmp.loc[2, 'c47_0_0'] == -0.55461
        assert tmp.loc[2, 'c48_0_0'] == '2016-11-30'
        assert pd.isnull(tmp.loc[3, 'c47_0_0'])
        assert tmp.loc[3, 'c48_0_0'] == '2010-01-01'

    def test_postgresql_float_is_empty(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example03.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[2, 'c21_0_0'] == 'Option number 2'
        assert pd.isnull(tmp.loc[2, 'c21_1_0'])
        assert tmp.loc[2, 'c21_2_0'] == 'No'
        assert tmp.loc[3, 'c21_0_0'] == 'Option number 3'
        assert tmp.loc[3, 'c21_1_0'] == 'Of course'
        assert tmp.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(tmp.loc[4, 'c21_2_0'])


        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c31_0_0'].strftime('%Y-%m-%d') == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[2, 'c31_0_0'].strftime('%Y-%m-%d') == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        assert int(tmp.loc[2, 'c46_0_0']) == -2
        assert tmp.loc[3, 'c31_0_0'].strftime('%Y-%m-%d') == '2007-03-19'
        assert int(tmp.loc[3, 'c34_0_0']) == 1
        assert int(tmp.loc[3, 'c46_0_0']) == -7

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert tmp.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
        assert tmp.loc[2, 'c47_0_0'].round(5) == -0.55461
        assert tmp.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2016-11-30'
        assert pd.isnull(tmp.loc[3, 'c47_0_0'])
        assert tmp.loc[3, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-01-01'

    def test_postgresql_timestamp_is_empty(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example04.csv')
        db_engine = 'postgresql://test:test@localhost:5432/ukb'

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_00', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c21_0_0'] == 'Option number 1'
        assert tmp.loc[1, 'c21_1_0'] == 'No response'
        assert tmp.loc[1, 'c21_2_0'] == 'Yes'
        assert tmp.loc[2, 'c21_0_0'] == 'Option number 2'
        assert pd.isnull(tmp.loc[2, 'c21_1_0'])
        assert tmp.loc[2, 'c21_2_0'] == 'No'
        assert tmp.loc[3, 'c21_0_0'] == 'Option number 3'
        assert tmp.loc[3, 'c21_1_0'] == 'Of course'
        assert tmp.loc[3, 'c21_2_0'] == 'Maybe'
        assert pd.isnull(tmp.loc[4, 'c21_2_0'])

        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c31_0_0'].strftime('%Y-%m-%d') == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[2, 'c31_0_0'].strftime('%Y-%m-%d') == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        assert int(tmp.loc[2, 'c46_0_0']) == -2
        assert tmp.loc[3, 'c31_0_0'].strftime('%Y-%m-%d') == '2007-03-19'
        assert int(tmp.loc[3, 'c34_0_0']) == 1
        assert int(tmp.loc[3, 'c46_0_0']) == -7
        assert pd.isnull(tmp.loc[4, 'c31_0_0'])

        tmp = pd.read_sql('select * from ukb_pheno_0_02', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c47_0_0'].round(5) == 45.55412
        assert tmp.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
        assert tmp.loc[2, 'c47_0_0'].round(5) == -0.55461
        assert pd.isnull(tmp.loc[2, 'c48_0_0'])
        assert tmp.loc[3, 'c47_0_0'].round(5) == -5.32471
        assert tmp.loc[3, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-01-01'

    def test_postgresql_integer_is_nan(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example06_nan_integer.csv')
        db_engine = 'postgresql://test:test@localhost:5432/ukb'

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4
        assert tmp.loc[1, 'c31_0_0'].strftime('%Y-%m-%d') == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert int(tmp.loc[1, 'c46_0_0']) == -9
        assert tmp.loc[2, 'c31_0_0'].strftime('%Y-%m-%d') == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        pd.isnull(tmp.loc[2, 'c46_0_0'])
        assert tmp.loc[3, 'c31_0_0'].strftime('%Y-%m-%d') == '2007-03-19'
        assert int(tmp.loc[3, 'c34_0_0']) == 1
        assert int(tmp.loc[3, 'c46_0_0']) == -7
        assert pd.isnull(tmp.loc[4, 'c31_0_0'])

    def test_postgresql_first_row_is_nan_integer(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example07_first_nan_integer.csv')
        db_engine = 'postgresql://test:test@localhost:5432/ukb'

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check data is correct
        tmp = pd.read_sql('select * from ukb_pheno_0_01', create_engine(db_engine), index_col='eid')
        assert not tmp.empty
        assert tmp.shape[0] == 4

        assert tmp.loc[1, 'c31_0_0'].strftime('%Y-%m-%d') == '2012-01-05'
        assert int(tmp.loc[1, 'c34_0_0']) == 21
        assert pd.isnull(tmp.loc[1, 'c46_0_0'])

        assert tmp.loc[2, 'c31_0_0'].strftime('%Y-%m-%d') == '2015-12-30'
        assert int(tmp.loc[2, 'c34_0_0']) == 12
        pd.isnull(tmp.loc[2, 'c46_0_0'])

        assert tmp.loc[3, 'c31_0_0'].strftime('%Y-%m-%d') == '2007-03-19'
        assert int(tmp.loc[3, 'c34_0_0']) == 1
        assert int(tmp.loc[3, 'c46_0_0']) == -7

        assert pd.isnull(tmp.loc[4, 'c31_0_0'])

    def test_postgresql_sql_chunksize01(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, sql_chunksize=2)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c48_0_0']

        query_result = p2sql.query(columns)

        # Validate
        assert query_result is not None

        import collections
        assert isinstance(query_result, collections.Iterable)

        index_len_sum = 0

        for chunk_idx, chunk in enumerate(query_result):
            assert chunk.index.name == 'eid'

            index_len_sum += len(chunk.index)
            assert len(chunk.index) == 2

            if chunk_idx == 0:
                indexes = (1, 2)
                assert all(x in chunk.index for x in indexes)
            else:
                indexes = (3, 4)
                assert all(x in chunk.index for x in indexes)

            assert len(chunk.columns) == len(columns)
            assert all(x in columns for x in chunk.columns)

            assert not chunk.empty
            assert chunk.shape[0] == 2
            if chunk_idx == 0:
                assert chunk.loc[1, 'c21_0_0'] == 'Option number 1'
                assert chunk.loc[2, 'c21_0_0'] == 'Option number 2'

                assert chunk.loc[1, 'c21_2_0'] == 'Yes'
                assert chunk.loc[2, 'c21_2_0'] == 'No'

                assert chunk.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
                assert chunk.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2016-11-30'
            else:
                assert chunk.loc[3, 'c21_0_0'] == 'Option number 3'
                assert chunk.loc[4, 'c21_0_0'] == 'Option number 4'

                assert chunk.loc[3, 'c21_2_0'] == 'Maybe'
                assert pd.isnull(chunk.loc[4, 'c21_2_0'])

                assert chunk.loc[3, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-01-01'
                assert chunk.loc[4, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-02-15'

        assert index_len_sum == 4

    def test_postgresql_sql_chunksize02(self):
        # Prepare
        csv_file = get_repository_path('pheno2sql/example02.csv')
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=3, sql_chunksize=3)
        p2sql.load_data()

        # Run
        columns = ['c21_0_0', 'c21_2_0', 'c48_0_0']

        query_result = p2sql.query(columns)

        # Validate
        assert query_result is not None

        import collections
        assert isinstance(query_result, collections.Iterable)

        index_len_sum = 0

        for chunk_idx, chunk in enumerate(query_result):
            assert chunk.index.name == 'eid'

            index_len_sum += len(chunk.index)

            if chunk_idx == 0:
                assert len(chunk.index) == 3
                indexes = (1, 2, 3)
                assert all(x in chunk.index for x in indexes)
            else:
                assert len(chunk.index) == 1
                indexes = (4,)
                assert all(x in chunk.index for x in indexes)

            assert len(chunk.columns) == len(columns)
            assert all(x in columns for x in chunk.columns)

            assert not chunk.empty
            if chunk_idx == 0:
                assert chunk.shape[0] == 3

                assert chunk.loc[1, 'c21_0_0'] == 'Option number 1'
                assert chunk.loc[2, 'c21_0_0'] == 'Option number 2'
                assert chunk.loc[3, 'c21_0_0'] == 'Option number 3'

                assert chunk.loc[1, 'c21_2_0'] == 'Yes'
                assert chunk.loc[2, 'c21_2_0'] == 'No'
                assert chunk.loc[3, 'c21_2_0'] == 'Maybe'

                assert chunk.loc[1, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-08-14'
                assert chunk.loc[2, 'c48_0_0'].strftime('%Y-%m-%d') == '2016-11-30'
                assert chunk.loc[3, 'c48_0_0'].strftime('%Y-%m-%d') == '2010-01-01'
            else:
                assert chunk.shape[0] == 1

                assert chunk.loc[4, 'c21_0_0'] == 'Option number 4'

                assert pd.isnull(chunk.loc[4, 'c21_2_0'])

                assert chunk.loc[4, 'c48_0_0'].strftime('%Y-%m-%d') == '2011-02-15'

        assert index_len_sum == 4

    def test_postgresql_samples_table_created(self):
        # Prepare
        directory = get_repository_path('pheno2sql/example10')

        csv_file = get_repository_path(os.path.join(directory, 'example10_diseases.csv'))
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, bgen_sample_file=os.path.join(directory, 'impv2.sample'),
                          n_columns_per_table=2, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check samples table exists
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('samples'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        samples_data = pd.read_sql('select * from samples', create_engine(db_engine))
        expected_columns = ["index", "eid"]
        assert len(samples_data.columns) == len(expected_columns)
        assert all(x in samples_data.columns for x in expected_columns)

        ## Check data is correct
        samples_data = pd.read_sql('select * from samples', create_engine(db_engine), index_col='index')
        assert not samples_data.empty
        assert samples_data.shape[0] == 5
        assert samples_data.loc[1, 'eid'] == 1000050
        assert samples_data.loc[2, 'eid'] == 1000030
        assert samples_data.loc[3, 'eid'] == 1000040
        assert samples_data.loc[4, 'eid'] == 1000010
        assert samples_data.loc[5, 'eid'] == 1000020

    def test_postgresql_events_tables_only_one_instance_filled(self):
        # Prepare
        directory = get_repository_path('pheno2sql/example10')

        csv_file = get_repository_path(os.path.join(directory, 'example10_diseases.csv'))
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, bgen_sample_file=os.path.join(directory, 'impv2.sample'),
                          n_columns_per_table=2, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check samples table exists
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('events'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        events_data = pd.read_sql('select * from events order by eid, instance, event', create_engine(db_engine))
        expected_columns = ['eid', 'field_id', 'instance', 'event']
        assert len(events_data.columns) == len(expected_columns)
        assert all(x in events_data.columns for x in expected_columns)

        ## Check data is correct
        assert not events_data.empty
        assert events_data.shape[0] == 6
        assert events_data.loc[0, 'eid'] == 1000020
        assert events_data.loc[0, 'field_id'] == 84
        assert events_data.loc[0, 'event'] == 'E103'

        assert events_data.loc[1, 'eid'] == 1000020
        assert events_data.loc[1, 'field_id'] == 84
        assert events_data.loc[1, 'event'] == 'N308'

        assert events_data.loc[2, 'eid'] == 1000020
        assert events_data.loc[2, 'field_id'] == 84
        assert events_data.loc[2, 'event'] == 'Q750'

        assert events_data.loc[3, 'eid'] == 1000030
        assert events_data.loc[3, 'field_id'] == 84
        assert events_data.loc[3, 'event'] == 'N308'

        assert events_data.loc[4, 'eid'] == 1000040
        assert events_data.loc[4, 'field_id'] == 84
        assert events_data.loc[4, 'event'] == 'N308'

        assert events_data.loc[5, 'eid'] == 1000050
        assert events_data.loc[5, 'field_id'] == 84
        assert events_data.loc[5, 'event'] == 'E103'

    def test_postgresql_events_tables_only_two_instances_filled(self):
        # Prepare
        directory = get_repository_path('pheno2sql/example11')

        csv_file = get_repository_path(os.path.join(directory, 'example11_diseases.csv'))
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, bgen_sample_file=os.path.join(directory, 'impv2.sample'),
                          n_columns_per_table=2, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check samples table exists
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('events'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        events_data = pd.read_sql('select * from events order by eid, instance, event', create_engine(db_engine))
        expected_columns = ['eid', 'field_id', 'instance', 'event']
        assert len(events_data.columns) == len(expected_columns)
        assert all(x in events_data.columns for x in expected_columns)

        ## Check data is correct
        assert not events_data.empty
        assert events_data.shape[0] == 11

        cidx = 0
        assert events_data.loc[cidx, 'eid'] == 1000010
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'E103'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000010
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'Q750'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000020
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'E103'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000020
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'N308'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000020
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'J32'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000030
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'N308'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000030
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'Q750'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000040
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'N308'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000040
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'E103'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000040
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'Q750'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000050
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'E103'

    def test_postgresql_events_tables_two_categorical_fields_and_two_and_three_instances(self):
        # Prepare
        directory = get_repository_path('pheno2sql/example12')

        csv_file = get_repository_path(os.path.join(directory, 'example12_diseases.csv'))
        db_engine = POSTGRESQL_ENGINE

        p2sql = Pheno2SQL(csv_file, db_engine, bgen_sample_file=os.path.join(directory, 'impv2.sample'),
                          n_columns_per_table=2, loading_n_jobs=1)

        # Run
        p2sql.load_data()

        # Validate
        assert p2sql.db_type == 'postgresql'

        ## Check samples table exists
        table = pd.read_sql("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '{}');".format('events'), create_engine(db_engine))
        assert table.iloc[0, 0]

        ## Check columns are correct
        events_data = pd.read_sql('select * from events order by eid, instance, event', create_engine(db_engine))
        expected_columns = ['eid', 'field_id', 'instance', 'event']
        assert len(events_data.columns) == len(expected_columns)
        assert all(x in events_data.columns for x in expected_columns)

        ## Check total data
        assert not events_data.empty
        assert events_data.shape[0] == 25

        cidx = 0
        assert events_data.loc[cidx, 'eid'] == 1000010
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'E103'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000010
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'Q750'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000020
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'E103'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000020
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'N308'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000020
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'J32'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000030
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'N308'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000030
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'Q750'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000040
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'N308'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000040
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'E103'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000040
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 1
        assert events_data.loc[cidx, 'event'] == 'Q750'

        cidx += 1
        assert events_data.loc[cidx, 'eid'] == 1000050
        assert events_data.loc[cidx, 'field_id'] == 84
        assert events_data.loc[cidx, 'instance'] == 0
        assert events_data.loc[cidx, 'event'] == 'E103'