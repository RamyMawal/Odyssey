import sys
import serial as pySerial
from data_sender import SendDataTask
from capture import VideoThread
from PyQt6.QtCore import pyqtSlot, QThreadPool
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QComboBox,
    QTextEdit, QVBoxLayout, QHBoxLayout, QWidget
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV Video Stream with QThread")
        self.serial_port = None
        
        self.image_label = QLabel()

        # --- Layouts ---
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.image_label)

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

        serial_controls = QHBoxLayout()
        serial_controls.addWidget(self.port_dropdown)
        serial_controls.addWidget(self.refresh_btn)
        serial_controls.addWidget(self.connect_btn)
        serial_controls.addWidget(self.send_btn)

        log_widget = QHBoxLayout()
        log_widget.addWidget(self.serial_log)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addLayout(video_layout)
        layout.addLayout(serial_controls)
        layout.addLayout(log_widget)
        self.setLayout(layout)
        
        # Create and start the video thread
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
    
    def refresh_serial_ports(self):
        """Discover available serial ports and populate the dropdown."""
        current_ports = {self.port_dropdown.itemData(i) for i in range(self.port_dropdown.count())}
        new_ports = {port.device for port in pySerial.tools.list_ports.comports()}

        if current_ports != new_ports:
            self.port_dropdown.clear()
            for port_info in pySerial.tools.list_ports.comports():
                if port_info.description != "n/a":
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
        """Send a predefined ASCII message via the serial port."""
        if not self.serial_port or not self.serial_port.is_open:
            self.serial_log.append("Serial port not connected!")
            return

        self.serial_log.append("Sending data...")
        task = SendDataTask(
            self.serial_port.portstr,
            115200,
            x = 0,
            y = 0,
            rot = 90.0,
            xt = 1.0,
            yt = 1.0
        )
        QThreadPool.globalInstance().start(task)
        self.serial_log.append("Data sent successfully!")

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
