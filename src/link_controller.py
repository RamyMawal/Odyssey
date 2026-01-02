import logging
import numpy as np
import time
from math import sin, cos
from PyQt6.QtCore import QThread
from constants import LINK_AGENT_MAP, NOMINAL_OFFSETS
from models.vectors import Pose2D
from stores.controller_context import ControllerContext

logger = logging.getLogger(__name__)


class LinkControllerThread(QThread):

    def __init__(self, link_id: int, context: ControllerContext):
        super().__init__()
        self.context = context
        self.link_id = link_id
        self._running = True

    def run(self):
        logger.info(f"Running LinkControllerThread for link {self.link_id}")
        while self._running:
            link_pose = self.context.link_pose_store.get(self.link_id)
            if link_pose is None:
                # print(f"Link {self.link_id} pose not available, waiting...")
                time.sleep(0.5)
                continue

            r_d, q_d = (link_pose.x, link_pose.y), link_pose.theta
            agent_ids = LINK_AGENT_MAP[self.link_id]

            X_F = np.array(
                [[cos(q_d), -sin(q_d), r_d[0]], [sin(q_d), cos(q_d), r_d[1]], [0, 0, 1]]
            )

            agent_poses = dict[int, Pose2D]()

            for i in agent_ids:
                offset = NOMINAL_OFFSETS[i]

                pose = X_F @ np.array([offset[0], offset[1], 1])

                agent_poses[i] = Pose2D(pose[0], pose[1], 0)

            # for agent_id, pose in agent_poses.items():
            # print(f"Link {self.link_id} updating agent {agent_id} pose: {pose.x:.3f}, {pose.y:.3f}, {pose.theta:.3f}")

            self.context.agent_target_store.update_batch(agent_poses)
            time.sleep(0.05)  # 20Hz update rate

    def stop(self):
        self._running = False
        logger.info(f"Stopping LinkControllerThread for link {self.link_id}")
