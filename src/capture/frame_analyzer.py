import time

# from typing import Dict
import cv2.aruco as aruco
import cv2
import numpy as np
from PyQt6.QtCore import QThread

from concurrent.futures import ThreadPoolExecutor
from capture.observer import ObserverThread
from models.vectors import Pose2D
from stores.controller_context import ControllerContext

calibration_data_path = "../calibration_data_latest.npz"
marker_length = 0.12  # in meters
all_ids = np.array([0, 1, 2, 3])


class FrameAnalyzer(QThread):
    _running: bool

    def __init__(self, observer: ObserverThread, context: ControllerContext):
        super().__init__()
        self.context = context
        self._running = True
        npz_file = np.load(calibration_data_path)
        self.camera_matrix = npz_file["camera_matrix"]
        self.dist_coeff = npz_file["dist_coeffs"]
        self.arucoParams = cv2.aruco.DetectorParameters()

    def run(self):
        while self._running:
            ids, corners = self.context.frame_data_store.get()
            # print(ids)
            if ids is not None:
                missing_ids = np.setdiff1d(all_ids, ids.flatten())
                # print(missing_ids)
                for id in missing_ids:
                    self.context.agent_pose_store.update(id, None)
                rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                    corners, marker_length, self.camera_matrix, self.dist_coeff
                )
                with ThreadPoolExecutor() as executor:
                    executor.map(
                        lambda args: process_marker(self.context, *args, rvecs, tvecs),
                        enumerate(ids.flatten()),
                    )
            else:
                for id in all_ids:
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
