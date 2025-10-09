import math
import time
from configuration_manager import ConfigurationManager
from models.vectors import Pose2D
from stores.controller_context import ControllerContext
from enums.configurations.formation_shape import FormationShape
from enums.configurations.command_type import CommandType
from PyQt6.QtCore import QThread
from stores.formation_state_store import FormationDescriptor


class GlobalSupervisor(QThread):
    current_formation: FormationDescriptor

    def __init__(self, context: ControllerContext, config_manager: ConfigurationManager):
        super().__init__()
        self.context = context
        self.config_manager = config_manager
        self._running = True        

    def stop(self):
        self._running = False

    def run(self):

        while(self._running):
            _, shape, target = self.config_manager.get_current_config()

            joints = self.get_joint_angles(shape)

            r_d, q_d = self.get_coordinates(target)

            self.current_formation = FormationDescriptor(r_d, q_d, joints)

            # print(f"Global Supervisor: {self.current_formation}")

            self.context.formation_state_store.update(self.current_formation)
            time.sleep(0.1)


    def get_coordinates(self, target: Pose2D) -> tuple[tuple[float,float],float]:
        return ((target.x, target.y), target.theta)
    
    def get_joint_angles(self, shape: FormationShape) -> list[float]:
        match shape:
            case FormationShape.LINE :
                return [0,0]
            case FormationShape.SQUARE:
                return [math.radians(90),math.radians(90)]
            case FormationShape.TRIANGLE:
                return [math.radians(60), math.radians(30)]
            case FormationShape.ARROW:
                return [math.radians(120), math.radians(40)]
                
