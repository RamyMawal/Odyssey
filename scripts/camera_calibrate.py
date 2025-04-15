import os
import cv2.aruco as aruco
import sys
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton

# ------------------------------
# ENTER YOUR REQUIREMENTS HERE:
ARUCO_DICT = cv2.aruco.DICT_6X6_250
SQUARES_VERTICALLY = 7
SQUARES_HORIZONTALLY = 5
SQUARE_LENGTH = 0.03
MARKER_LENGTH = 0.015
# ...
PATH_TO_YOUR_IMAGES = './calibration_images'
# ------------------------------


class VideoThread(QThread):
    # Signal that will send a QImage to update the GUI
    change_pixmap_signal = pyqtSignal(QImage)

    def calibrate_and_save_parameters(self):
        # Define the aruco dictionary and charuco board
        dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
        board = cv2.aruco.CharucoBoard((SQUARES_VERTICALLY, SQUARES_HORIZONTALLY), SQUARE_LENGTH, MARKER_LENGTH, dictionary)
        params = cv2.aruco.DetectorParameters()

        # Load PNG images from folder
        image_files = [os.path.join(PATH_TO_YOUR_IMAGES, f) for f in os.listdir(PATH_TO_YOUR_IMAGES) if f.endswith(".png")]
        image_files.sort()  # Ensure files are in order

        all_charuco_corners = []
        all_charuco_ids = []
        mtx = any
        dist = any

        for image_file in image_files:
            image = cv2.imread(image_file)
            image_copy = image.copy()
            marker_corners, marker_ids, _ = cv2.aruco.detectMarkers(image, dictionary, parameters=params)
            
            # If at least one marker is detected
            if len(marker_ids) > 0:
                cv2.aruco.drawDetectedMarkers(image_copy, marker_corners, marker_ids)
                charuco_retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(marker_corners, marker_ids, image, board)
                if charuco_retval:
                    all_charuco_corners.append(charuco_corners)
                    all_charuco_ids.append(charuco_ids)

        # Calibrate camera
        
            retval, mtx, dist, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(all_charuco_corners, all_charuco_ids, board, image.shape[:2], None, None)

        # # Save calibration data
        # np.save('camera_matrix.npy', camera_matrix)
        # np.save('dist_coeffs.npy', dist_coeffs)

        for image_file in image_files:
            image = cv2.imread(image_file)
            image_copy = image.copy()
            h,  w = image.shape[:2]
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))

            dst = cv2.undistort(image, mtx, dist, None, newcameramtx)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


    
    def run(self):
        # Define the aruco dictionary and charuco board
        dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
        board = cv2.aruco.CharucoBoard((SQUARES_VERTICALLY, SQUARES_HORIZONTALLY), SQUARE_LENGTH, MARKER_LENGTH, dictionary)
        params = cv2.aruco.DetectorParameters()

        # Load PNG images from folder
        image_files = [os.path.join(PATH_TO_YOUR_IMAGES, f) for f in os.listdir(PATH_TO_YOUR_IMAGES) if f.endswith(".png")]
        image_files.sort()  # Ensure files are in order

        all_charuco_corners = []
        all_charuco_ids = []
        mtx = any
        dist = any

        first = True
        for im in image_files:
            img_gray = cv2.cvtColor(im,cv2.COLOR_RGB2GRAY)
            corners, ids, rejectedImgPoints = aruco.detectMarkers(img_gray, aruco_dict, parameters=arucoParams)
            if first == True:
                corners_list = corners
                id_list = ids
                first = False
            else:
                corners_list = np.vstack((corners_list, corners))
                id_list = np.vstack((id_list,ids))
            counter.append(len(ids))
        print('Found {} unique markers'.format(np.unique(ids)))

        counter = np.array(counter)
        print ("Calibrating camera .... Please wait...")
        #mat = np.zeros((3,3), float)

        ret, mtx, dist, rvecs, tvecs = aruco.calibrateCameraAruco(corners_list, id_list, counter, board, img_gray.shape, None, None )

        print("Camera matrix is \n", mtx, "distortion coefficients : \n", dist)

        # # Save calibration data
        np.save('camera_matrix.npy', mtx)
        np.save('dist_coeffs.npy', dist)


        # Open the default camera
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # Stop if frame is not captured
            
            # h,  w = frame.shape[:2]
            # newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))

            # dst = cv2.undistort(frame, mtx, dist, None, newcameramtx)

            # Place for heavy processing (e.g., filtering, object detection)
            # For demonstration, we just convert BGR (OpenCV default) to RGB.
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert the frame (a NumPy array) to QImage:
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Emit the signal with the new QImage
            self.change_pixmap_signal.emit(qt_image)
        cap.release()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV Video Stream with QThread")
        
        # Create a label to display the video
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
        self.thread.quit()
        self.thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())