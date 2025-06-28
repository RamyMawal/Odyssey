
from dataclasses import dataclass

from enums.configurations.command_type import CommandType
from enums.configurations.formation_shape import FormationShape
from models.vectors import MovementVector


@dataclass
class ConfigurationMessage:
    command: CommandType
    data: FormationShape | MovementVector
    pass
