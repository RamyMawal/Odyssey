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

# Path Crossing Resolver / Collision Avoidance parameters
PCR_COLLISION_RADIUS = 0.30  # Meters - conflict detection radius
PCR_TIME_WINDOW = 2.0  # Seconds - arrival time conflict window
PCR_ROBOT_SPEED_MIN = 0.2  # m/s - minimum robot speed
PCR_ROBOT_SPEED_MAX = 1.0  # m/s - maximum robot speed
PCR_CLEAR_MARGIN = 1.5  # Hysteresis factor for clearing conflicts
