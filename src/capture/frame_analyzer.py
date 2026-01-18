import logging
import pathlib
import time

# from typing import Dict
import cv2.aruco as aruco
import cv2
import numpy as np
from PyQt6.QtCore import QThread

from concurrent.futures import ThreadPoolExecutor
from capture.observer import ObserverThread
from constants import MARKER_LENGTH, ALL_MARKER_IDS
from models.vectors import Pose2D
from stores.controller_context import ControllerContext

logger = logging.getLogger(__name__)

calibration_data_path = (
    pathlib.Path(__file__).parent.parent.parent / "calibration_data_latest.npz"
)


class FrameAnalyzer(QThread):
    _running: bool

    def __init__(self, observer: ObserverThread, context: ControllerContext):
        super().__init__()
        self.context = context
        self._running = True
        self.calibration_loaded = False

        try:
            npz_file = np.load(calibration_data_path)
            self.camera_matrix = npz_file["camera_matrix"]
            self.dist_coeff = npz_file["dist_coeffs"]
            self.calibration_loaded = True
        except FileNotFoundError:
            logger.error(f"Calibration file not found: {calibration_data_path}")
        except Exception as e:
            logger.error(f"Failed to load calibration data: {e}")

        self.arucoParams = cv2.aruco.DetectorParameters()

    def run(self):
        if not self.calibration_loaded:
            logger.error("FrameAnalyzer: Cannot run without calibration data")
            return

        while self._running:
            ids, corners = self.context.frame_data_store.get()
            # print(ids)
            if ids is not None:
                missing_ids = np.setdiff1d(ALL_MARKER_IDS, ids.flatten())
                # print(missing_ids)
                for id in missing_ids:
                    self.context.agent_pose_store.update(id, None)
                rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                    corners, MARKER_LENGTH, self.camera_matrix, self.dist_coeff
                )
                with ThreadPoolExecutor() as executor:
                    executor.map(
                        lambda args: process_marker(self.context, *args, rvecs, tvecs),
                        enumerate(ids.flatten()),
                    )
            else:
                for id in ALL_MARKER_IDS:
                    self.context.agent_pose_store.update(id, None)
                time.sleep(0.1)

    def stop(self):
        self._running = False


def process_marker(context: ControllerContext, i, marker_id, rvecs, tvecs):
    x, y, _ = tvecs[i][0]
    rvec = rvecs[i][0]
    R, _ = cv2.Rodrigues(rvec)
    yaw = np.arctan2(R[1, 0], R[0, 0])
    context.agent_pose_store.update(marker_id, Pose2D(x, y, yaw))
