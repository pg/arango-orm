"Test cases for the :module:`arango_orm.database`"

from datetime import date
from . import TestBase
from .data import Person, Car, cars
from arango import ArangoClient
from arango.collections.base import CollectionStatisticsError

from arango_orm.database import Database
from arango_orm.collections import Collection
from arango_orm.query import Query


class TestQuery(TestBase):

    @classmethod
    def setUpClass(cls):
        db = cls._get_db_obj()
        db.create_collection(Person)
        db.create_collection(Car)

    @classmethod
    def tearDownClass(cls):
        db = cls._get_db_obj()
        db.drop_collection(Person)
        db.drop_collection(Car)

    def _populate_cars(self):
        db = self._get_db_obj()
        for car in cars:
            db.add(car)

    def test_01_get_count(self):

        db = self._get_db_obj()

        count_1 = db.query(Person).count()
        assert count_1 == 0

    def test_02_get_all_records(self):
        db = self._get_db_obj()

        count_1 = db.query(Person).count()
        db.add(Person(name='test1', _key='12312', dob=date(year=2016, month=9, day=12)))
        db.add(Person(name='test2', _key='22312', dob=date(year=2015, month=9, day=12)))

        assert db.query(Person).count() == count_1 + 2

        persons = db.query(Person).all()
        assert len(persons) == 2
        assert isinstance(persons[0], Person)

    def test_03_get_records_by_aql(self):
        db = self._get_db_obj()
        persons = db.query(Person).aql("FOR rec IN @@collection RETURN rec")

        assert len(persons) == 2
        assert isinstance(persons[0], Person)

    def test_04_get_by_key(self):
        db = self._get_db_obj()

        p = db.query(Person).by_key("12312")
        assert p.name == 'test1'

    def test_05_test_filter_condition(self):

        self._populate_cars()
        db = self._get_db_obj()

        results = db.query(Car).filter("year==2005").all()

        assert 1 == len(results) 
        assert "Mitsubishi" == results[0].make
        assert "Lancer" == results[0].model
        assert 2005 == results[0].year

    def test_06_test_filter_condition_using_bind_vars(self):

        db = self._get_db_obj()

        results = db.query(Car).filter("year==@year", year=2005).all()

        assert 1 == len(results) 
        assert "Mitsubishi" == results[0].make
        assert "Lancer" == results[0].model
        assert 2005 == results[0].year

    def test_07_multiple_filter_conditions(self):
        db = self._get_db_obj()

        results = db.query(Car).filter("make==@make", make='Honda').filter("year<=@year", year=1990).all()

        assert 1 == len(results) 
        assert "Honda" == results[0].make
        assert "Civic" == results[0].model
        assert 1984 == results[0].year

    def test_08_filter_or_conditions(self):
        db = self._get_db_obj()

        results = db.query(Car).filter(
            "make==@make", make='Mitsubishi').filter(
            "year<=@year", _or=True, year=1987).all()

        assert 2 == len(results) 
        assert results[0].make in ['Honda', 'Mitsubishi']
        assert results[0].model in ['Civic', 'Lancer']
        assert results[0].year in [1984, 2005]

    def test_09_limit_records(self):
        db = self._get_db_obj()

        records = db.query(Car).limit(5).all()

        assert len(records) == 5
        assert isinstance(records[0], Car)

        # we'll get only 2 records since we have total of 7 records
        records = db.query(Car).limit(3, 5).all()

        assert len(records) == 2
        assert isinstance(records[0], Car)

    def test_10_sort_records(self):
        db = self._get_db_obj()

        records = db.query(Car).sort("year DESC").all()

        assert isinstance(records[0], Car)
        assert 2005 == records[0].year

        records = db.query(Car).sort("year").all()

        assert isinstance(records[0], Car)
        assert 1984 == records[0].year

    def test_11_multiple_sort(self):

        db = self._get_db_obj()

        records = db.query(Car).sort("make").sort("year DESC").all()

        assert isinstance(records[0], Car)
        assert 2001 == records[0].year
        assert "Honda" == records[0].make
        assert "Civic" == records[0].model

        assert isinstance(records[4], Car)
        assert 2005 == records[4].year
        assert "Mitsubishi" == records[4].make
        assert "Lancer" == records[4].model

        assert isinstance(records[6], Car)
        assert 1988 == records[6].year
        assert "Toyota" == records[6].make
        assert "Corolla" == records[6].model

    def test_12_sort_and_limit_records(self):
        db = self._get_db_obj()

        records = db.query(Car).sort("year DESC").limit(2).all()

        assert 2 == len(records)

        assert isinstance(records[0], Car)
        assert 2005 == records[0].year
        assert "Mitsubishi" == records[0].make
        assert "Lancer" == records[0].model

        assert isinstance(records[1], Car)
        assert 2004 == records[1].year
        assert "Toyota" == records[1].make
        assert "Corolla" == records[1].model

    def test_13_filter_sort_and_limit_records(self):

        db = self._get_db_obj()

        records = db.query(Car).filter("year>=2000").sort("year ASC").limit(2).all()

        assert 2 == len(records)

        assert isinstance(records[0], Car)
        assert 2001 == records[0].year
        assert "Honda" == records[0].make
        assert "Civic" == records[0].model

        assert isinstance(records[1], Car)
        assert 2004 == records[1].year
        assert "Toyota" == records[1].make
        assert "Corolla" == records[1].model
