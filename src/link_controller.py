import numpy as np
import time
from math import sin,cos
from PyQt6.QtCore import QThread, QRunnable
from models.vectors import Pose2D
from stores.controller_context import ControllerContext

class LinkControllerThread(QThread):
    link_agent_map = {
        0: [0],
        1: [1,2],
        2: [3]
    }
    nominal_offsets = {
        0:(0.0,0.0),
        1:(0.0,0.0),
        2:(1.0,0.0),
        3:(1.0,0.0)
    }

    def __init__(self, link_id:int, context:ControllerContext):
        super().__init__()
        self.context = context
        self.link_id = link_id
        self._running = True

    def run(self):
        while self._running:
            link_pose = self.context.link_pose_store.get(self.link_id)
            if(link_pose is None):
                time.sleep(0.5)
                continue

            r_d , q_d = (link_pose.x, link_pose.y), link_pose.theta
            agent_ids = self.link_agent_map[self.link_id]

            X_F = np.array([[cos(q_d), -sin(q_d), r_d[0]],
                            [sin(q_d), cos(q_d),  r_d[1]],
                            [0,          0,           1]])
            
            agent_poses = dict[int, Pose2D]()

            for i in agent_ids:
                offset = self.nominal_offsets[i]

                pose = X_F @ np.array([offset[0], offset[1], 1])

                agent_poses[i] = Pose2D(pose[0], pose[1], 0)

            self.context.agent_target_store.update_batch(agent_poses)
