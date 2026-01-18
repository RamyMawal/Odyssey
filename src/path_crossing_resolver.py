"""Path Crossing Resolver using Priority-Based Conflict Resolution."""

import logging
import math
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple

from PyQt6.QtCore import QThread

from constants import (
    PCR_CLEAR_MARGIN,
    PCR_COLLISION_RADIUS,
    PCR_ROBOT_SPEED_MAX,
    PCR_ROBOT_SPEED_MIN,
    PCR_TIME_WINDOW,
)
from models.vectors import Pose2D
from stores.controller_context import ControllerContext

logger = logging.getLogger(__name__)


@dataclass
class PathConflict:
    """Represents a detected path crossing conflict between two robots."""

    robot_a: int
    robot_b: int
    intersection_point: Tuple[float, float]
    time_to_intersection_a: float
    time_to_intersection_b: float


def segments_intersect(
    p1: Tuple[float, float],
    t1: Tuple[float, float],
    p2: Tuple[float, float],
    t2: Tuple[float, float],
) -> Tuple[bool, Optional[Tuple[float, float]]]:
    """
    Check if line segment p1->t1 intersects segment p2->t2.

    Uses parametric line intersection with cross products.

    Args:
        p1: Start point of segment 1 (robot 1 current position)
        t1: End point of segment 1 (robot 1 target)
        p2: Start point of segment 2 (robot 2 current position)
        t2: End point of segment 2 (robot 2 target)

    Returns:
        (intersects, intersection_point) - intersection_point is None if no intersection
    """
    # Direction vectors
    d1 = (t1[0] - p1[0], t1[1] - p1[1])
    d2 = (t2[0] - p2[0], t2[1] - p2[1])

    # Cross product of direction vectors
    cross = d1[0] * d2[1] - d1[1] * d2[0]

    # Parallel or collinear lines
    if abs(cross) < 1e-10:
        return False, None

    # Vector from p1 to p2
    dp = (p2[0] - p1[0], p2[1] - p1[1])

    # Parameters for intersection point
    t = (dp[0] * d2[1] - dp[1] * d2[0]) / cross
    u = (dp[0] * d1[1] - dp[1] * d1[0]) / cross

    # Check if intersection is within both segments
    if 0 <= t <= 1 and 0 <= u <= 1:
        intersection = (p1[0] + t * d1[0], p1[1] + t * d1[1])
        return True, intersection

    return False, None


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def calculate_speed(dist_to_target: float, speed_min: float, speed_max: float) -> float:
    """
    Calculate robot speed based on distance to target.

    Speed equals distance to target, clamped between min and max.
    This means robots slow down as they approach their target.
    """
    return max(speed_min, min(dist_to_target, speed_max))


def estimate_time_to_point(
    current: Tuple[float, float],
    target: Tuple[float, float],
    final_target: Tuple[float, float],
    speed_min: float,
    speed_max: float,
) -> float:
    """
    Estimate time to reach a point with dynamic speed.

    Speed is based on distance to final_target (not the intermediate point).
    """
    dist_to_point = distance(current, target)
    dist_to_final = distance(current, final_target)
    speed = calculate_speed(dist_to_final, speed_min, speed_max)
    if speed <= 0:
        return float("inf")
    return dist_to_point / speed


