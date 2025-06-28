from threading import Lock
from typing import Dict, Optional
from dataclasses import dataclass


class FrameDataStore:
    ids: object
    corners: object

    def __init__(self):
        self._lock = Lock()
        self.ids = None
        self.corners = None


    def update(self, ids, corners):
        with self._lock:
            self.ids = ids
            self.corners = corners

    def get(self):
        with self._lock:
            return (self.ids, self.corners)