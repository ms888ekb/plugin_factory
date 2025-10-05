# extent_picker_tool.py
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes, QgsRectangle, QgsGeometry

class ExtentPickerTool(QgsMapTool):
    """Drag to draw a rectangle; emits QgsRectangle (project CRS) or None."""
    extentPicked = pyqtSignal(object)  # QgsRectangle or None

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)
        self.rb = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setStrokeColor(QColor(0, 0, 0))
        self.rb.setFillColor(QColor(0, 0, 0, 0))
        self.rb.setWidth(2)
        self._start = None  # QgsPointXY (map coords)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._finish(cancel=True)

    def canvasPressEvent(self, e):
        if e.button() == Qt.RightButton:
            self._finish(cancel=True)
            return
        if e.button() != Qt.LeftButton:
            return
        self._start = self.toMapCoordinates(e.pos())
        # show a tiny rect immediately
        rect = QgsRectangle(self._start, self._start)
        self._update_band(rect)

    def canvasMoveEvent(self, e):
        if self._start is None:
            return
        cur = self.toMapCoordinates(e.pos())
        rect = QgsRectangle(self._start, cur)
        rect.normalize()  # <-- in-place!
        self._update_band(rect)

    def canvasReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or self._start is None:
            return
        end = self.toMapCoordinates(e.pos())
        rect = QgsRectangle(self._start, end)
        rect.normalize()  # <-- in-place!
        self._finish(cancel=False, rect=rect)

    # ----- helpers -----
    def _update_band(self, rect: QgsRectangle):
        # simplest & API-safe: build geometry directly from the rectangle
        self.rb.setToGeometry(QgsGeometry.fromRect(rect), None)

    def _finish(self, cancel: bool, rect: QgsRectangle = None):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)
        self.canvas.unsetMapTool(self)
        self._start = None
        self.extentPicked.emit(None if cancel else rect)
