"""Prompts for the fake news detection agents."""

from .router import ROUTER_PROMPT
from .agent_d import AGENT_D_PROMPT
from .agent_t import AGENT_T_PROMPT
from .agent_c import AGENT_C_PROMPT
from .synthesizer import SYNTHESIZER_PROMPT

__all__ = [
    "ROUTER_PROMPT",
    "AGENT_D_PROMPT",
    "AGENT_T_PROMPT",
    "AGENT_C_PROMPT",
    "SYNTHESIZER_PROMPT",
]
