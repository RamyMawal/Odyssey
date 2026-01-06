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
