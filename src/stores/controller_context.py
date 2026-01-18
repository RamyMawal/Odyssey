from stores.agent_resolved_target_store import AgentResolvedTargetStore
from stores.agent_target_store import AgentTargetStore
from stores.formation_state_store import FormationStateStore
from stores.frame_data_store import FrameDataStore
from stores.link_pose_store import LinkPoseStore
from stores.agent_pose_store import AgentPoseStore


class ControllerContext:
    agent_pose_store: AgentPoseStore
    link_pose_store: LinkPoseStore
    formation_state_store: FormationStateStore
    frame_data_store: FrameDataStore
    agent_target_store: AgentTargetStore
    resolved_target_store: AgentResolvedTargetStore
    port: str
    safety_stop_enabled: bool

    def __init__(self):
        self.agent_pose_store = AgentPoseStore()
        self.link_pose_store = LinkPoseStore()
        self.formation_state_store = FormationStateStore()
        self.frame_data_store = FrameDataStore()
        self.agent_target_store = AgentTargetStore()
        self.resolved_target_store = AgentResolvedTargetStore()
        self.port = ""
        self.safety_stop_enabled = False  



