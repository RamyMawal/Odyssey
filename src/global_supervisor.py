import math
import time
from configuration_manager import ConfigurationManager
from models.vectors import Pose2D
from stores.controller_context import ControllerContext
from enums.configurations.formation_shape import FormationShape
from PyQt6.QtCore import QThread
from stores.formation_state_store import FormationDescriptor


class GlobalSupervisor(QThread):
    current_formation: FormationDescriptor

    def __init__(
        self, context: ControllerContext, config_manager: ConfigurationManager
    ):
        super().__init__()
        self.context = context
        self.config_manager = config_manager
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            _, shape, target = self.config_manager.get_current_config()

            joints = self.get_joint_angles(shape)
            multipliers = self.get_link_multipliers(shape)

            r_d, q_d = self.get_coordinates(target)

            self.current_formation = FormationDescriptor(r_d, q_d, joints, multipliers)

            # print(f"Global Supervisor: {self.current_formation}")

            self.context.formation_state_store.update(self.current_formation)
            time.sleep(0.1)

    def get_coordinates(self, target: Pose2D) -> tuple[tuple[float, float], float]:
        return ((target.x, target.y), target.theta)

    def get_joint_angles(self, shape: FormationShape) -> list[float]:
        match shape:
            case FormationShape.LINE:
                # Origin in center: 0 -- 1 -- O -- 2 -- 3
                return [
                    math.radians(180),   # Go left from origin
                    math.radians(180),   # Turn around to go right
                    math.radians(0),     # Continue right
                    math.radians(0),     # Continue right
                ]
            case FormationShape.SQUARE:
                # O(center) → 0(bottom-left) → 1(top-left) → 2(top-right) → 3(bottom-right)
                return [
                    math.radians(-135),  # From origin (0°), go to bottom-left (-135°)
                    math.radians(225),   # From -135°, turn to face up (90°): 90 - (-135) = 225
                    math.radians(-90),   # From 90°, turn to face right (0°): 0 - 90 = -90
                    math.radians(-90),   # From 0°, turn to face down (-90°): -90 - 0 = -90
                ]
            case FormationShape.TRIANGLE:
                # Robot 0 at center, Robots 1,2,3 at triangle corners
                return [
                    math.radians(0),    # O → Robot 0 (at origin)
                    math.radians(0),    # Robot 0 → Robot 1 (right)
                    math.radians(150),  # Robot 1 → Robot 2 (top-left)
                    math.radians(120),  # Robot 2 → Robot 3 (bottom-left)
                ]
            case FormationShape.DIAMOND:
                # Origin at center, robots at cardinal directions (W, N, E, S)
                return [
                    math.radians(180),   # O → Robot 0 (left)
                    math.radians(-135),  # Robot 0 → Robot 1 (top)
                    math.radians(-90),   # Robot 1 → Robot 2 (right)
                    math.radians(-90),   # Robot 2 → Robot 3 (bottom)
                ]
            case FormationShape.FAN:
                # Robot 0 at origin, Robots 1,2,3 spread above
                return [
                    math.radians(0),     # O → Robot 0 (at origin)
                    math.radians(135),   # Robot 0 → Robot 1 (top-left)
                    math.radians(-135),  # Robot 1 → Robot 2 (top-center)
                    math.radians(0),     # Robot 2 → Robot 3 (top-right)
                ]
            case _:
                return [0, 0, 0, 0]

    def get_link_multipliers(self, shape: FormationShape) -> list[float]:
        """Return link length multipliers. Actual length = multiplier × LINK_LENGTH."""
        match shape:
            case FormationShape.LINE:
                # Origin in center: 0(-0.6) -- 1(-0.2) -- O(0) -- 2(0.2) -- 3(0.6)
                # Uniform LINK_LENGTH spacing between all adjacent robots
                return [1.5, 1.0, 1.0, 1.0]
            case FormationShape.SQUARE:
                # First link from center to corner = √2/2, others = 1
                return [0.7071, 1.0, 1.0, 1.0]
            case FormationShape.TRIANGLE:
                # Robot 0 at origin (length 0), then to corners
                # Side length = LINK_LENGTH * √3 ≈ 1.732
                return [0, 1.0, 1.732, 1.732]
            case FormationShape.DIAMOND:
                # First link = 1, others = √2 (diagonal of unit square)
                return [1.0, 1.414, 1.414, 1.414]
            case FormationShape.FAN:
                # Robot 0 at origin, then diagonal to top-left, then horizontal
                return [0, 1.414, 1.0, 1.0]
            case _:
                return [1.0, 1.0, 1.0, 1.0]
