import logging
import time
from math import cos, sin
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from constants import LINK_LENGTH, NUM_LINKS
from models.vectors import Pose2D
from stores.controller_context import ControllerContext

logger = logging.getLogger(__name__)


class FormationDispatcher(QThread):
    # Signal: (origin_pos, origin_theta, joint_angles, link_poses)
    poses_computed = pyqtSignal(tuple, float, list, list)

    def __init__(self, context: ControllerContext):
        super().__init__()
        self.context = context
        self._running = True

    def run(self):
        while self._running:
            descriptor = self.context.formation_state_store.get()

            if descriptor is None:
                time.sleep(0.5)
                continue

            (r_d_x, r_d_y), q_d, joints, multipliers = (
                descriptor.r_d,
                descriptor.q_d,
                descriptor.theta_d,
                descriptor.link_multipliers,
            )

            # Origin transformation matrix (virtual origin point)
            X_origin = np.array(
                [[cos(q_d), -sin(q_d), r_d_x], [sin(q_d), cos(q_d), r_d_y], [0, 0, 1]]
            )

            # Build chain: each link rotates by joint angle, then translates
            cumulative = X_origin
            orientation = q_d

            link_poses = []
            for i in range(NUM_LINKS):
                # Use shape-specific multiplier for link length
                link_length = multipliers[i] * LINK_LENGTH

                # Apply rotation for this joint, then translate along link
                cumulative = cumulative @ R(joints[i]) @ T(link_length)
                orientation = orientation + joints[i]

                # Extract position from transformation matrix
                pos = (cumulative[0, 2], cumulative[1, 2])
                self.context.link_pose_store.update(i, Pose2D(pos[0], pos[1], orientation))
                link_poses.append((pos[0], pos[1], orientation))

            # Emit signal with computed poses
            self.poses_computed.emit((r_d_x, r_d_y), q_d, joints, link_poses)

            time.sleep(0.5)

    def stop(self):
        self._running = False
        logger.info("Stopping FormationDispatcher")


def R(theta: float) -> np.ndarray:
    return np.array(
        [[cos(theta), -sin(theta), 0], [sin(theta), cos(theta), 0], [0, 0, 1]]
    )


def T(L: float) -> np.ndarray:
    return np.array([[1, 0, L], [0, 1, 0], [0, 0, 1]])
