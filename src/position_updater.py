import global_data
from data_sender import SendDataTask
from PyQt6.QtCore import QRunnable, QMutex
import serial
import time

serial_mutex = QMutex()

class PositionUpdater(QRunnable):

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        print("Running PositionUpdater")
        while self._running:

            if global_data.port is None or global_data.port == "":
                time.sleep(0.5)
                continue

            for marker_id, (x, y, yaw) in global_data.marker_positions.items():
                print(f"Position for Marker ID: {marker_id}, X: {x:.3f}, Y: {y:.3f}")
                if marker_id not in global_data.target_positions:
                    xt = x
                    yt = y
                else:
                    xt, yt = global_data.target_positions[marker_id]
                print(f"Target Position for Marker ID: {marker_id}, X: {xt:.3f}, Y: {yt:.3f}, yaw: {yaw:.3f}")

                serial_mutex.lock()
                try:
                    with serial.Serial(global_data.port, 115200, timeout=1) as ser:
                        message = f"{marker_id},{x:.3f},{y:.3f},{yaw:.3f},{xt:.3f},{yt:.3f}\n"
                        ser.write(message.encode('utf-8'))
                        print(f"Sent: {message.strip()}")
                except serial.SerialException as e:
                    print(f"Serial error: {e}")
                finally:
                    serial_mutex.unlock()
                    
            time.sleep(0.1)
        print("Stopping PositionUpdater")

            

    def stop(self):
        self._running = False