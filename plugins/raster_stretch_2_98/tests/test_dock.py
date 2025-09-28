from qgis.PyQt.QtWidgets import QMainWindow, QToolBar
from raster_stretch_2_98.raster_stretch import RasterStretch

class DummyIface:
    def __init__(self, main):
        self._mw = main
        self._tb = QToolBar("RasterStretch", self._mw)
        self._mw.addToolBar(self._tb)

    def mainWindow(self): return self._mw
    def addDockWidget(self, area, w): self._mw.addDockWidget(area, w)
    def addToolBar(self, name): return self._tb

    # minimal stubs your plugin touches in init/add_action/unload
    def addPluginToMenu(self, menu, action): pass
    def removePluginMenu(self, menu, action): pass
    def removeToolBarIcon(self, action): pass

    # message bar stubs
    def messageBar(self): return self
    def pushMessage(self, *args, **kwargs): pass

    # only needed if your code queries canvas extent in this test (it doesn't)
    def mapCanvas(self): return self._mw

def test_dock_loads(qtbot):
    mw = QMainWindow(); qtbot.addWidget(mw); mw.show()
    plugin = RasterStretch(DummyIface(mw))
    plugin.initGui()
    plugin.run()
    assert plugin.dockwidget is not None
    assert plugin.dockwidget.isVisible()
