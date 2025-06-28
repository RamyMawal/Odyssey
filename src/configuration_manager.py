import math
from threading import Lock
from enums.configurations.command_type import CommandType
from enums.configurations.formation_shape import FormationShape
from models.configuration_message import ConfigurationMessage
from models.target_joint import TargetJoint
from models.vectors import MovementVector
from stores.controller_context import ControllerContext
from stores.formation_state_store import FormationDescriptor
from PyQt6.QtCore import QThread, pyqtSlot

class ConfigurationManager(QThread):
    _running:bool
    _lock:Lock
    _current_command: CommandType
    _current_formation: FormationShape
    _movement_target: MovementVector

    def __init__(self, context: ControllerContext):
        self.context = context
        self._running = True
        self._lock = Lock()


    def __run__(self):
        while(self._running):
            with self._lock:
                self.generate_configuration()


    @pyqtSlot(ConfigurationMessage)
    def update_configuration(self, message: ConfigurationMessage):
        with self._lock:
            self._current_command = message.command
            match message.command:
                case CommandType.CONFIGURE:
                    self._current_formation = message.data
                case CommandType.MOVE:
                    self._movement_target = message.data

                
    def generate_configuration(self, joints: list[TargetJoint]):
        joints.sort(key=lambda x: x.id)
        joint_angles = []

        for i in range(1,len(joints) - 1):
            if(i + 1 >= len(joints)):
                break

            A = joints[i - 1]
            B = joints[i]
            C = joints[i + 1]

            joint_angles.append(self.angle_between_points(A,B,C))

        discriptor = FormationDescriptor(r_d= (0,0), q_d= 0, theta_d= joint_angles)

        self.context.formation_state_store.update(discriptor)

    def angle_between_points(A: tuple[float,float], B:tuple[float,float], C:tuple[float,float]):
            # Vectors BA and BC
        BA = (A[0] - B[0], A[1] - B[1])
        BC = (C[0] - B[0], C[1] - B[1])

        # Dot product and magnitudes
        dot_product = BA[0] * BC[0] + BA[1] * BC[1]
        magnitude_BA = math.hypot(*BA)
        magnitude_BC = math.hypot(*BC)

        # Guard against division by zero
        if magnitude_BA == 0 or magnitude_BC == 0:
            raise ValueError("One of the vectors has zero length.")

        # Compute angle in radians
        cos_theta = dot_product / (magnitude_BA * magnitude_BC)
        
        # Clamp value to avoid domain errors due to floating point precision
        cos_theta = max(-1.0, min(1.0, cos_theta))

        return math.acos(cos_theta)
        

    def stop(self):
        self._running = False