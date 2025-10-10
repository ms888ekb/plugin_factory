# extent_picker_tool.py
# Futuristic HUD with semi-transparent background the SAME SIZE as the drawn rectangle

from qgis.PyQt.QtCore import pyqtSignal, Qt, QPoint
from qgis.PyQt.QtGui import QColor, QFont, QPen  # <-- import QPen
from qgis.PyQt.QtWidgets import QGraphicsTextItem, QGraphicsRectItem, QGraphicsDropShadowEffect
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes, QgsRectangle, QgsGeometry


class ExtentPickerTool(QgsMapTool):
    """
    Drag to draw a rectangle on the map; shows live '{w}px × {h}px' at the center,
    with a semi-transparent background that EXACTLY matches the current rectangle size.
    Emits extentPicked(QgsRectangle) on finish, or extentPicked(None) on cancel.
    """
    extentPicked = pyqtSignal(object, object, object)  # QgsRectangle or None

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)

        # Rubber band outline (optional visual of the box edges)
        self.rb = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setStrokeColor(QColor(0, 0, 0))
        self.rb.setFillColor(QColor(0, 0, 0, 0))
        self.rb.setWidth(2)

        # Start points (map + screen)
        self._start_map = None
        self._start_screen = None

        # Colors (same hue for text & background; background is more transparent)
        self._textColor = QColor(0, 255, 102, 200)  # neon green, slightly faded
        self._bgColor   = QColor(0, 255, 102, 60)   # same tone, very transparent

        # HUD elements on the canvas scene
        scene = self.canvas.scene()

        # Text: neon mono, bigger, with soft glow
        self._hud_text = QGraphicsTextItem("")
        font = QFont("Consolas")                # any monospaced font is fine
        font.setPointSize(18)                   # larger digits
        font.setWeight(QFont.DemiBold)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setLetterSpacing(QFont.PercentageSpacing, 105)
        self._hud_text.setFont(font)
        self._hud_text.setDefaultTextColor(self._textColor)

        try:
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(22)
            glow.setColor(QColor(0, 255, 102, 120))  # soft neon glow
            glow.setOffset(0, 0)
            self._hud_text.setGraphicsEffect(glow)
        except Exception:
            pass  # in case graphics effects aren't available

        # Background: NO border, same color tone, sized to the current rectangle
        self._hud_bg = QGraphicsRectItem()
        self._hud_bg.setBrush(self._bgColor)
        self._hud_bg.setPen(QPen(Qt.NoPen))  # <-- FIX: wrap NoPen in QPen

        # Add to scene; ensure background is just below the text
        scene.addItem(self._hud_bg);   self._hud_bg.setZValue(1e6 - 1)
        scene.addItem(self._hud_text); self._hud_text.setZValue(1e6)

        # Hidden until the user starts dragging
        self._set_hud_visible(False)

    # ---------- Event handlers ----------

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._finish(cancel=True)

    def canvasPressEvent(self, e):
        if e.button() == Qt.RightButton:
            self._finish(cancel=True)
            return
        if e.button() != Qt.LeftButton:
            return

        # Start points
        self._start_map = self.toMapCoordinates(e.pos())
        self._start_screen = QPoint(e.pos())

        # Initialize a tiny rect and show HUD ("0px × 0px")
        self.rb.setToGeometry(QgsGeometry.fromRect(QgsRectangle(self._start_map, self._start_map)), None)
        self._update_hud(self._start_screen, self._start_screen)
        self._set_hud_visible(True)

    def canvasMoveEvent(self, e):
        if self._start_map is None or self._start_screen is None:
            return

        # Rubber band (map geometry)
        cur_map = self.toMapCoordinates(e.pos())
        rect = QgsRectangle(self._start_map, cur_map)
        rect.normalize()
        self.rb.setToGeometry(QgsGeometry.fromRect(rect), None)

        # HUD (screen geometry)
        self._update_hud(self._start_screen, e.pos())

    def canvasReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or self._start_map is None:
            return
        end_map = self.toMapCoordinates(e.pos())
        rect = QgsRectangle(self._start_map, end_map)
        rect.normalize()
        self._finish(cancel=False, rect=rect)

    # ---------- Helpers ----------

    def _set_hud_visible(self, vis: bool):
        self._hud_text.setVisible(vis)
        self._hud_bg.setVisible(vis)

    def _update_hud(self, start_screen: QPoint, cur_screen: QPoint):
        """
        Update the HUD so that:
          - Numbers show '{w}px × {h}px'
          - Background rect is EXACTLY the size of the current drawn rectangle
          - Text is centered within that background
        """
        # Current rectangle in SCREEN pixels (widget coords)
        x1, y1 = start_screen.x(), start_screen.y()
        x2, y2 = cur_screen.x(), cur_screen.y()
        left, right = (x1, x2) if x1 <= x2 else (x2, x1)
        top, bottom = (y1, y2) if y1 <= y2 else (y2, y1)
        w_px = int(right - left)
        h_px = int(bottom - top)

        # Update numbers
        self._hud_text.setPlainText(f"{w_px}px × {h_px}px")

        # Center the text in the current rectangle
        br = self._hud_text.boundingRect()
        cx = (left + right) / 2.0
        cy = (top + bottom) / 2.0
        self._hud_text.setPos(cx - br.width() / 2.0, cy - br.height() / 2.0)

        # Background covers the ENTIRE rectangle (same tone, transparent)
        self._hud_bg.setRect(left, top, max(0, w_px), max(0, h_px))
        self.width_pix = w_px
        self.height_pix = h_px

    def _finish(self, cancel: bool, rect: QgsRectangle = None):
        # Cleanup overlays and restore canvas state
        self.rb.reset(QgsWkbTypes.PolygonGeometry)
        self._set_hud_visible(False)
        self.canvas.unsetMapTool(self)
        self._start_map = None
        self._start_screen = None
        self.extentPicked.emit(None if cancel else rect,
                               None if cancel else self.width_pix,
                               None if cancel else self.height_pix)
