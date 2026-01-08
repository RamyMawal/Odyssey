"""Collision avoidance layer using Artificial Potential Functions (APF)."""

import logging
import time

from PyQt6.QtCore import QThread

from apf import adjust_target, compute_repulsive_force
from constants import (
    APF_D_INFLUENCE,
    APF_D_SAFETY,
    APF_ETA,
    APF_K_REP,
    APF_MAX_ADJUSTMENT,
)
from models.vectors import Pose2D
from stores.controller_context import ControllerContext

logger = logging.getLogger(__name__)


class CollisionAvoidanceLayer(QThread):
    """
    Reads raw targets from AgentTargetStore, applies APF corrections
    based on current poses, and writes adjusted targets to AdjustedTargetStore.

    Runs at 40Hz for responsive collision avoidance.
    """

    def __init__(self, context: ControllerContext):
        super().__init__()
        self.context = context
        self._running = True

        # APF parameters (can be modified at runtime)
        self.d_influence = APF_D_INFLUENCE
        self.d_safety = APF_D_SAFETY
        self.k_rep = APF_K_REP
        self.eta = APF_ETA
        self.max_adjustment = APF_MAX_ADJUSTMENT
        self.enabled = True

    def run(self):
        logger.info("Running CollisionAvoidanceLayer")
        while self._running:
            raw_targets = self.context.agent_target_store.get_all()
            current_poses = self.context.agent_pose_store.get_all()

            adjusted = {}
            for robot_id, target in raw_targets.items():
                if self.enabled and target is not None:
                    # Get current position of this robot
                    robot_pose = current_poses.get(robot_id)
                    if robot_pose is None:
                        # No pose data, pass through raw target
                        adjusted[robot_id] = target
                        continue

                    # Get positions of all other robots
                    other_positions = []
                    for other_id, other_pose in current_poses.items():
                        if other_id != robot_id and other_pose is not None:
                            other_positions.append((other_pose.x, other_pose.y))

                    # Compute repulsive force
                    force = compute_repulsive_force(
                        robot_pos=(robot_pose.x, robot_pose.y),
                        other_positions=other_positions,
                        d_influence=self.d_influence,
                        d_safety=self.d_safety,
                        k_rep=self.k_rep,
                    )

                    # Adjust target based on repulsive force
                    adj_x, adj_y = adjust_target(
                        target=(target.x, target.y),
                        repulsive_force=force,
                        eta=self.eta,
                        max_adjustment=self.max_adjustment,
                    )

                    adjusted[robot_id] = Pose2D(adj_x, adj_y, target.theta)
                else:
                    # APF disabled or no target, pass through
                    adjusted[robot_id] = target

            self.context.adjusted_target_store.update_batch(adjusted)

            # 40Hz update rate
            time.sleep(0.025)

        logger.info("Stopping CollisionAvoidanceLayer")

    def stop(self):
        self._running = False

    def set_enabled(self, enabled: bool):
        """Enable or disable APF collision avoidance."""
        self.enabled = enabled
        logger.info(f"CollisionAvoidanceLayer enabled: {enabled}")
