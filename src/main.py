import logging
import math
import sys

from PyQt6.QtCore import pyqtSlot, Qt

from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import serial
import serial.tools.list_ports

from capture.frame_analyzer import FrameAnalyzer
from capture.observer import ObserverThread, get_available_cameras
from collision_avoidance import CollisionAvoidanceLayer
from configuration_manager import ConfigurationManager
from enums.configurations.command_type import CommandType
from enums.configurations.formation_shape import FormationShape
from formation_dispatcher import FormationDispatcher
from global_supervisor import GlobalSupervisor
from link_controller import LinkControllerThread
from models.configuration_message import ConfigurationMessage
from models.vectors import Pose2D
from position_updater import PositionUpdater
from stores.controller_context import ControllerContext

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Odyssey Formation Control")
        self.serial_port = None
        self.observer_thread = None

        self.image_label = QLabel()

        # --- Layouts ---
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Camera Section ---
        self.camera_dropdown = QComboBox()

        self.refresh_camera_btn = QPushButton("Refresh Cameras")
        self.refresh_camera_btn.clicked.connect(self.refresh_cameras)

        self.connect_camera_btn = QPushButton("Start Camera")
        self.connect_camera_btn.clicked.connect(self.start_camera)

        camera_controls = QHBoxLayout()
        camera_controls.addWidget(QLabel("Camera:"))
        camera_controls.addWidget(self.camera_dropdown)
        camera_controls.addWidget(self.refresh_camera_btn)
        camera_controls.addWidget(self.connect_camera_btn)

        # --- Serial Port Section ---
        self.port_dropdown = QComboBox()
        self.refresh_serial_ports()

        self.refresh_btn = QPushButton("Refresh Ports")
        self.refresh_btn.clicked.connect(self.refresh_serial_ports)

        self.connect_btn = QPushButton("Connect Serial")
        self.connect_btn.clicked.connect(self.connect_serial)

        self.serial_log = QTextEdit()
        self.serial_log.setReadOnly(True)

        self.formation_log = QTextEdit()
        self.formation_log.setReadOnly(True)
        self.formation_log.setPlaceholderText("Formation debug log...")
        self._prev_link_poses = None

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

        self.safety_stop_checkbox = QCheckBox("Stop on lost detection")
        self.safety_stop_checkbox.setChecked(False)
        self.safety_stop_checkbox.stateChanged.connect(self.on_safety_stop_changed)

        self.apf_checkbox = QCheckBox("APF Collision Avoidance")
        self.apf_checkbox.setChecked(True)
        self.apf_checkbox.stateChanged.connect(self.on_apf_changed)

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
        command_layout.addWidget(self.safety_stop_checkbox)
        command_layout.addWidget(self.apf_checkbox)

        # --- Log Layout ---
        log_widget = QHBoxLayout()
        log_widget.addWidget(self.serial_log)
        log_widget.addWidget(self.formation_log)

        # --- Main Layout ---
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addLayout(video_layout)
        left_layout.addLayout(camera_controls)
        left_layout.addLayout(serial_controls)
        left_layout.addLayout(log_widget)
        left_layout.addLayout(command_layout)
        main_layout.addLayout(left_layout)
        self.setLayout(main_layout)

        self.initialize_threads()

    def initialize_threads(self):
        self.context = ControllerContext()

        # Auto-select first available camera
        cameras = get_available_cameras()
        camera_index = cameras[0][0] if cameras else 0

        self.observer_thread = ObserverThread(self.context, camera_index)
        self.observer_thread.change_pixmap_signal.connect(self.update_image)
        self.observer_thread.start()

        # Populate camera dropdown and select current camera
        self.refresh_cameras()
        for i in range(self.camera_dropdown.count()):
            if self.camera_dropdown.itemData(i) == camera_index:
                self.camera_dropdown.setCurrentIndex(i)
                break

        self.analyzer_thread = FrameAnalyzer(self.observer_thread, self.context)
        self.analyzer_thread.start()

        self.configuration_manager = ConfigurationManager()

        self.collision_avoidance_thread = CollisionAvoidanceLayer(self.context)
        self.collision_avoidance_thread.start()

        self.position_thread = PositionUpdater(self.context)
        self.position_thread.start()

        self.global_supervisor_thread = GlobalSupervisor(
            self.context, self.configuration_manager
        )
        self.global_supervisor_thread.start()

        self.formation_dispatcher_thread = FormationDispatcher(self.context)
        self.formation_dispatcher_thread.poses_computed.connect(self.on_poses_computed)
        self.formation_dispatcher_thread.start()

        self.link_threads = [LinkControllerThread(i, self.context) for i in range(4)]
        for thread in self.link_threads:
            thread.start()

    def refresh_cameras(self):
        """Discover available cameras and populate the dropdown."""
        self.camera_dropdown.clear()
        for index, description in get_available_cameras():
            self.camera_dropdown.addItem(description, index)

    def start_camera(self):
        """Start the camera with the selected index."""
        camera_index = self.camera_dropdown.currentData()
        if camera_index is None:
            self.serial_log.append("No camera selected")
            return

        # Stop existing observer if running
        if self.observer_thread and self.observer_thread.isRunning():
            self.observer_thread.stop()
            self.observer_thread.wait()

        # Start new observer with selected camera
        self.observer_thread = ObserverThread(self.context, camera_index)
        self.observer_thread.change_pixmap_signal.connect(self.update_image)
        self.observer_thread.start()
        self.serial_log.append(f"Started camera {camera_index}")

    def handle_send_command(self):
        message: ConfigurationMessage = ConfigurationMessage(
            CommandType.CONFIGURE, FormationShape.LINE, Pose2D(0, 0, 0)
        )
        command: CommandType = self.command_dropdown.currentData()
        formation: FormationShape = self.formation_dropdown.currentData()
        message.command = command
        message.shape = formation
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            theta = float(self.theta_input.text())
            theta = math.radians(theta)
            mv = Pose2D(x, y, theta)
            message.target = mv
        except ValueError:
            self.serial_log.append("Invalid input for x, y, or theta.")
            message.target = Pose2D(0, 0, 0)
        self.configuration_manager.update_configuration(message)

    def refresh_serial_ports(self):
        """Discover available serial ports and populate the dropdown."""

        self.port_dropdown.clear()
        for port_info in serial.tools.list_ports.comports():
            if port_info.description != "n/a":
                self.port_dropdown.addItem(
                    f"{port_info.device} - {port_info.description}", port_info.device
                )

    def connect_serial(self):
        """Connect to the serial port selected from the dropdown."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        port = self.port_dropdown.currentData()
        self.context.port = port
        try:
            self.serial_port = serial.Serial(port, baudrate=115200, timeout=1)
            self.serial_log.append(f"Connected to serial port: {port}")
        except Exception as e:
            self.serial_log.append(f"Error connecting to {port}: {e}")

    def on_safety_stop_changed(self, state):
        """Toggle safety stop feature that stops robots when detection is lost."""
        self.context.safety_stop_enabled = (state == Qt.CheckState.Checked.value)

    def on_apf_changed(self, state):
        """Toggle APF collision avoidance feature."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.collision_avoidance_thread.set_enabled(enabled)

    def on_poses_computed(self, origin_pos, origin_theta, joints, link_poses):
        """Log formation poses when they change."""
        # Check if values changed
        if link_poses == self._prev_link_poses:
            return
        self._prev_link_poses = link_poses

        # Get current shape name
        config = self.configuration_manager.get_current_config()
        _, formation, _ = config
        shape_name = formation.name if formation else "UNKNOWN"

        # Format log entry
        log = "=== Formation Update ===\n"
        log += f"Origin: ({origin_pos[0]:.3f}, {origin_pos[1]:.3f}) θ={math.degrees(origin_theta):.1f}°\n"
        log += f"Shape: {shape_name}\n"
        log += f"Joints: [{', '.join(f'{math.degrees(j):.1f}°' for j in joints)}]\n\n"

        for i, (x, y, theta) in enumerate(link_poses):
            log += f"Link {i} → Robot {i}: ({x:.3f}, {y:.3f}) θ={math.degrees(theta):.1f}°\n"

        log += "=" * 24 + "\n"

        self.formation_log.append(log)

    @pyqtSlot(QImage)
    def update_image(self, qt_image):
        """Receive QImage from the thread and update the label."""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, a0: any) -> None:
        """Handle the window close event to properly terminate the thread."""
        if self.observer_thread:
            self.observer_thread.stop()
        self.analyzer_thread.stop()
        self.collision_avoidance_thread.stop()
        self.position_thread.stop()
        self.global_supervisor_thread.stop()
        self.formation_dispatcher_thread.stop()
        for thread in self.link_threads:
            thread.stop()
        if self.observer_thread:
            self.observer_thread.wait()
        self.analyzer_thread.wait()
        self.collision_avoidance_thread.wait()
        self.position_thread.wait()
        self.global_supervisor_thread.wait()
        self.formation_dispatcher_thread.wait()
        for thread in self.link_threads:
            thread.wait()
        a0.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
