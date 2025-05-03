import cv2
import cv2.aruco as aruco
import numpy as np
import global_data
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

calibration_data_path = "/home/ramy-mawal/Desktop/Projects/rc-robot-ui/calibration_data_latest.npz"

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        cap = cv2.VideoCapture(2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        npz_file = np.load(calibration_data_path)
        camera_matrix = npz_file['camera_matrix']
        dist_coeff = npz_file['dist_coeffs']
        arucoParams = cv2.aruco.DetectorParameters()
        marker_length = 0.015  # Adjust this to the correct size

        while self._running:
            ret, frame = cap.read()
            if not ret:
                break

            undistorted_frame = cv2.undistort(frame, cameraMatrix=camera_matrix, distCoeffs=dist_coeff)
            gray = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = aruco.detectMarkers(gray, self.dictionary, parameters=arucoParams)
            rgb_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2RGB)

            img_drawn = aruco.drawDetectedMarkers(rgb_frame.copy(), corners, ids)

            if ids is not None:
                rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeff)
                global_data.marker_positions = {}  # Clear previous positions
                for i, marker_id in enumerate(ids.flatten()):
                    img_drawn = cv2.drawFrameAxes(img_drawn, camera_matrix, dist_coeff, rvec[i], tvec[i], 0.01)
                    #Multiply by 10 for better coordinates
                    x, y, _ = tvec[i][0]
                    global_data.marker_positions[marker_id] = (x * 10, y * 10)  # Store x and y positions

            h, w, ch = img_drawn.shape
            bytes_per_line = ch * w
            qt_image = QImage(img_drawn.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.change_pixmap_signal.emit(qt_image)

        cap.release()

    def stop(self):
        self._running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

