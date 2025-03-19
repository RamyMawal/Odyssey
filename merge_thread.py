import sys
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton

class VideoThread(QThread):
    # Signal that will send a QImage to update the GUI
    change_pixmap_signal = pyqtSignal(QImage)
    
    def run(self):
        # Open the default camera
        cap = cv2.VideoCapture(2)
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # Stop if frame is not captured
            
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
