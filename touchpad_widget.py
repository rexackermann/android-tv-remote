from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QTimer
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QLinearGradient
import time

class TouchpadWidget(QWidget):
    """
    A widget acting as a touchpad.
    Emits signals for swipes, clicks, and navigation.
    """
    swipeSignal = pyqtSignal(str)  # UP, DOWN, LEFT, RIGHT
    clickSignal = pyqtSignal()     # DPAD_CENTER
    longClickSignal = pyqtSignal() # Long Press Action
    backSignal = pyqtSignal()      # BACK button
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.last_pos = None
        self.press_pos = None
        self.press_time = 0
        self.direction_start_time = 0 # To reset acceleration on reversal
        self.is_dragging = False
        self.long_press_triggered = False
        
        # UX Thresholds
        self.swipe_threshold = 30
        self.tap_timeout = 0.2  # Seconds
        self.long_press_timeout = 350 # ms
        
        self.long_press_timer = QTimer(self)
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self._handle_long_press)

        self.repeat_timer = QTimer(self)
        self.repeat_timer.timeout.connect(self._handle_repeat)
        self.repeat_key = None

    def _handle_long_press(self):
        if not self.is_dragging:
            self.long_press_triggered = True
            self.longClickSignal.emit()
            # Start repeating the click for long-press
            self.repeat_key = "CLICK"
            self.direction_start_time = time.time()
            self.repeat_timer.start(100) # Fast repeat for OK

    def _handle_repeat(self):
        if self.repeat_key == "CLICK":
            self.clickSignal.emit()
        elif self.repeat_key:
            # Multi-dimensional acceleration: Distance + Time (In Current Direction)
            elapsed = time.time() - self.direction_start_time
            # Distance factor from initial press
            delta = self.last_pos - self.press_pos
            dist = delta.manhattanLength()
            
            # Base interval from distance (Physics)
            dist_interval = max(50, 350 - (dist * 3.0))
            
            # Add time-based acceleration (decay by ~125ms per second)
            time_factor = elapsed * 125
            final_interval = max(30, int(dist_interval - time_factor))
            
            self.repeat_timer.setInterval(final_interval)
            self.swipeSignal.emit(self.repeat_key)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background (Premium Glassmorphism)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#1c2128"))
        gradient.setColorAt(1, QColor("#0d1117"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#30363d"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 16, 16)
        
        # Subtle Inner Glow/Border
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        painter.drawRoundedRect(self.rect().adjusted(2,2,-2,-2), 14, 14)
        
        # Draw "Touchpad" label in center
        painter.setPen(QPen(QColor("#8b949e")))
        font = painter.font()
        font.setFamily("Inter")
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        
        # Center text with slight transparency
        painter.setOpacity(0.7)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                         "TOUCHPAD\nSwipe to Navigate • Tap to OK\nHold & Pull to Scroll")
        painter.setOpacity(1.0)

    def mousePressEvent(self, event):
        self.last_pos = event.pos()
        self.press_pos = event.pos()
        self.press_time = time.time()
        self.direction_start_time = time.time()
        self.is_dragging = False
        self.long_press_triggered = False
        self.repeat_key = None
        self.repeat_timer.stop()
        self.long_press_timer.start(self.long_press_timeout)

    def mouseMoveEvent(self, event):
        if not self.last_pos:
            return
            
        current_pos = event.pos()
        delta_total = current_pos - self.press_pos
        delta_instant = current_pos - self.last_pos
        dist_total = delta_total.manhattanLength()
        
        if dist_total > 15:
            self.is_dragging = True
            self.long_press_timer.stop()
            
            # 1. Determine direction based on TOTAL delta from press_pos
            new_key = None
            if abs(delta_total.x()) > abs(delta_total.y()):
                if abs(delta_total.x()) > self.swipe_threshold:
                    new_key = "DPAD_RIGHT" if delta_total.x() > 0 else "DPAD_LEFT"
            else:
                if abs(delta_total.y()) > self.swipe_threshold:
                    new_key = "DPAD_DOWN" if delta_total.y() > 0 else "DPAD_UP"
            
            # 2. Check for REVERSAL based on INSTANT movement
            # If the user moves significantly in the opposite direction, we flip even if total delta is still original
            if self.repeat_key and self.repeat_key != "CLICK":
                reversal = False
                if self.repeat_key == "DPAD_RIGHT" and delta_instant.x() < -10: reversal = True
                if self.repeat_key == "DPAD_LEFT" and delta_instant.x() > 10: reversal = True
                if self.repeat_key == "DPAD_UP" and delta_instant.y() > 10: reversal = True
                if self.repeat_key == "DPAD_DOWN" and delta_instant.y() < -10: reversal = True
                
                if reversal:
                    # Determine new direction from the instant push
                    if abs(delta_instant.x()) > abs(delta_instant.y()):
                        new_key = "DPAD_RIGHT" if delta_instant.x() > 0 else "DPAD_LEFT"
                    else:
                        new_key = "DPAD_DOWN" if delta_instant.y() > 0 else "DPAD_UP"
            
            if new_key:
                # If direction flipped while holding, update it and reset acceleration
                if new_key != self.repeat_key and self.repeat_key != "CLICK":
                    self.repeat_key = new_key
                    # Move the press_pos to current pos to reset distance-based physics
                    self.press_pos = current_pos 
                    self.direction_start_time = time.time() # RESET TIME ACCELERATION
                    self.swipeSignal.emit(new_key)
                    
                # Ensure timer is running at baseline
                if not self.repeat_timer.isActive():
                    self.repeat_timer.start(250)
        
        self.last_pos = current_pos

    def mouseReleaseEvent(self, event):
        self.long_press_timer.stop()
        had_repeat = self.repeat_timer.isActive() or self.repeat_key is not None
        self.repeat_timer.stop()
        
        if self.long_press_triggered or had_repeat:
            self.repeat_key = None
            return

        release_time = time.time()
        release_pos = event.pos()
        
        delta_x = release_pos.x() - self.press_pos.x()
        delta_y = release_pos.y() - self.press_pos.y()
        
        duration = release_time - self.press_time
        
        if duration < self.tap_timeout and abs(delta_x) < 10 and abs(delta_y) < 10:
            if event.button() == Qt.MouseButton.LeftButton:
                self.clickSignal.emit()
            elif event.button() == Qt.MouseButton.RightButton:
                self.backSignal.emit()
            return
            
        # Fallback for quick flicks (Physics: rate = fast)
        if abs(delta_x) > abs(delta_y):
            if abs(delta_x) > self.swipe_threshold:
                self.swipeSignal.emit("DPAD_RIGHT" if delta_x > 0 else "DPAD_LEFT")
        else:
            if abs(delta_y) > self.swipe_threshold:
                self.swipeSignal.emit("DPAD_DOWN" if delta_y > 0 else "DPAD_UP")
        
        self.last_pos = None
        self.repeat_key = None

