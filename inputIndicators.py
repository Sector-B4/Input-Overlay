import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt

# Import visualizers
from keyboardVisualizer.keyboardUiVisual import KeyboardVisualizer
from mouseVisualizer.mouseUiVisual import MouseVisualizer

class XcroEngineDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.kb = KeyboardVisualizer()
        self.ms = MouseVisualizer()
        
        # Add widgets with stretch factors: 3 for Keyboard, 1 for Mouse
        layout.addWidget(self.kb, stretch=3)
        layout.addWidget(self.ms, stretch=1)
        
        self.setCentralWidget(self.container)
        
        # Set a reasonable starting size, but allow resize
        self.resize(1000, 320)

    def mousePressEvent(self, event):
        self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = XcroEngineDashboard()
    window.show()
    sys.exit(app.exec())