import sys
import serial
import serial.tools.list_ports
import cv2
from cv2.typing import MatLike
from PyQt6.QtCore import pyqtSlot, QThreadPool, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QComboBox,
    QTextEdit, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit, QListWidget, QListWidgetItem, QFrame
)
from capture.frame_analyzer import FrameAnalyzer
from configuration_manager import ConfigurationManager
from enums.configurations.command_type import CommandType
from enums.configurations.formation_shape import FormationShape
from models.configuration_message import ConfigurationMessage
from models.vectors import MovementVector
from stores.controller_context import ControllerContext
import stores.global_data as global_data
from position_updater import PositionUpdater
from capture.observer import ObserverThread
from global_supervisor import GlobalSupervisor


class MainWindow(QWidget):
    update_configuration_signal = pyqtSignal(ConfigurationMessage)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Odyssey Formation Control")
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

        # --- Command/Formation Section ---
        self.command_dropdown = QComboBox()
        for cmd in CommandType:
            self.command_dropdown.addItem(cmd.name, cmd)

        self.formation_dropdown = QComboBox()
        for form in FormationShape:
            self.formation_dropdown.addItem(form.name, form)

        self.x_input = QLineEdit()
        self.x_input.setPlaceholderText("X")
        self.y_input = QLineEdit()
        self.y_input.setPlaceholderText("Y")
        self.theta_input = QLineEdit()
        self.theta_input.setPlaceholderText("Theta")

        self.push_config_btn = QPushButton("Send Command")
        self.push_config_btn.clicked.connect(self.handle_send_command)

        # Layout for command controls
        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel("Command Type:"))
        command_layout.addWidget(self.command_dropdown)
        command_layout.addWidget(QLabel("Formation:"))
        command_layout.addWidget(self.formation_dropdown)
        command_layout.addWidget(QLabel("Target X:"))
        command_layout.addWidget(self.x_input)
        command_layout.addWidget(QLabel("Target Y:"))
        command_layout.addWidget(self.y_input)
        command_layout.addWidget(QLabel("Target Theta:"))
        command_layout.addWidget(self.theta_input)
        command_layout.addWidget(self.push_config_btn)

        # --- Log Layout ---
        log_widget = QHBoxLayout()
        log_widget.addWidget(self.serial_log)

        # --- Main Layout ---
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addLayout(video_layout)
        left_layout.addLayout(serial_controls)
        left_layout.addLayout(log_widget)
        left_layout.addLayout(command_layout)
        main_layout.addLayout(left_layout)
        self.setLayout(main_layout)

        self.initialize_threads()



    def initialize_threads(self):
        self.context = ControllerContext()

        self.observer_thread = ObserverThread(self.context)
        self.observer_thread.change_pixmap_signal.connect(self.update_image)
        self.observer_thread.start()

        self.analyzer_thread = FrameAnalyzer(self.observer_thread, self.context)
        # self.analyzer_thread.change_pixmap_signal.connect(self.update_image)
        self.analyzer_thread.start()

        self.configuration_manager_thread = ConfigurationManager(self.context)

        self.position_thread = PositionUpdater(self.context)
        self.position_thread.start()

        self.global_supervisor_thread = GlobalSupervisor(self.context)
        self.global_supervisor_thread.start()


    def handle_send_command(self):
        message:ConfigurationMessage = ConfigurationMessage()
        command: CommandType = self.command_dropdown.currentData()
        if command == CommandType.CONFIGURE:
            formation: FormationShape = self.formation_dropdown.currentData()
            message.command = command
            message.data = formation
        elif command == CommandType.MOVE:
            try:
                x = float(self.x_input.text())
                y = float(self.y_input.text())
                theta = float(self.theta_input.text())
                mv = MovementVector(x, y, theta)
                message.command = command
                message.data = mv
            except ValueError:
                self.serial_log.append("Invalid input for x, y, or theta.")
        self.update_configuration_signal.emit(message)

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

    # @pyqtSlot(object)
    # def update_image(self, frame: MatLike):
    #     emit_image = cv2.resize(frame, dsize=(1280, 720), interpolation=cv2.INTER_CUBIC)

    #     h, w, ch = emit_image.shape
    #     bytes_per_line = ch * w
    #     qt_image = QImage(emit_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    #     self.image_label.setPixmap(QPixmap.fromImage(qt_image))
    
    def closeEvent(self, event):
        """Handle the window close event to properly terminate the thread."""
        self.observer_thread.stop()
        self.analyzer_thread.stop()
        self.position_thread.stop()
        self.global_supervisor_thread.stop()
        self.observer_thread.wait()
        self.analyzer_thread.wait()
        self.position_thread.wait()
        self.global_supervisor_thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
