import sys
import cv2
import json
import serial as pySerial
import serial.tools.list_ports
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QComboBox,
    QTextEdit, QVBoxLayout, QHBoxLayout, QWidget
)

class VideoThread(QThread):
    # Signal to send a QImage to the main GUI
    change_pixmap_signal = pyqtSignal(QImage)
    
    def run(self):
        cap = cv2.VideoCapture(2)
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # Exit loop if frame is not captured
            # Heavy processing can be inserted here
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.change_pixmap_signal.emit(qt_image)
        cap.release()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video & Serial Interface")
        self.serial_port = None
        
        # --- Video Section ---
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        
        # --- Serial Port Section ---
        self.port_dropdown = QComboBox()
        self.refresh_serial_ports()

        self.refresh_btn = QPushButton("Refresh Ports")
        self.refresh_btn.clicked.connect(self.refresh_serial_ports)
        
        self.connect_btn = QPushButton("Connect Serial")
        self.connect_btn.clicked.connect(self.connect_serial)
        
        self.send_btn = QPushButton("Send Data")
        self.send_btn.clicked.connect(self.send_data)
        self.send_btn.setEnabled(False)
        
        self.serial_log = QTextEdit()
        self.serial_log.setReadOnly(True)
        
        # --- Layouts ---
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.image_label)
        
        serial_controls = QHBoxLayout()
        serial_controls.addWidget(self.port_dropdown)
        serial_controls.addWidget(self.refresh_btn)
        serial_controls.addWidget(self.connect_btn)
        serial_controls.addWidget(self.send_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(video_layout)
        main_layout.addLayout(serial_controls)
        main_layout.addWidget(self.serial_log)
        
        self.setLayout(main_layout)
        
        # --- Start Video Thread ---
        self.video_thread = VideoThread()
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()
    
    def refresh_serial_ports(self):
        """Discover available serial ports and populate the dropdown."""
        self.port_dropdown.clear()
        ports = pySerial.tools.list_ports.comports()
        for port_info in ports:
            # Each item shows the device and description; we use the device name as underlying data.
            self.port_dropdown.addItem(f"{port_info.device} - {port_info.description}", port_info.device)
    
    def connect_serial(self):
        """Connect to the serial port selected from the dropdown."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        port = self.port_dropdown.currentData()
        try:
            self.serial_port = pySerial.Serial(port, baudrate=115200, timeout=1)
            self.serial_log.append(f"Connected to serial port: {port}")
            self.send_btn.setEnabled(True)
        except Exception as e:
            self.serial_log.append(f"Error connecting to {port}: {e}")
            self.send_btn.setEnabled(False)
    
    def send_data(self):
        """Send a predefined JSON message via the serial port."""
        if not self.serial_port or not self.serial_port.is_open:
            self.serial_log.append("Serial port not connected!")
            return
        
        # Define a predefined data structure (example)
        data = {"command": "start", "value": 42}
        message = json.dumps(data) + "\n"  # Add newline as a message delimiter
        try:
            self.serial_port.write(message.encode('utf-8'))
            self.serial_log.append(f"Sent: {message}")
        except Exception as e:
            self.serial_log.append(f"Error sending data: {e}")
    
    @pyqtSlot(QImage)
    def update_image(self, qt_image):
        """Update the video display label with the new frame."""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))
    
    def closeEvent(self, event):
        """Clean up threads and serial connection on close."""
        self.video_thread.quit()
        self.video_thread.wait()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
