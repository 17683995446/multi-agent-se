"""Agent基础类模块 - 阶段4.

复用AutoGen ConversableAgent，封装统一Agent创建接口
遵循第一性原理：职责正交公理（Agent职责无重叠、无空缺）
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager


class HumanInputMode(Enum):
    """人机交互模式."""
    NEVER = "NEVER"           # 从不需要人工输入
    ALWAYS = "ALWAYS"         # 总是需要人工输入
    TERMINATE = "TERMINATE"   # 终止时需要人工输入


@dataclass
class AgentConfig:
    """Agent配置."""
    name: str
    role: str = ""
    system_message: str = "你是一个专业的软件工程助手。"
    human_input_mode: str = HumanInputMode.NEVER.value
    llm_config: Optional[Dict[str, Any]] = None
    max_consecutive_auto_reply: int = 10
    description: str = ""
    code_execution_config: Optional[Dict[str, Any]] = None


class BaseAgent:
    """Agent基础类.
    
    封装AutoGen ConversableAgent，提供统一接口
    """
    
    def __init__(self, config: AgentConfig) -> None:
        """初始化Agent.
        
        Args:
            config: Agent配置
        """
        self.config = config
        self._agent: Optional[ConversableAgent] = None
        self._message_history: List[Dict[str, Any]] = []
        self._init_agent()
    
    def _init_agent(self) -> None:
        """初始化AutoGen Agent."""
        llm_config = self.config.llm_config or {
            "config_list": [{"model": "gpt-4", "api_key": "placeholder"}],
            "timeout": 60,
        }
        
        self._agent = ConversableAgent(
            name=self.config.name,
            system_message=self.config.system_message,
            llm_config=llm_config,
            human_input_mode=self.config.human_input_mode,
            max_consecutive_auto_reply=self.config.max_consecutive_auto_reply,
            description=self.config.description,
            code_execution_config=self.config.code_execution_config or False,
        )
    
    @property
    def agent(self) -> ConversableAgent:
        """获取底层AutoGen Agent."""
        return self._agent
    
    @property
    def name(self) -> str:
        """获取Agent名称."""
        return self.config.name
    
    @property
    def role(self) -> str:
        """获取Agent角色."""
        return self.config.role
    
    def send_message(
        self,
        message: str,
        recipient: "BaseAgent",
        request_reply: bool = True
    ) -> Optional[str]:
        """发送消息给另一个Agent.
        
        Args:
            message: 消息内容
            recipient: 接收方Agent
            request_reply: 是否请求回复
            
        Returns:
            回复内容
        """
        self._message_history.append({
            "from": self.name,
            "to": recipient.name,
            "content": message,
        })
        
        response = self._agent.send(
            recipient.agent,
            message,
            request_reply=request_reply,
            silent=True,
        )
        return response
    
    def receive_message(
        self,
        message: str,
        sender: "BaseAgent",
        request_reply: bool = True
    ) -> Optional[str]:
        """接收消息.
        
        Args:
            message: 消息内容
            sender: 发送方Agent
            request_reply: 是否请求回复
            
        Returns:
            回复内容
        """
        self._message_history.append({
            "from": sender.name,
            "to": self.name,
            "content": message,
        })
        
        response = self._agent.receive(
            sender.agent,
            message,
            request_reply=request_reply,
            silent=True,
        )
        return response
    
    def generate_reply(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional["BaseAgent"] = None
    ) -> Optional[str]:
        """生成回复.
        
        Args:
            messages: 消息列表
            sender: 发送方Agent
            
        Returns:
            回复内容
        """
        return self._agent.generate_reply(
            messages=messages,
            sender=sender.agent if sender else None,
        )
    
    def get_message_history(self) -> List[Dict[str, Any]]:
        """获取消息历史.
        
        Returns:
            消息历史列表
        """
        return list(self._message_history)
    
    def clear_history(self) -> None:
        """清空消息历史."""
        self._message_history.clear()
    
    def __repr__(self) -> str:
        return f"BaseAgent(name={self.name}, role={self.role})"


class UserProxyWrapper(BaseAgent):
    """用户代理包装类."""
    
    def __init__(
        self,
        name: str = "user_proxy",
        human_input_mode: str = HumanInputMode.NEVER.value,
        code_execution_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化用户代理.
        
        Args:
            name: 代理名称
            human_input_mode: 人机交互模式
            code_execution_config: 代码执行配置
        """
        config = AgentConfig(
            name=name,
            role="user_proxy",
            system_message="",
            human_input_mode=human_input_mode,
            code_execution_config=code_execution_config,
        )
        super().__init__(config)
        self._agent = UserProxyAgent(
            name=name,
            human_input_mode=human_input_mode,
            code_execution_config=code_execution_config or False,
        )


# ========== Agent工厂函数 ==========

def create_assistant_agent(
    name: str,
    role: str,
    system_message: str,
    llm_config: Optional[Dict[str, Any]] = None,
) -> BaseAgent:
    """创建助手Agent.
    
    Args:
        name: Agent名称
        role: Agent角色
        system_message: 系统消息
        llm_config: LLM配置
        
    Returns:
        BaseAgent实例
    """
    config = AgentConfig(
        name=name,
        role=role,
        system_message=system_message,
        llm_config=llm_config,
    )
    return BaseAgent(config)


def create_user_proxy(
    name: str = "user_proxy",
    human_input_mode: str = HumanInputMode.NEVER.value,
) -> UserProxyWrapper:
    """创建用户代理.
    
    Args:
        name: 代理名称
        human_input_mode: 人机交互模式
        
    Returns:
        UserProxyWrapper实例
    """
    return UserProxyWrapper(name=name, human_input_mode=human_input_mode)
