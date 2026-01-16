from threading import Lock
from typing import Optional
from dataclasses import dataclass

@dataclass
class FormationDescriptor:
    r_d: tuple[float, float]      # global position
    q_d: float                    # global orientation
    theta_d: list[float]          # joint angles
    link_multipliers: list[float] # length multipliers per link

class FormationStateStore:
    def __init__(self):
        self._lock = Lock()
        self._formation: Optional[FormationDescriptor] = None

    def update(self, new_state: FormationDescriptor):
        with self._lock:
            self._formation = new_state

    def get(self) -> Optional[FormationDescriptor]:
        with self._lock:
            return self._formation
