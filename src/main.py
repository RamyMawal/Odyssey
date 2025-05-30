import sys
import serial
import serial.tools.list_ports
import global_data
from position_updater import PositionUpdater
from capture import VideoThread
from PyQt6.QtCore import pyqtSlot, QThreadPool
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QComboBox,
    QTextEdit, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit
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
        
        self.serial_log = QTextEdit()
        self.serial_log.setReadOnly(True)

        serial_controls = QHBoxLayout()
        serial_controls.addWidget(self.port_dropdown)
        serial_controls.addWidget(self.refresh_btn)
        serial_controls.addWidget(self.connect_btn)

        input_layout = QHBoxLayout()
        self.marker_id_input = QLineEdit()
        self.marker_id_input.setPlaceholderText("Marker ID")
        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        self.update_btn = QPushButton("Update Position")
        self.update_btn.clicked.connect(self.update_target_position)
        input_layout.addWidget(QLabel("Marker ID:"))
        input_layout.addWidget(self.marker_id_input)
        input_layout.addWidget(QLabel("X:"))
        input_layout.addWidget(self.x_input)
        input_layout.addWidget(QLabel("Y:"))
        input_layout.addWidget(self.y_input)
        input_layout.addWidget(self.update_btn)

        log_widget = QHBoxLayout()
        log_widget.addWidget(self.serial_log)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addLayout(video_layout)
        layout.addLayout(serial_controls)
        layout.addLayout(input_layout)
        layout.addLayout(log_widget)
        self.setLayout(layout)
        
        # Create and start the video thread
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

        self.position_thread = PositionUpdater()
        QThreadPool.globalInstance().start(self.position_thread)

    
    def refresh_serial_ports(self):
        """Discover available serial ports and populate the dropdown."""

        self.port_dropdown.clear()
        for port_info in serial.tools.list_ports.comports():
            if port_info.description != "n/a":
                self.port_dropdown.addItem(f"{port_info.device} - {port_info.description}", port_info.device)
    
    def connect_serial(self):
        """Connect to the serial port selected from the dropdown."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        port = self.port_dropdown.currentData()
        global_data.port = port
        try:
            self.serial_port = serial.Serial(port, baudrate=115200, timeout=1)
            self.serial_log.append(f"Connected to serial port: {port}")
        except Exception as e:
            self.serial_log.append(f"Error connecting to {port}: {e}")

    def update_target_position(self):
        """Update the target position for the selected marker."""
        try:
            marker_id = int(self.marker_id_input.text())
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            global_data.target_positions[marker_id] = (x, y)
        except ValueError as e:
            self.serial_log.append(f"Error: {e}")

    @pyqtSlot(QImage)
    def update_image(self, qt_image):
        """Receive QImage from the thread and update the label."""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))
    
    def closeEvent(self, event):
        """Handle the window close event to properly terminate the thread."""
        self.thread.stop()
        self.thread.wait()
        self.position_thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
