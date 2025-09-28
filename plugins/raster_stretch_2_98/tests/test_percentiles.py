# tests/test_percentiles.py
import os
import numpy as np
from types import SimpleNamespace

from osgeo import gdal
from qgis.core import QgsRasterLayer, QgsRectangle
from qgis.PyQt.QtWidgets import QMainWindow
from raster_stretch_2_98.raster_stretch import RasterStretch

# --- helpers ----------------------------------------------------------------
def make_ramp_tif(fp, w=128, h=128, nodata=0):
    """Create a small ramp GeoTIFF with a top stripe of NoData."""
    arr = np.arange(w*h, dtype=np.uint16).reshape(h, w)
    arr[:5, :] = nodata  # inject a NoData stripe
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(str(fp), w, h, 1, gdal.GDT_UInt16, options=["TILED=YES"])
    band = ds.GetRasterBand(1)
    band.WriteArray(arr)
    band.SetNoDataValue(nodata)
    ds = None
    return fp

class DummyIface:
    """Minimal iface stub to satisfy the plugin constructor."""
    def __init__(self, mw):
        self._mw = mw
    def mainWindow(self): return self._mw
    def addToolBar(self, name):
        from qgis.PyQt.QtWidgets import QToolBar
        tb = QToolBar(name, self._mw); self._mw.addToolBar(tb); return tb
    def addDockWidget(self, area, w): self._mw.addDockWidget(area, w)
    def addPluginToMenu(self, menu, action): pass
    def removePluginMenu(self, menu, action): pass
    def removeToolBarIcon(self, action): pass
    def messageBar(self): return self
    def pushMessage(self, *a, **k): pass

# --- the actual test --------------------------------------------------------
def test_percentile_matches_cumulative_cut(qgis_app, tmp_path):
    # 1) tiny raster on disk
    tif = make_ramp_tif(tmp_path / "ramp.tif", nodata=0)

    # 2) load in QGIS
    layer = QgsRasterLayer(str(tif), "ramp")
    assert layer.isValid()
    provider = layer.dataProvider()

    # 3) plugin instance (with minimal iface) + stub dock UI state
    mw = QMainWindow()
    plugin = RasterStretch(DummyIface(mw))

    # Stub out just the fields _percentile_from_hist touches
    class _Check:
        def isChecked(self): return True  # enable UI nodata override
    class _Line:
        def isEnabled(self): return True
        def text(self): return "0"        # override NoData=0

    plugin.dockwidget = SimpleNamespace(checkBoxNoData=_Check(), lineEditNoData=_Line())

    # 4) call your method
    lo, hi = plugin._percentile_from_hist(
        provider=provider, band=1,
        lower_pct=2.0, upper_pct=98.0,
        extent=QgsRectangle(), bins=256
    )
    assert lo is not None and hi is not None and lo < hi

    # 5) reference: provider.cumulativeCut on the same band/extent/sample
    rlo, rhi = provider.cumulativeCut(1, 0.02, 0.98, QgsRectangle(), sampleSize=200_000)

    # 6) allow small tolerance ~ one histogram bin
    tol = (rhi - rlo) / 256.0 + 1e-6
    assert abs(lo - rlo) <= tol
    assert abs(hi - rhi) <= tol
