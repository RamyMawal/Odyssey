from stores.controller_context import ControllerContext
from PyQt6.QtCore import QThread, QMutex
import serial
import time

serial_mutex = QMutex()

class PositionUpdater(QThread):

    def __init__(self, context: ControllerContext):
        super().__init__()
        self._running = True
        self.context = context

    def run(self):
        print("Running PositionUpdater")
        while self._running:

            if self.context.port is None or self.context.port == "":
                time.sleep(0.5)
                continue

            targets = self.context.agent_target_store.get_all()

            for marker_id, pose in self.context.agent_pose_store.get_all().items():
                print(f"Position for Marker ID: {marker_id}, X: {pose.x:.3f}, Y: {pose.y:.3f}, yaw: {pose.theta:.3f}")
                if marker_id not in targets:
                    xt = pose.x
                    yt = pose.y
                else:
                    target_pose = targets[marker_id]
                    xt, yt = target_pose.x, target_pose.y

                serial_mutex.lock()
                try:
                    with serial.Serial(self.context.port, 115200, timeout=1) as ser:
                        message = f"{marker_id},{pose.x:.3f},{pose.y:.3f},{pose.theta:.3f},{xt:.3f},{yt:.3f}\n"
                        ser.write(message.encode('utf-8'))
                        print(f"Sent: {message.strip()}")
                except serial.SerialException as e:
                    print(f"Serial error: {e}")
                finally:
                    serial_mutex.unlock()
                    
            time.sleep(0.05)
        print("Stopping PositionUpdater")

            

    def stop(self):
        self._running = False