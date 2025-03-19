import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QTextEdit, QLabel, QMessageBox
)
import serial
import serial.tools.list_ports


class SerialGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32 JSON Serial Sender")
        self.serial_port = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()

        # Dropdown for available serial ports
        self.port_dropdown = QComboBox()
        self.refresh_ports()  # Populate dropdown
        layout.addWidget(QLabel("Select Serial Port:"))
        layout.addWidget(self.port_dropdown)

        # Button to connect
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_serial)
        layout.addWidget(self.connect_btn)

        # Button to send JSON data
        self.send_btn = QPushButton("Send Data")
        self.send_btn.clicked.connect(self.send_data)
        self.send_btn.setEnabled(False)
        layout.addWidget(self.send_btn)

        # Text area for status/log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def refresh_ports(self):
        """Refresh the dropdown with currently available serial ports."""
        self.port_dropdown.clear()
        ports = serial.tools.list_ports.comports()
        for port_info in ports:
            # Use the device name for connection
            self.port_dropdown.addItem(f"{port_info.device} - {port_info.description}", port_info.device)

    def connect_serial(self):
        """Connect to the serial port selected in the dropdown."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        port = self.port_dropdown.currentData()
        try:
            # Adjust baud rate and timeout as needed
            self.serial_port = serial.Serial(port, baudrate=115200, timeout=1)
            self.log_text.append(f"Connected to {port}")
            self.send_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Could not open port {port}:\n{e}")
            self.log_text.append(f"Error connecting to {port}: {e}")
            self.send_btn.setEnabled(False)

    def send_data(self):
        """Send a predefined JSON message through the serial port."""
        if not self.serial_port or not self.serial_port.is_open:
            self.log_text.append("Serial port is not connected!")
            return

        # Define a predefined data structure
        data = {"command": "start", "value": 42}
        # Convert to JSON and add newline as a message delimiter
        message = json.dumps(data) + "\n"
        try:
            self.serial_port.write(message.encode('utf-8'))
            self.log_text.append(f"Sent: {message}")
        except Exception as e:
            self.log_text.append(f"Error sending data: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SerialGUI()
    window.show()
    sys.exit(app.exec())
