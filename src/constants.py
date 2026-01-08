"""Centralized constants for the Odyssey Formation Control system."""

import numpy as np

# ArUco marker configuration
MARKER_LENGTH = 0.12  # in meters
ALL_MARKER_IDS = np.array([0, 1, 2, 3])

# Formation link configuration
LINK_LENGTH = 0.4  # in meters

# Link-to-agent mapping
LINK_AGENT_MAP = {0: [0], 1: [1, 2], 2: [3]}

# Nominal offsets for each agent within their link frame
NOMINAL_OFFSETS = {
    0: (0.0, 0.0),
    1: (0.0, 0.0),
    2: (LINK_LENGTH, 0.0),
    3: (LINK_LENGTH, 0.0),
}

# APF Collision Avoidance parameters
APF_D_INFLUENCE = 0.3  # Radius of repulsive influence (meters)
APF_D_SAFETY = 0.15  # Minimum safe distance / collision threshold (meters)
APF_K_REP = 0.01  # Repulsive gain coefficient
APF_ETA = 0.1  # Force-to-displacement scaling factor
APF_MAX_ADJUSTMENT = 0.1  # Maximum target adjustment distance (meters)
