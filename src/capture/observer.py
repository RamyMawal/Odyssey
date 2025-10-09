from typing import Dict
import pathlib
import cv2
import cv2.aruco as aruco
import numpy as np
from models.vectors import Pose2D
from stores.controller_context import ControllerContext
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

calibration_data_path = "../calibration_data_latest.npz"

class ObserverThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    frame_signal = pyqtSignal(object, object, object)
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_7X7_100)

    def __init__(self, context:ControllerContext):
        super().__init__()
        self._running = True
        self.context = context

    def run(self):
        cap = cv2.VideoCapture(2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)
        path = pathlib.PosixPath(calibration_data_path)
        npz_file = np.load(path)
        camera_matrix = npz_file['camera_matrix']
        dist_coeff = npz_file['dist_coeffs']
        arucoParams = cv2.aruco.DetectorParameters()

        while self._running:
            ret, frame = cap.read()
            if not ret:
                break

            undistorted_frame = cv2.undistort(frame, cameraMatrix=camera_matrix, distCoeffs=dist_coeff)
            gray = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = aruco.detectMarkers(gray, self.dictionary, parameters=arucoParams)
            rgb_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2RGB)

            rgb_frame = aruco.drawDetectedMarkers(rgb_frame, corners, ids)

            self.context.frame_data_store.update(ids=ids, corners=corners)

            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.change_pixmap_signal.emit(qt_image)

        cap.release()

    def stop(self):
        self._running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

