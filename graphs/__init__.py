"""LangGraph architectures for fake news detection."""

from .architecture_a import create_router_graph
from .architecture_b import create_parallel_graph

__all__ = ["create_router_graph", "create_parallel_graph"]
