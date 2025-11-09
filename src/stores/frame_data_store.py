from threading import Lock
from typing import Sequence

from cv2 import UMat
from numpy import ndarray
import numpy as np


class FrameDataStore:
    ids: ndarray
    corners: Sequence[UMat]

    def __init__(self):
        self._lock = Lock()
        self.ids = np.empty((4, 1))
        self.corners = []

    def update(self, ids, corners):
        with self._lock:
            self.ids = ids
            self.corners = corners

    def get(self) -> tuple[ndarray, Sequence[UMat]]:
        with self._lock:
            return (self.ids, self.corners)

