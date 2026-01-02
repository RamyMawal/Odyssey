# from typing import Dict
import logging
import pathlib
import cv2
import cv2.aruco as aruco
import numpy as np

# from models.vectors import Pose2D
from stores.controller_context import ControllerContext
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)

calibration_data_path = pathlib.Path(__file__).parent.parent.parent / "calibration_data_latest.npz"


def get_available_cameras(max_cameras: int = 10) -> list[tuple[int, str]]:
    """Scan for available cameras and return list of (index, description)."""
    available = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            available.append((i, f"Camera {i} ({width}x{height})"))
            cap.release()
    return available


class ObserverThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    frame_signal = pyqtSignal(object, object, object)
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)

    def __init__(self, context: ControllerContext, camera_index: int = 0):
        super().__init__()
        self._running = True
        self.context = context
        self.cap = None
        self.camera_index = camera_index

    def run(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)

        try:
            npz_file = np.load(calibration_data_path)
            camera_matrix = npz_file["camera_matrix"]
            dist_coeff = npz_file["dist_coeffs"]
        except FileNotFoundError:
            logger.error(f"Calibration file not found: {calibration_data_path}")
            if self.cap and self.cap.isOpened():
                self.cap.release()
            return
        except Exception as e:
            logger.error(f"Failed to load calibration data: {e}")
            if self.cap and self.cap.isOpened():
                self.cap.release()
            return

        arucoParams = cv2.aruco.DetectorParameters()

        while self._running:
            ret, frame = self.cap.read()
            if not ret:
                break

            undistorted_frame = cv2.undistort(
                frame, cameraMatrix=camera_matrix, distCoeffs=dist_coeff
            )
            gray = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = aruco.detectMarkers(
                gray, self.dictionary, parameters=arucoParams
            )
            rgb_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2RGB)

            rgb_frame = aruco.drawDetectedMarkers(rgb_frame, corners, ids)

            self.context.frame_data_store.update(ids=ids, corners=corners)

            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(
                rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
            )
            self.change_pixmap_signal.emit(qt_image)

        if self.cap and self.cap.isOpened():
            self.cap.release()

    def stop(self):
        self._running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
