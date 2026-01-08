"""Artificial Potential Function (APF) utilities for collision avoidance."""

import math
from typing import Optional


def compute_repulsive_force(
    robot_pos: tuple[float, float],
    other_positions: list[tuple[float, float]],
    d_influence: float,
    d_safety: float,
    k_rep: float,
) -> tuple[float, float]:
    """
    Compute total repulsive force on a robot from all other robots.

    Args:
        robot_pos: Current (x, y) position of the robot
        other_positions: List of (x, y) positions of other robots
        d_influence: Radius of repulsive influence
        d_safety: Minimum safe distance (collision threshold)
        k_rep: Repulsive gain coefficient

    Returns:
        Total repulsive force as (fx, fy)
    """
    fx_total = 0.0
    fy_total = 0.0

    for other_pos in other_positions:
        dx = robot_pos[0] - other_pos[0]
        dy = robot_pos[1] - other_pos[1]
        d_ij = math.sqrt(dx * dx + dy * dy)

        # Skip if distance is zero (same position) or outside influence radius
        if d_ij < 1e-6:
            continue

        if d_ij < d_influence:
            # Clamp distance to safety threshold to prevent extreme forces
            d_clamped = max(d_ij, d_safety)

            # Repulsive force magnitude: k_rep * (1/d - 1/d_influence) * (1/d^2)
            magnitude = k_rep * (1.0 / d_clamped - 1.0 / d_influence) * (1.0 / (d_clamped * d_clamped))

            # Direction: unit vector from other robot to this robot
            ux = dx / d_ij
            uy = dy / d_ij

            fx_total += magnitude * ux
            fy_total += magnitude * uy

    return (fx_total, fy_total)


def adjust_target(
    target: tuple[float, float],
    repulsive_force: tuple[float, float],
    eta: float,
    max_adjustment: Optional[float] = None,
) -> tuple[float, float]:
    """
    Adjust target position based on repulsive force.

    Args:
        target: Original target (x, y) position
        repulsive_force: Repulsive force (fx, fy) computed from APF
        eta: Force-to-displacement scaling factor
        max_adjustment: Optional maximum adjustment distance to clamp drift

    Returns:
        Adjusted target position as (x, y)
    """
    adj_x = eta * repulsive_force[0]
    adj_y = eta * repulsive_force[1]

    # Optionally clamp the adjustment magnitude
    if max_adjustment is not None:
        adj_magnitude = math.sqrt(adj_x * adj_x + adj_y * adj_y)
        if adj_magnitude > max_adjustment:
            scale = max_adjustment / adj_magnitude
            adj_x *= scale
            adj_y *= scale

    return (target[0] + adj_x, target[1] + adj_y)
