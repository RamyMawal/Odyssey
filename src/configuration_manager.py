from threading import Lock
import time
from enums.configurations.command_type import CommandType
from enums.configurations.formation_shape import FormationShape
from models.configuration_message import ConfigurationMessage
from models.vectors import Pose2D
from PyQt6.QtCore import QThread, pyqtSlot

class ConfigurationManager(QThread):
    _lock:Lock
    _current_command: CommandType
    _current_formation: FormationShape
    _target: Pose2D

    def __init__(self):
        self._running = True
        self._lock = Lock()
        self._current_command = CommandType.CONFIGURE
        self._current_formation = FormationShape.LINE
        self._target = Pose2D(0,0,0)

    def run(self):
        time.sleep(5)

    def stop(self):
        self._running = False


    def update_configuration(self, message: ConfigurationMessage):
        with self._lock:
            self._current_command = message.command
            self._current_formation = message.shape
            self._target = message.target


    def get_current_config(self):
        return self._current_command, self._current_formation, self._target
                