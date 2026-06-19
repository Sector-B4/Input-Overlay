import os
import subprocess
import time
from PyQt6.QtCore import QThread, pyqtSignal

class MouseListenerThread(QThread):
    mouse_signal = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.running = False
        self.process = None
        self.last_down_times = {"LEFT": 0.0, "RIGHT": 0.0, "MIDDLE": 0.0}

    def run(self):
        self.running = True
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cpp_backend_path = os.path.join(current_dir, "mouseHookup.exe")

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
                
                token = line.strip()
                now = time.perf_counter()

                # --- LEFT CLICK ---
                if token == "M_L_1":
                    self.last_down_times["LEFT"] = now
                    self.mouse_signal.emit("LEFT", True)
                    
                elif token == "M_L_0":
                    duration = now - self.last_down_times["LEFT"]
                    if duration < 0.010:  # Your consistent 10ms threshold
                        self.msleep(5)   # Hold open for 1 frame
                        self.mouse_signal.emit("LEFT", False)
                    else:
                        self.mouse_signal.emit("LEFT", False)

                # --- RIGHT CLICK ---
                elif token == "M_R_1":
                    self.last_down_times["RIGHT"] = now
                    self.mouse_signal.emit("RIGHT", True)
                elif token == "M_R_0":
                    duration = now - self.last_down_times["RIGHT"]
                    if duration < 0.010:
                        self.msleep(5)
                        self.mouse_signal.emit("RIGHT", False)
                    else:
                        self.mouse_signal.emit("RIGHT", False)

                # --- MIDDLE CLICK ---
                elif token == "M_M_1":
                    self.mouse_signal.emit("MIDDLE", True)
                elif token == "M_M_0":
                    self.mouse_signal.emit("MIDDLE", False)

                # --- SCROLL WHEEL ---
                elif token == "M_W_UP" or token == "M_W_DOWN":
                    self.mouse_signal.emit("MIDDLE", True)
                    self.msleep(15)  # Quick, clear blip for the scroll wheel
                    self.mouse_signal.emit("MIDDLE", False)

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                pass