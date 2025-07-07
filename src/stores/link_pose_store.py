from threading import Lock
from typing import Dict, Optional
from dataclasses import dataclass

from models.vectors import Pose2D


class LinkPoseStore:
    def __init__(self):
        self._lock = Lock()
        self._poses: Dict[int, Pose2D] = {}

    def update(self, link_id: int, pose: Pose2D):
        with self._lock:
            self._poses[link_id] = pose

    def get(self, link_id: int) -> Optional[Pose2D]:
        with self._lock:
            return self._poses.get(link_id)

    def get_all(self) -> Dict[int, Pose2D]:
        with self._lock:
            return self._poses.copy()
