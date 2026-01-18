"""Thread-safe store for path-resolved target positions."""

from threading import Lock
from typing import Dict, Optional

from models.vectors import Pose2D


class AgentResolvedTargetStore:
    """
    Thread-safe storage for path-resolved target positions.

    This store holds targets that have been processed by the PathCrossingResolver
    to handle path intersection conflicts before APF collision avoidance.
    """

    def __init__(self):
        self._lock = Lock()
        self._poses: Dict[int, Pose2D] = {}

    def update(self, agent_id: int, pose: Pose2D):
        """Update the resolved target for a single agent."""
        with self._lock:
            self._poses[agent_id] = pose

    def update_batch(self, pose_dict: Dict[int, Pose2D]):
        """Update resolved targets for multiple agents at once."""
        with self._lock:
            self._poses.update(pose_dict)

    def get(self, agent_id: int) -> Optional[Pose2D]:
        """Get the resolved target for a specific agent."""
        with self._lock:
            return self._poses.get(agent_id)

    def get_all(self) -> Dict[int, Pose2D]:
        """Get all resolved targets."""
        with self._lock:
            return self._poses.copy()
