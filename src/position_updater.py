import logging
from stores.controller_context import ControllerContext
from PyQt6.QtCore import QThread, QMutex
import serial
import time

logger = logging.getLogger(__name__)


class PositionUpdater(QThread):
    def __init__(self, context: ControllerContext):
        super().__init__()
        self._running = True
        self.context = context
        self.serial_conn = None
        self._current_port = None
        self._mutex = QMutex()

    def run(self):
        logger.info("Running PositionUpdater")
        while self._running:
            if self.context.port is None or self.context.port == "":
                time.sleep(0.5)
                continue

            # Check if port changed or connection needs to be established
            if self._current_port != self.context.port:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                self.serial_conn = None
                self._current_port = self.context.port

            # Open connection if needed
            if self.serial_conn is None or not self.serial_conn.is_open:
                try:
                    self.serial_conn = serial.Serial(
                        self.context.port, 115200, timeout=1
                    )
                    logger.info(f"Serial port opened: {self.context.port}")
                except serial.SerialException as e:
                    logger.error(f"Failed to open serial port: {e}")
                    time.sleep(0.5)
                    continue

            targets = self.context.agent_target_store.get_all()

            for marker_id, pose in self.context.agent_pose_store.get_all().items():
                if pose is None:
                    continue
                else:
                    if marker_id not in targets:
                        xt = pose.x
                        yt = pose.y
                    else:
                        target_pose = targets[marker_id]
                        xt, yt = target_pose.x, target_pose.y

                    message = f"1,{marker_id},{pose.x:.3f},{pose.y:.3f},{pose.theta:.3f},{xt:.3f},{yt:.3f}\n"

                logger.debug(message.strip())
                self._mutex.lock()
                try:
                    self.serial_conn.write(message.encode("utf-8"))
                    logger.info(message)
                except serial.SerialException as e:
                    logger.error(f"Serial error: {e}")
                    # Connection lost, will reconnect on next iteration
                    if self.serial_conn and self.serial_conn.is_open:
                        self.serial_conn.close()
                    self.serial_conn = None
                finally:
                    self._mutex.unlock()

            time.sleep(0.05)
        logger.info("Stopping PositionUpdater")

    def stop(self):
        self._running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Serial port closed")
