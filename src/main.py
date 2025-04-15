import sys
import cv2
import cv2.aruco as aruco
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton

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
        npz_file = np.load("/home/ramy-mawal/Desktop/Projects/rc-robot-ui/calibration_data.npz") 
        camera_matrix = npz_file['camera_matrix']
        dist_coeff = npz_file['dist_coeffs']
        arucoParams = cv2.aruco.DetectorParameters()
        marker_length = 0.015 

        print(npz_file.files)
        while self._running:  
            ret, frame = cap.read()
            if not ret:
                break  

            undistorted_frame = frame # cv2.undistort(frame, cameraMatrix=camera_matrix, distCoeffs=dist_coeff)

            gray = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = aruco.detectMarkers(gray, self.dictionary, parameters=arucoParams)
            rgb_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2RGB)
            img_drawn = aruco.drawDetectedMarkers(rgb_frame.copy(), corners, ids)

            if ids is not None:
                rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeff)
                for i in range(len(ids)):
                    img_drawn = cv2.drawFrameAxes(img_drawn, camera_matrix, dist_coeff, rvec[i], tvec[i], 0.01)            

            h, w, ch = img_drawn.shape
            bytes_per_line = ch * w
            qt_image = QImage(img_drawn.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            self.change_pixmap_signal.emit(qt_image)
        
        cap.release()  # Release the camera when the loop ends

    def stop(self):
        """Stop the thread by setting the running flag to False."""
        self._running = False

    def close(self):
        """Handle the thread close event to properly terminate the thread."""
        self.stop()
        self.wait()  


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV Video Stream with QThread")
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        
        self.count = 0
        self.text_label = QLabel("I Was not clicked yet!")
        self.button = QPushButton("Increment Count")
        self.button.clicked.connect(lambda: self.update_label())

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.text_label)
        layout.addWidget(self.button)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        
        # Create and start the video thread
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
    
    def update_label(self):
        self.count += 1
        self.text_label.setText("I was clicked {} times!".format(self.count))

    @pyqtSlot(QImage)
    def update_image(self, qt_image):
        """Receive QImage from the thread and update the label."""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))
    
    def closeEvent(self, event):
        """Handle the window close event to properly terminate the thread."""
        self.thread.stop()
        self.thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
