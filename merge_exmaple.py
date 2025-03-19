import sys
import cv2
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton

class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV + PyQt Video Stream")
        self.count = 0
        self.video_label = QLabel()
        self.text_label = QLabel("I Was not clicked yet!")
        self.button = QPushButton("Increment Count")
        self.button.clicked.connect(lambda: self.update_label())
        layout = QVBoxLayout()
        layout.addWidget(self.text_label)
        layout.addWidget(self.button)
        layout.addWidget(self.video_label)
        self.setLayout(layout)
        
        # Open the camera
        self.cap = cv2.VideoCapture(2)
        
        # Create a timer to fetch frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # roughly 30 frames per second

    def update_label(self):
        self.count += 1
        self.text_label.setText("I was clicked {} times!".format(self.count))

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Convert the frame to RGB format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            # Convert the image to QImage
            qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            # Set the pixmap on the label
            self.video_label.setPixmap(QPixmap.fromImage(qimg))

    def closeEvent(self, event):
        # Release the video capture when the widget is closed
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_widget = VideoWidget()
    video_widget.show()
    sys.exit(app.exec())
