from threading import Lock
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class LinkPose:
    position: tuple[float, float]  # (x, y) an meters
    orientation: float             # in radians

class LinkPoseStore:
    def __init__(self):
        self._lock = Lock()
        self._poses: Dict[int, LinkPose] = {}

    def update(self, link_id: int, pose: LinkPose):
        with self._lock:
            self._poses[link_id] = pose

    def get(self, link_id: int) -> Optional[LinkPose]:
        with self._lock:
            return self._poses.get(link_id)

    def get_all(self) -> Dict[int, LinkPose]:
        with self._lock:
            return self._poses.copy()
