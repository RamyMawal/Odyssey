import global_data
from data_sender import SendDataTask
from PyQt6.QtCore import QRunnable, QThreadPool
import serial
import time


class PositionUpdater(QRunnable):

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        print("Running PositionUpdater")
        while self._running:

            if global_data.port is None or global_data.port == "":
                print("Serial port not set. Waiting...")
                continue

            for marker_id, (x, y) in global_data.marker_positions.items():
                print(f"Position for Marker ID: {marker_id}, X: {x:.3f}, Y: {y:.3f}")
                if marker_id not in global_data.target_positions:
                    xt = x
                    yt = y
                else:
                    xt, yt = global_data.target_positions[marker_id]
                print(f"Target Position for Marker ID: {marker_id}, X: {xt:.3f}, Y: {yt:.3f}")

                task = SendDataTask(
                    port=global_data.port,  
                    baudrate=115200,
                    id=marker_id,
                    x=x,
                    y=y,
                    rot=0.0,  # Placeholder for rotation
                    xt=xt,
                    yt=yt
                )
                QThreadPool.globalInstance().start(task)
            
            time.sleep(0.2)
        print("Stopping PositionUpdater")

            

    def stop(self):
        self._running = False