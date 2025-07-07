import time
from typing import Dict
import cv2.aruco as aruco
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QImage

from concurrent.futures import ThreadPoolExecutor
from capture.observer import ObserverThread
from stores.agent_pose_store import AgentPose
from stores.controller_context import ControllerContext

calibration_data_path = "../calibration_data_latest.npz"
marker_length = 0.12  # in meters


class FrameAnalyzer(QThread):
    _running: bool
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_7X7_100)
    pose_dict = Dict[int, AgentPose]

    def __init__(self, observer: ObserverThread, context: ControllerContext):
        super().__init__()
        self.context = context
        self._running = True
        npz_file = np.load(calibration_data_path)
        self.camera_matrix = npz_file['camera_matrix']
        self.dist_coeff = npz_file['dist_coeffs']
        self.arucoParams = cv2.aruco.DetectorParameters()
        self.pose_dict = {}

    def run(self):
        while(self._running):
            ids, corners = self.context.frame_data_store.get()
            if ids is not None:
                rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, marker_length, self.camera_matrix, self.dist_coeff)
                with ThreadPoolExecutor() as executor:
                    executor.map(
                        lambda args: process_marker(self.context, *args, rvecs, tvecs),
                        enumerate(ids.flatten())
                    )
            else:
                time.sleep(0.1)

    def stop(self):
        self._running = False



def process_marker(context: ControllerContext, i, marker_id, rvecs, tvecs):
    x, y, _ = tvecs[i][0]
    rvec = rvecs[i][0]
    R, _ = cv2.Rodrigues(rvec)
    yaw = np.arctan2(R[1, 0], R[0, 0])
    context.agent_pose_store.update(marker_id, AgentPose(x, y, yaw))