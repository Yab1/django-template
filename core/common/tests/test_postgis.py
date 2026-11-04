import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import connection


def test_database_engine_is_postgis():
    assert settings.DATABASES["default"]["ENGINE"] == "django.contrib.gis.db.backends.postgis"
    assert "django.contrib.gis" in settings.INSTALLED_APPS


@pytest.mark.django_db
def test_postgis_point_roundtrip():
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        cursor.execute("SELECT PostGIS_Version()")
        version = cursor.fetchone()
        assert version and version[0]

        point = Point(38.7578, 9.025, srid=4326)
        cursor.execute(
            "SELECT ST_X(ST_GeomFromText(%s, 4326)), ST_Y(ST_GeomFromText(%s, 4326))",
            [point.wkt, point.wkt],
        )
        x, y = cursor.fetchone()
        assert abs(x - 38.7578) < 1e-6
        assert abs(y - 9.025) < 1e-6
