from threading import Lock
from enums.configurations.command_type import CommandType
from enums.configurations.formation_shape import FormationShape
from models.configuration_message import ConfigurationMessage
from models.vectors import Pose2D


class ConfigurationManager:
    _lock: Lock
    _current_command: CommandType
    _current_formation: FormationShape
    _target: Pose2D

    def __init__(self):
        self._lock = Lock()
        self._current_command = CommandType.CONFIGURE
        self._current_formation = FormationShape.LINE
        self._target = Pose2D(0, 0, 0)

    def update_configuration(self, message: ConfigurationMessage):
        print(f"Updating configuration: {message}")
        with self._lock:
            self._current_command = message.command
            self._current_formation = message.shape
            self._target = message.target

    def get_current_config(self):
        with self._lock:
            return self._current_command, self._current_formation, self._target
