import time
from math import cos, sin
import numpy as np
from PyQt6.QtCore import QThread
from models.vectors import Pose2D
from stores.controller_context import ControllerContext


class FormationDispatcher(QThread):
    pass

    def __init__(self, context: ControllerContext):
        super().__init__()
        self.context = context
        self._running = True

    def run(self):
        while self._running:
            discriptor = self.context.formation_state_store.get()

            if discriptor is None:
                time.sleep(0.5)
                continue

            (r_d_x, r_d_y), q_d, joints = (
                discriptor.r_d,
                discriptor.q_d,
                discriptor.theta_d,
            )

            X_r = np.array(
                [[cos(q_d), -sin(q_d), r_d_x], [sin(q_d), cos(q_d), r_d_y], [0, 0, 1]]
            )

            X_0_1 = np.eye(3) @ R(joints[0]) @ T(1)
            X_0_2 = X_0_1 @ R(joints[1]) @ T(1)

            X_0 = X_r
            X_1 = X_r @ X_0_1
            X_2 = X_r @ X_0_2

            r_d_0 = X_0[0, 2], X_0[1, 2]
            r_d_1 = X_1[0, 2], X_1[1, 2]
            r_d_2 = X_2[0, 2], X_2[1, 2]

            q_0 = q_d
            q_1 = q_0 + joints[0]
            q_2 = q_1 + joints[1]

            print(
                f"Dispatching poses: {r_d_0}, {r_d_1}, {r_d_2} with angles: {q_0}, {q_1}, {q_2}"
            )

            self.context.link_pose_store.update(0, Pose2D(r_d_0[0], r_d_0[1], q_0))
            self.context.link_pose_store.update(1, Pose2D(r_d_1[0], r_d_1[1], q_1))
            self.context.link_pose_store.update(2, Pose2D(r_d_2[0], r_d_2[1], q_2))

            time.sleep(0.1)

    def stop(self):
        self._running = False
        print("Stopping FormationDispatcher")


def R(theta: float):
    return np.array(
        [[cos(theta), -sin(theta), 0], [sin(theta), cos(theta), 0], [0, 0, 1]]
    )


def T(L):
    return np.array([[1, 0, L], [0, 1, 0], [0, 0, 1]])
