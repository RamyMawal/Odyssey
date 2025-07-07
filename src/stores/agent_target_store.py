from threading import Lock
from typing import Dict, Optional
from dataclasses import dataclass

from models.vectors import Pose2D


class AgentTargetStore:
    def __init__(self):
        self._lock = Lock()
        self._poses: Dict[int, Pose2D] = {}

    def update(self, agent_id: int, pose: Pose2D):
        with self._lock:
            print(f"{agent_id}:{pose}")
            self._poses[agent_id] = pose

    def update_batch(self, pose_dict: Dict[int, Pose2D]):
        with self._lock:
            self._poses.update(pose_dict)

    def get(self, agent_id: int) -> Optional[Pose2D]:
        with self._lock:
            return self._poses.get(agent_id)

    def get_all(self) -> Dict[int, Pose2D]:
        with self._lock:
            return self._poses.copy()

    def get_agents_for_link(self, agent_ids: list[int]) -> Dict[int, Pose2D]:
        with self._lock:
            return {aid: self._poses[aid] for aid in agent_ids if aid in self._poses}
