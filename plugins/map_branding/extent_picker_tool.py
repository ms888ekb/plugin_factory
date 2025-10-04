# -*- coding: utf-8 -*-
from __future__ import annotations

from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes, QgsRectangle, QgsGeometry, QgsProject


class ExtentPickerTool(QgsMapTool):
    """Click-drag to draw a rectangle on the canvas; emits QgsRectangle.
       Esc/right-click cancels and emits None.
    """
    extentPicked = pyqtSignal(object)  # QgsRectangle or None

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)
        self.rb = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setStrokeColor(QColor(0, 0, 0))
        self.rb.setFillColor(QColor(0, 0, 0, 0))
        self.rb.setWidth(2)
        self.start_mappt = None

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._cleanup()
            self.extentPicked.emit(None)

    def canvasPressEvent(self, e):
        if e.button() == Qt.RightButton:
            # cancel
            self._cleanup()
            self.extentPicked.emit(None)
            return
        if e.button() != Qt.LeftButton:
            return
        self.start_mappt = self.toMapCoordinates(e.pos())
        self._update_band(self.start_mappt, self.start_mappt)

    def canvasMoveEvent(self, e):
        if self.start_mappt is None:
            return
        cur = self.toMapCoordinates(e.pos())
        self._update_band(self.start_mappt, cur)

    def canvasReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or self.start_mappt is None:
            return
        end = self.toMapCoordinates(e.pos())
        rect = QgsRectangle(self.start_mappt, end)
        self._cleanup()
        self.extentPicked.emit(rect)

    # helpers
    def _update_band(self, p1, p2):
        rect = QgsRectangle(p1, p2)
        pts = [
            rect.topLeft(), rect.topRight(),
            rect.bottomRight(), rect.bottomLeft(), rect.topLeft()
        ]
        geom = QgsGeometry.fromPolygonXY([[p for p in pts]])
        self.rb.setToGeometry(geom, None)

    def _cleanup(self):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)
        self.canvas.unsetMapTool(self)
        self.start_mappt = None
