import sys
import cv2
import json
import serial as pySerial
import serial.tools.list_ports
import cv2.aruco as aruco
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QComboBox,
    QTextEdit, QVBoxLayout, QHBoxLayout, QWidget
)

calibration_data_path = "/home/ramy-mawal/Desktop/Projects/rc-robot-ui/calibration_data_latest.npz"

class VideoThread(QThread):
    # Signal that will send a QImage to update the GUI
    change_pixmap_signal = pyqtSignal(QImage)
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)

    def __init__(self):
        super().__init__()
        self._running = True  # Add a flag to control the thread's execution

    def run(self):
        # Open the default camera
        cap = cv2.VideoCapture(2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        npz_file = np.load(calibration_data_path) 
        camera_matrix = npz_file['camera_matrix']
        dist_coeff = npz_file['dist_coeffs']
        arucoParams = cv2.aruco.DetectorParameters()
        marker_length = 0.015 # TODO: ADJUST THIS TO CORRECT SIZE

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
                print(f"rvec: {rvec}")
                print(f"tvec: {tvec}")
                for i in range(len(ids)):
                    img_drawn = cv2.drawFrameAxes(img_drawn, camera_matrix, dist_coeff, rvec[i], tvec[i], 0.01)            

            h, w, ch = img_drawn.shape
            bytes_per_line = ch * w
            qt_image = QImage(img_drawn.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            self.change_pixmap_signal.emit(qt_image)
        
        cap.release()  # Release the camera when the loop ends

    def send_data_to_esp(port: str, baudrate: int, x: float, y: float, rot: float, xt: float, yt: float):
        try:
                # Open serial port
            with serial.Serial(port, baudrate, timeout=1) as ser:
                # Format the message
                message = f"{x:.3f},{y:.3f},{rot:.3f},{xt:.3f},{yt:.3f}\n"
                # Send as bytes
                ser.write(message.encode('utf-8'))
                print(f"Sent: {message.strip()}")

        except serial.SerialException as e:
            print(f"Serial error: {e}")
    

    def stop(self):
        """Stop the thread and release the camera."""
        self._running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

    def close(self):
        """Handle the thread close event to properly terminate the thread."""
        self.stop()
        self.wait()  

