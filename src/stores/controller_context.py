from dataclasses import dataclass
from stores.formation_state_store import FormationStateStore
from stores.frame_data_store import FrameDataStore
from stores.link_pose_store import LinkPoseStore
from stores.agent_pose_store import AgentPoseStore
import queue


class ControllerContext:
    agent_pose_store: AgentPoseStore
    link_pose_store: LinkPoseStore
    formation_state_store: FormationStateStore
    frame_data_store: FrameDataStore
    agent_command_queue: queue.Queue
    link_target_queue: queue.Queue

    def __init__(self):
        self.agent_pose_store = AgentPoseStore()
        self.link_pose_store = LinkPoseStore()
        self.formation_state_store = FormationStateStore()
        self.frame_data_store = FrameDataStore()
        self.agent_command_queue = queue.Queue()
        self.link_target_queue = queue.Queue()



