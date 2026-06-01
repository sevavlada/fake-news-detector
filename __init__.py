"""
Fake News Detection Multi-Agent System

A LangGraph-based system with three specialized agents:
- Agent D: Data-based Cross-checking
- Agent T: Textual & Discourse Analysis
- Agent C: Contextual & Source Analysis
"""

from .state import FakeNewsAgentState
from .config import get_llm

__version__ = "0.1.0"
__all__ = ["FakeNewsAgentState", "get_llm"]
