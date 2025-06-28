from dataclasses import dataclass


@dataclass
class TargetJoint:
    id: int
    location: tuple[float,float]