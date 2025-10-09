from dataclasses import dataclass

from enums.configurations.command_type import CommandType
from enums.configurations.formation_shape import FormationShape
from models.vectors import Pose2D


@dataclass
class ConfigurationMessage:
    command: CommandType
    shape: FormationShape
    target: Pose2D
