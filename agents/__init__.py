"""Specialized agents for fake news detection."""

from .base import BaseAgent
from .agent_d import agent_d_node
from .agent_t import agent_t_node
from .agent_c import agent_c_node

__all__ = ["BaseAgent", "agent_d_node", "agent_t_node", "agent_c_node"]
