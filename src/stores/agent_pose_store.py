from threading import Lock
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class AgentPose:
    x: float
    y: float
    theta: float 

class AgentPoseStore:
    def __init__(self):
        self._lock = Lock()
        self._poses: Dict[int, AgentPose] = {}

    def update(self, agent_id: int, pose: AgentPose):
        with self._lock:
            print(f"{agent_id}:{pose}")
            self._poses[agent_id] = pose

    def update_batch(self, pose_dict: Dict[int, AgentPose]):
        with self._lock:
            self._poses.update(pose_dict)

    def get(self, agent_id: int) -> Optional[AgentPose]:
        with self._lock:
            return self._poses.get(agent_id)

    def get_all(self) -> Dict[int, AgentPose]:
        with self._lock:
            return self._poses.copy()

    def get_agents_for_link(self, agent_ids: list[int]) -> Dict[int, AgentPose]:
        with self._lock:
            return {aid: self._poses[aid] for aid in agent_ids if aid in self._poses}
