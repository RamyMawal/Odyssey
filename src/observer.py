import cv2
import cv2.aruco as aruco
import numpy as np
import global_data
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

calibration_data_path = "/home/ramy-mawal/Desktop/Projects/rc-robot-ui/calibration_data_latest.npz"
marker_length = 0.12  # in cm

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_7X7_100)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        cap = cv2.VideoCapture(2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)
        npz_file = np.load(calibration_data_path)
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

            img_drawn = aruco.drawDetectedMarkers(rgb_frame.copy(), corners, ids)

            if ids is not None:
                rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeff)
                global_data.marker_positions = {} 
                for i, marker_id in enumerate(ids.flatten()):
                    img_drawn = cv2.drawFrameAxes(img_drawn, camera_matrix, dist_coeff, rvecs[i], tvecs[i], 0.01)
                    x, y, _ = tvecs[i][0]
                    rvec = rvecs[i][0]
                    R, _ = cv2.Rodrigues(rvec)
                    yaw = np.arctan2(R[1,0], R[0,0])
                    global_data.marker_positions[marker_id] = (x, y , yaw)  

            emit_image = cv2.resize(img_drawn, dsize=(1280, 720), interpolation=cv2.INTER_CUBIC)

            h, w, ch = emit_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(emit_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.change_pixmap_signal.emit(qt_image)

        cap.release()

    def stop(self):
        self._running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

