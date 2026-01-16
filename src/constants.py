"""Centralized constants for the Odyssey Formation Control system."""

import numpy as np

# ArUco marker configuration
MARKER_LENGTH = 0.12  # in meters
ALL_MARKER_IDS = np.array([0, 1, 2, 3])

# Formation link configuration
LINK_LENGTH = 0.5  # in meters

# Number of links in the formation chain
NUM_LINKS = 4

# Link-to-agent mapping (1:1 - each link controls one robot)
LINK_AGENT_MAP = {0: [0], 1: [1], 2: [2], 3: [3]}

# Nominal offsets for each agent within their link frame
# Each robot is at the link pose (no offset) since FormationDispatcher
# already computes the end position of each link
NOMINAL_OFFSETS = {
    0: (0.0, 0.0),
    1: (0.0, 0.0),
    2: (0.0, 0.0),
    3: (0.0, 0.0),
}

# APF Collision Avoidance parameters
APF_D_INFLUENCE = 0.25  # Radius of repulsive influence (meters)
APF_D_SAFETY = 0.20  # Minimum safe distance / collision threshold (meters)
APF_K_REP = 0.01  # Repulsive gain coefficient
APF_ETA = 0.1  # Force-to-displacement scaling factor
APF_MAX_ADJUSTMENT = 0.1  # Maximum target adjustment distance (meters)
