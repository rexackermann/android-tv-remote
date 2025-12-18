from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
import time

class TouchpadWidget(QWidget):
    """
    A widget acting as a touchpad.
    Emits signals for swipes, clicks, and navigation.
    """
    swipeSignal = pyqtSignal(str)  # UP, DOWN, LEFT, RIGHT
    clickSignal = pyqtSignal()     # DPAD_CENTER
    backSignal = pyqtSignal()      # BACK button
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setStyleSheet("background-color: #2D2D2D; border-radius: 10px;")
        
        self.last_pos = None
        self.press_pos = None
        self.press_time = 0
        self.is_dragging = False
        
        # UX Thresholds
        self.swipe_threshold = 50
        self.tap_timeout = 0.2  # Seconds

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.setBrush(QBrush(QColor("#353535")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        # Draw "Touchpad" label in center
        painter.setPen(QPen(QColor("#808080")))
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Touchpad Area")

    def mousePressEvent(self, event):
        self.last_pos = event.pos()
        self.press_pos = event.pos()
        self.press_time = time.time()
        self.is_dragging = False

    def mouseMoveEvent(self, event):
        if not self.last_pos:
            return
            
        current_pos = event.pos()
        delta = current_pos - self.last_pos
        
        # Very simple swipe detection based on aggregated distance
        # Ideally, we would track velocity
        
        # Accumulate distance logic could be added here for "mouse pointer" mode
        # For now, we strictly implement swipe gestures for D-Pad navigation
        
        self.last_pos = current_pos

    def mouseReleaseEvent(self, event):
        release_time = time.time()
        release_pos = event.pos()
        
        delta_x = release_pos.x() - self.press_pos.x()
        delta_y = release_pos.y() - self.press_pos.y()
        
        duration = release_time - self.press_time
        
        # Tap detection
        if duration < self.tap_timeout and abs(delta_x) < 10 and abs(delta_y) < 10:
            if event.button() == Qt.MouseButton.LeftButton:
                self.clickSignal.emit()
            elif event.button() == Qt.MouseButton.RightButton:
                self.backSignal.emit()
            return
            
        # Swipe detection
        if abs(delta_x) > abs(delta_y):
            if abs(delta_x) > self.swipe_threshold:
                if delta_x > 0:
                    self.swipeSignal.emit("DPAD_RIGHT")
                else:
                    self.swipeSignal.emit("DPAD_LEFT")
        else:
            if abs(delta_y) > self.swipe_threshold:
                if delta_y > 0:
                    self.swipeSignal.emit("DPAD_DOWN")
                else:
                    self.swipeSignal.emit("DPAD_UP")
        
        self.last_pos = None

