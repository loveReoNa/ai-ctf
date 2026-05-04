"""MCP Integration Module for AI-driven CTF challenge solving.

This module provides:
- MCP protocol client for communication with security tool servers (MCPClient)
- Server registry for managing multiple MCP servers (MCPServerRegistry)
- Tool schema parser for LLM-to-tool mapping (ToolSchemaParser)
- CTF agent orchestrator for automated challenge solving (CTFAgentOrchestrator)
- Prompt management for agent system prompts (PromptManager)
- Structured logging schemas for tool calls and agent state
"""

from mcp_integration.agent_orchestrator import CTFAgentOrchestrator, RunConfig, RunSummary
from mcp_integration.mcp_client import (
    MCPClient,
    MCPConnectionConfig,
    ServerInfo,
    ToolCallResult,
    ToolSchema,
    TransportType,
)
from mcp_integration.mcp_server_registry import LiveMCPBenchLoader, MCPServerRegistry
from mcp_integration.prompts.prompt_manager import PromptManager
from mcp_integration.schemas.agent_state_schema import (
    AgentState,
    AttackPhase,
    ErrorRecord,
    VulnInfo,
)
from mcp_integration.schemas.tool_call_schema import LoggedToolCall, TokenUsage
from mcp_integration.tool_schema_parser import ToolQualityFilter, ToolSchemaParser

__all__ = [
    # Client
    "MCPClient",
    "MCPConnectionConfig",
    "ToolSchema",
    "ToolCallResult",
    "ServerInfo",
    "TransportType",
    # Registry
    "MCPServerRegistry",
    "LiveMCPBenchLoader",
    # Schema Parser
    "ToolSchemaParser",
    "ToolQualityFilter",
    # Orchestrator
    "CTFAgentOrchestrator",
    "RunConfig",
    "RunSummary",
    # Prompts
    "PromptManager",
    # Schemas
    "AgentState",
    "AttackPhase",
    "ErrorRecord",
    "VulnInfo",
    "LoggedToolCall",
    "TokenUsage",
]