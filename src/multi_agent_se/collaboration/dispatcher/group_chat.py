"""GroupChat管理模块 - 阶段4.

复用AutoGen GroupChat + GroupChatManager，封装多Agent群聊管理
"""

import os
from typing import Any, Dict, List, Optional

from autogen import GroupChat, GroupChatManager as AutogenGroupChatManager

from multi_agent_se.agents.agent_base import BaseAgent, AgentConfig

# 禁用Docker
os.environ["AUTOGEN_USE_DOCKER"] = "False"


class GroupChatManager:
    """GroupChat管理器.
    
    封装AutoGen GroupChat，提供简化的多Agent群聊管理
    """
    
    def __init__(
        self,
        name: str = "group_chat_manager",
        agents: Optional[List[BaseAgent]] = None,
        max_round: int = 20,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.agents: List[BaseAgent] = agents or []
        self.max_round = max_round
        self._llm_config = llm_config or {
            "config_list": [{"model": "gpt-4", "api_key": "placeholder"}],
            "timeout": 60,
        }
        self._group_chat: Optional[GroupChat] = None
        self._manager: Optional[AutogenGroupChatManager] = None
    
    def add_agent(self, agent: BaseAgent) -> "GroupChatManager":
        if agent not in self.agents:
            self.agents.append(agent)
        return self
    
    def remove_agent(self, agent_name: str) -> "GroupChatManager":
        self.agents = [a for a in self.agents if a.name != agent_name]
        return self
    
    def build(self) -> "GroupChatManager":
        if len(self.agents) < 2:
            raise ValueError("GroupChat至少需要2个Agent")
        
        autogen_agents = [a.agent for a in self.agents]
        
        self._group_chat = GroupChat(
            agents=autogen_agents,
            messages=[],
            max_round=self.max_round,
        )
        
        self._manager = AutogenGroupChatManager(
            groupchat=self._group_chat,
            name=self.name,
            llm_config=self._llm_config,
        )
        return self
    
    def get_agent_list(self) -> List[str]:
        return [a.name for a in self.agents]
    
    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        if self._group_chat:
            return list(self._group_chat.messages)
        return []
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "agent_count": len(self.agents),
            "agents": [f"{a.name}({a.role})" for a in self.agents],
            "max_round": self.max_round,
            "is_built": self._group_chat is not None,
            "message_count": len(self.get_chat_history()),
        }
    
    @property
    def autogen_manager(self) -> Optional[AutogenGroupChatManager]:
        return self._manager
    
    @property
    def autogen_group_chat(self) -> Optional[GroupChat]:
        return self._group_chat