class PathCrossingResolver(QThread):
    """
    Detects path crossings and resolves conflicts using priority-based strategy.

    Higher priority robots (lower ID) continue; lower priority robots wait.

    Reads raw targets from AgentTargetStore, applies path crossing resolution,
    and writes resolved targets to AgentResolvedTargetStore.
    """

    def __init__(self, context: ControllerContext):
        super().__init__()
        self.context = context
        self._running = True
        self.enabled = True

        # Track active conflicts with hysteresis
        self._active_conflicts: Set[Tuple[int, int]] = set()

        # Parameters
        self.collision_radius = PCR_COLLISION_RADIUS
        self.time_window = PCR_TIME_WINDOW
        self.speed_min = PCR_ROBOT_SPEED_MIN
        self.speed_max = PCR_ROBOT_SPEED_MAX
        self.clear_margin = PCR_CLEAR_MARGIN

    def detect_conflicts(
        self,
        targets: Dict[int, Pose2D],
        poses: Dict[int, Optional[Pose2D]],
    ) -> list[PathConflict]:
        """
        Detect conflicts between all robot pairs.

        A conflict exists when:
        1. Robots are currently too close (proximity conflict)
        2. Two robot paths intersect geometrically with similar arrival times
        3. Two robots have targets that are too close
        """
        conflicts = []
        robot_ids = sorted(targets.keys())

        for i, robot_a in enumerate(robot_ids):
            for robot_b in robot_ids[i + 1 :]:
                target_a = targets.get(robot_a)
                target_b = targets.get(robot_b)
                pose_a = poses.get(robot_a)
                pose_b = poses.get(robot_b)

                # Skip if any required data is missing
                if target_a is None or target_b is None:
                    continue
                if pose_a is None or pose_b is None:
                    continue

                p1 = (pose_a.x, pose_a.y)
                t1 = (target_a.x, target_a.y)
                p2 = (pose_b.x, pose_b.y)
                t2 = (target_b.x, target_b.y)

                # 1. PROXIMITY CHECK: Are robots currently too close?
                current_distance = distance(p1, p2)
                if current_distance < self.collision_radius:
                    # Emergency proximity conflict - robots are already too close
                    conflicts.append(
                        PathConflict(
                            robot_a=robot_a,
                            robot_b=robot_b,
                            intersection_point=p1,  # Current position as conflict point
                            time_to_intersection_a=0.0,  # Already there
                            time_to_intersection_b=0.0,
                        )
                    )
                    continue  # Skip other checks, proximity takes precedence

                # 2. PATH CROSSING CHECK: Do the paths intersect?
                intersects, intersection = segments_intersect(p1, t1, p2, t2)

                if intersects and intersection:
                    # Check arrival times (speed based on distance to final target)
                    time_a = estimate_time_to_point(
                        p1, intersection, t1, self.speed_min, self.speed_max
                    )
                    time_b = estimate_time_to_point(
                        p2, intersection, t2, self.speed_min, self.speed_max
                    )

                    # Conflict if both arrive within time window of each other
                    if abs(time_a - time_b) < self.time_window:
                        conflicts.append(
                            PathConflict(
                                robot_a=robot_a,
                                robot_b=robot_b,
                                intersection_point=intersection,
                                time_to_intersection_a=time_a,
                                time_to_intersection_b=time_b,
                            )
                        )
                else:
                    # 3. TARGET PROXIMITY CHECK: Are targets too close?
                    if distance(t1, t2) < self.collision_radius:
                        conflicts.append(
                            PathConflict(
                                robot_a=robot_a,
                                robot_b=robot_b,
                                intersection_point=t1,
                                time_to_intersection_a=estimate_time_to_point(
                                    p1, t1, t1, self.speed_min, self.speed_max
                                ),
                                time_to_intersection_b=estimate_time_to_point(
                                    p2, t2, t2, self.speed_min, self.speed_max
                                ),
                            )
                        )

        return conflicts

    def resolve_conflicts(
        self,
        targets: Dict[int, Pose2D],
        poses: Dict[int, Optional[Pose2D]],
        conflicts: list[PathConflict],
    ) -> Dict[int, Pose2D]:
        """
        Resolve conflicts using priority-based strategy.

        Lower robot ID = higher priority.
        Higher priority robot continues to its target.
        Lower priority robot waits at current position.
        """
        resolved = dict(targets)
        waiting_robots: Set[int] = set()

        # Get current conflict pairs
        current_conflict_pairs: Set[Tuple[int, int]] = set()

        for conflict in conflicts:
            pair = (
                min(conflict.robot_a, conflict.robot_b),
                max(conflict.robot_a, conflict.robot_b),
            )
            current_conflict_pairs.add(pair)

            # Lower ID has priority (continues), higher ID waits
            waiter = max(conflict.robot_a, conflict.robot_b)
            waiting_robots.add(waiter)

        # Update active conflicts with hysteresis
        new_conflicts = current_conflict_pairs - self._active_conflicts
        for pair in new_conflicts:
            logger.info(f"Path conflict detected: Robot {pair[0]} vs Robot {pair[1]}")
            self._active_conflicts.add(pair)

        # Check if existing conflicts should be cleared
        cleared = set()
        for pair in self._active_conflicts:
            if pair not in current_conflict_pairs:
                # Check if robots have passed intersection (hysteresis)
                robot_a, robot_b = pair
                pose_a = poses.get(robot_a)
                pose_b = poses.get(robot_b)
                target_a = targets.get(robot_a)

                if pose_a and pose_b and target_a:
                    # Clear if higher priority robot is close to its target
                    dist_to_target = distance(
                        (pose_a.x, pose_a.y), (target_a.x, target_a.y)
                    )
                    if dist_to_target < self.collision_radius * self.clear_margin:
                        cleared.add(pair)
                        logger.info(
                            f"Path conflict cleared: Robot {pair[0]} vs Robot {pair[1]}"
                        )

        self._active_conflicts -= cleared

        # Apply wait strategy: robots in active conflicts wait
        for pair in self._active_conflicts:
            waiter = max(pair[0], pair[1])
            waiting_robots.add(waiter)

        # Set resolved targets
        for robot_id in waiting_robots:
            pose = poses.get(robot_id)
            if pose:
                # WAIT strategy: target = current position
                resolved[robot_id] = Pose2D(pose.x, pose.y, pose.theta)

        return resolved

    def run(self):
        logger.info("Running PathCrossingResolver")
        while self._running:
            raw_targets = self.context.agent_target_store.get_all()
            current_poses = self.context.agent_pose_store.get_all()

            if self.enabled and raw_targets and current_poses:
                # Detect path crossings
                conflicts = self.detect_conflicts(raw_targets, current_poses)

                # Resolve conflicts
                resolved = self.resolve_conflicts(raw_targets, current_poses, conflicts)

                # Write to resolved target store
                self.context.resolved_target_store.update_batch(resolved)
            else:
                # Pass through raw targets
                self.context.resolved_target_store.update_batch(raw_targets)

            # 20Hz update rate (path planning doesn't need to be as fast as APF)
            time.sleep(0.05)

        logger.info("Stopping PathCrossingResolver")

    def stop(self):
        self._running = False

    def set_enabled(self, enabled: bool):
        """Enable or disable path crossing resolution."""
        self.enabled = enabled
        if not enabled:
            self._active_conflicts.clear()
        logger.info(f"PathCrossingResolver enabled: {enabled}")
