import pytest
from qgis.testing import start_app

# Ensure QGIS can find its prefixes when running outside QGIS.
# On Windows OSGeo4W, you may set this in your shell instead:
# os.environ.setdefault("QGIS_PREFIX_PATH", r"C:\OSGeo4W64\apps\qgis")
# os.environ.setdefault("GDAL_DATA", r"C:\OSGeo4W64\share\gdal")

@pytest.fixture(scope="session", autouse=True)
def qgis_app():
    app = start_app()
    return app
