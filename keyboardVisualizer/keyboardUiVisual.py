import os
import subprocess
import time
import ctypes
import sys
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QApplication
from PyQt6.QtCore import pyqtSlot, Qt, QThread, pyqtSignal, QSize

# =========================================================================
# THE BACKGROUND CONNECTOR LINK
# =========================================================================
class KeyboardListenerThread(QThread):
    key_signal = pyqtSignal(int, bool)

    def __init__(self):
        super().__init__()
        self.running = False
        self.process = None
        self.last_down_times = {}

    def run(self):
        self.running = True
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cpp_backend_path = os.path.join(current_dir, "keyboardHookup.exe")

        if not os.path.exists(cpp_backend_path):
            print(f"[Error] C++ keyboard backend executable missing at: {cpp_backend_path}")
            return

        self.process = subprocess.Popen(
            [cpp_backend_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )

        if self.process.stderr is not None:
            for line in self.process.stderr:
                if not self.running:
                    break
                
                parts = line.strip().split('_')
                if len(parts) != 3 or parts[0] != 'K':
                    continue
                
                try:
                    vk_code = int(parts[1])
                    state = int(parts[2])
                    now = time.perf_counter()

                    if state == 1:
                        self.last_down_times[vk_code] = now
                        self.key_signal.emit(vk_code, True)
                    elif state == 0:
                        duration = now - self.last_down_times.get(vk_code, now)
                        if duration < 0.010:
                            self.msleep(10)
                        self.key_signal.emit(vk_code, False)
                except ValueError:
                    continue

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                pass

# =========================================================================
# THE KEYBOARD VISUAL INTERFACE LABELS
# =========================================================================
class KeyboardVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_stylesheet()
        
        # --- NEW: Sync with System Caps Lock State ---
        self.sync_caps_lock_state()
        
        self.listener_thread = KeyboardListenerThread()
        self.listener_thread.key_signal.connect(self.update_key_visual)
        self.listener_thread.start()

    def sync_caps_lock_state(self):
        # 0x14 is the VK code for VK_CAPITAL (Caps Lock)
        # GetKeyState returns the toggle state in the lowest bit
        is_caps_on = ctypes.windll.user32.GetKeyState(0x14) & 1
        
        caps_key = self.key_map.get(20)
        if caps_key:
            caps_key.setProperty("active", bool(is_caps_on))
            # Refresh the styling to show the correct state immediately
            caps_key.style().unpolish(caps_key)
            caps_key.style().polish(caps_key)
            caps_key.repaint()
    
    def init_ui(self):
        # --- FIXED DESIGN MATRIX SYSTEM ---
        U = 40          # Base 1U cap size
        gap = 4         # Gap between adjacent keycap boundaries
        padding = 12    # Outer perimeter margin boundary

        # A standard 75% configuration scales perfectly to exactly 16U total track width
        frame_width = int(16 * U + (15 * gap) + (padding * 2))
        frame_height = int(6 * U + (5 * gap) + (padding * 2))

        self.keyboardBase = QFrame(self)
        self.keyboardBase.setObjectName("keyboardBase")
        self.keyboardBase.setGeometry(0, 0, frame_width, frame_height) 

        self.key_map = {}

        def create_key(vk_code, text, x_start, y_start, u_width=1.0):
            width = int(u_width * U + (u_width - 1) * gap if u_width > 1 else u_width * U)
            height = U
            
            lbl = QLabel(text, self.keyboardBase)
            lbl.setObjectName(f"key_{vk_code}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setGeometry(int(x_start), int(y_start), int(width), int(height))
            
            self.key_map[vk_code] = lbl
            return x_start + width + gap 

        # Map clean vertical Y track offsets dynamically
        y_row = [padding + i * (U + gap) for i in range(6)]

        # =========================================================================
        # ROW 1: Function Row (Total: Balanced to fit exact 16U boundary)
        # =========================================================================
        x = padding
        x = create_key(27, "Esc", x, y_row[0], 1.0)
        for i in range(1, 5): x = create_key(111 + i, f"F{i}", x, y_row[0], 1.0)
        for i in range(5, 9): x = create_key(111 + i, f"F{i}", x, y_row[0], 1.0)
        for i in range(9, 13): x = create_key(111 + i, f"F{i}", x, y_row[0], 1.0)
        x = create_key(44, "Prtc", x, y_row[0], 1.0)
        x = create_key(145, "ScrL", x, y_row[0], 1.0) 
        create_key(46, "Del", x, y_row[0], 1.0)

        # =========================================================================
        # ROW 2: Numbers Row (FIXED: Remapped to align VK codes 49-57, then 48)
        # =========================================================================
        x = padding
        x = create_key(192, "~ `", x, y_row[1], 1.0)
        
        # Explicitly map keys 1-9 to VK codes 49-57
        for i in range(1, 10):
            x = create_key(48 + i, str(i), x, y_row[1], 1.0)
            
        # Map the 0 key to its true VK code: 48
        x = create_key(48, "0", x, y_row[1], 1.0)
        
        x = create_key(189, "- _", x, y_row[1], 1.0)
        x = create_key(187, "+ =", x, y_row[1], 1.0)
        x = create_key(8, "backspace", x, y_row[1], 2.0) 
        create_key(36, "hm", x, y_row[1], 1.0)

        # =========================================================================
        # ROW 3: QWERTY Row
        # =========================================================================
        x = padding
        x = create_key(9, "Tab", x, y_row[2], 1.5) 
        row3_keys = [
            (81, "Q"), (87, "W"), (69, "E"), (82, "R"), (84, "T"), 
            (89, "Y"), (85, "U"), (73, "I"), (79, "O"), (80, "P"),
            (219, "[ {"), (221, "] }")
        ]
        for vk, txt in row3_keys: x = create_key(vk, txt, x, y_row[2], 1.0)
        x = create_key(220, "\\ |", x, y_row[2], 1.5)
        create_key(35, "end", x, y_row[2], 1.0)

        # =========================================================================
        # ROW 4: ASDF Row
        # =========================================================================
        x = padding
        x = create_key(20, "Caps", x, y_row[3], 1.75) 
        row4_keys = [
            (65, "A"), (83, "S"), (68, "D"), (70, "F"), (71, "G"),
            (72, "H"), (74, "J"), (75, "K"), (76, "L"), (186, "; :"), (222, "' \"")
        ]

        for vk, txt in row4_keys: x = create_key(vk, txt, x, y_row[3], 1.0)
        x = create_key(13, "Enter", x, y_row[3], 2.25) 
        create_key(33, "pUp", x, y_row[3], 1.0)

        # =========================================================================
        # ROW 5: ZXCV Row (FIXED: Left shift changed from 16 to 160)
        # =========================================================================
        x = padding
        x = create_key(160, "Shift", x, y_row[4], 2.25) # 160 = VK_LSHIFT
        row5_keys = [
            (90, "Z"), (88, "X"), (67, "C"), (86, "V"), (66, "B"),
            (78, "N"), (77, "M"), (188, "< ,"), (190, "> ."), (191, "/ ?")
        ]
        for vk, txt in row5_keys: x = create_key(vk, txt, x, y_row[4], 1.0)
        x = create_key(161, "shft", x, y_row[4], 1.75)  # 161 = VK_RSHIFT
        x = create_key(38, "▲", x, y_row[4], 1.0)
        create_key(34, "pDw", x, y_row[4], 1.0)

        # =========================================================================
        # ROW 6: Modifiers & Spacebar (FIXED: Added Windows Key 91, balanced sizes)
        # Total Units: Ctrl(1.0) + Win(1.0) + Alt(1.0) + Space(6.0) + Rest(7.0) = 16.0U
        # =========================================================================
        x = padding
        x = create_key(162, "ctrl", x, y_row[5], 1.0) 
        x = create_key(91, "win", x, y_row[5], 1.0)   # 91 = VK_LWIN
        x = create_key(164, "alt", x, y_row[5], 1.0)
        
        x = create_key(32, "benywise | Xcro-engine v0.1", x, y_row[5], 6.0) 
        
        x = create_key(165, "alt", x, y_row[5], 1.0)
        x = create_key(255, "fn", x, y_row[5], 1.0)   # Hardware-level placeholder
        x = create_key(163, "ctrl", x, y_row[5], 1.0)
        x = create_key(45, "ins", x, y_row[5], 1.0)
        x = create_key(37, "◀", x, y_row[5], 1.0)
        x = create_key(40, "▼", x, y_row[5], 1.0)
        create_key(39, "▶", x, y_row[5], 1.0)

    def load_stylesheet(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            qss_path = os.path.join(current_dir, "keyboardUiStyle.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"[Error] Failed to read keyboard style sheet: {e}")

    def sizeHint(self):
        # Return the exact dimensions your content needs
        return QSize(700, 300) # Adjust these values to fit your layout
    
    @pyqtSlot(int, bool)
    def update_key_visual(self, vk_code, is_pressed):
        widget = self.key_map.get(vk_code)
        if widget:
            # --- THIS IS THE TOGGLE SECTION ---
            if vk_code == 20:
                if is_pressed:
                    new_state = not widget.property("active")
                    widget.setProperty("active", new_state)
            else:
                widget.setProperty("active", is_pressed)
            # --- END OF TOGGLE SECTION ---

            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.repaint()

    def closeEvent(self, event):
        self.listener_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Xcro Unified Keyboard UI")
    window.setStyleSheet("background-color: #0b0b0b;")

    window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    
    visualizer = KeyboardVisualizer(window)
    
    # Track the exact dynamic bounding region and pad the window container cleanly
    base_geom = visualizer.keyboardBase.geometry()
    window.resize(base_geom.width() + 20, base_geom.height() + 20)
    
    # Place visualizer container with 10px interior margin offset alignment
    visualizer.move(10, 10)
    window.show()
    
    sys.exit(app.exec())