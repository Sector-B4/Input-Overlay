import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QFrame
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QStyleOption

# Import our dedicated background state polling thread
from .mouseHookUp import MouseListenerThread

# ==============================================================================
# STYLED BLUEPRINT COMPONENT
# ==============================================================================
class StyledFrame(QFrame):
    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(self.style().PrimitiveElement.PE_Widget, opt, painter, self)


# ==============================================================================
# MAIN MOUSE VISUALIZER PANEL
# ==============================================================================
class MouseVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_stylesheet()


        # Connect our high-speed background engine directly via signals
        self.listener_thread = MouseListenerThread()
        self.listener_thread.mouse_signal.connect(self.handle_mouse_input)
        self.listener_thread.start()

    def init_ui(self):
        self.mouseBase = StyledFrame(self)
        self.mouseBase.setObjectName("mouseBase")
        self.mouseBase.setGeometry(10, 10, 160, 260) 

        self.mouseLeft = StyledFrame(self.mouseBase)
        self.mouseLeft.setObjectName("mouseLeft")
        self.mouseLeft.setGeometry(10, 12, 60, 85)

        self.mouseRight = StyledFrame(self.mouseBase)
        self.mouseRight.setObjectName("mouseRight")
        self.mouseRight.setGeometry(90, 12, 60, 85)

        self.mouseMiddle = StyledFrame(self.mouseBase)
        self.mouseMiddle.setObjectName("mouseMiddle")
        self.mouseMiddle.setGeometry(74, 25, 12, 45)

        self.button_map = {
            'LEFT': self.mouseLeft,
            'RIGHT': self.mouseRight,
            'MIDDLE': self.mouseMiddle
        }

    def load_stylesheet(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            qss_path = os.path.join(current_dir, "mouseUiStyle.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"[Error] Failed to read style sheet: {e}")

    def sizeHint(self):
        # Return the exact dimensions your content needs
        return QSize(700, 300) # Adjust these values to fit your layout

    @pyqtSlot(str, bool)
    def handle_mouse_input(self, button_name, is_pressed):
        """Forces an instantaneous UI refresh while protecting custom QSS geometry shapes."""
        if button_name in self.button_map:
            widget = self.button_map[button_name]
            
            # Update the core active property layout status
            widget.setProperty("active", is_pressed)
            
            # Force the engine to polish the QSS stylesheet rule variations
            if widget.style():
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                
            # Direct hardware canvas redraw invocation
            widget.repaint()


# ==============================================================================
# STANDALONE OVERLAY APP CANVAS
# ==============================================================================
class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("benywise | mouse test")
        self.setFixedSize(180, 280)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.visualizer = MouseVisualizer(self)
        self.setCentralWidget(self.visualizer)

    def closeEvent(self, event):
        self.visualizer.closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = TestWindow()
    main_window.show()
    sys.exit(app.exec())