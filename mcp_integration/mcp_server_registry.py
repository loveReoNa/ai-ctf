"""MCP server registry for managing all available MCP servers."""

from typing import Dict, List, Optional

from mcp_integration.mcp_client import (
    MCPClient,
    MCPConnectionConfig,
    ToolSchema,
    TransportType,
)


class MCPServerRegistry:
    """Registry of all MCP servers available for agent tool use.

    Manages registration, discovery, health checking, and aggregated
    tool listing across all connected servers.
    """

    def __init__(self, registry_file: Optional[str] = None):
        """Initialize the server registry.

        Args:
            registry_file: Optional path to a JSON config file.
        """
        self._servers: Dict[str, MCPConnectionConfig] = {}
        self._clients: Dict[str, MCPClient] = {}
        if registry_file:
            self._load_from_file(registry_file)

    def load_from_livemcpbench(self, config_path: str) -> int:
        """Load server configurations from a LiveMCPBench-style config directory.

        Args:
            config_path: Path to LiveMCPBench server configuration directory.

        Returns:
            Number of server configs loaded.
        """
        count = 0
        try:
            import json
            import os

            if os.path.isdir(config_path):
                for filename in os.listdir(config_path):
                    if filename.endswith(".json"):
                        filepath = os.path.join(config_path, filename)
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            config = MCPConnectionConfig(
                                server_name=data.get("name", filename.replace(".json", "")),
                                transport_type=TransportType(
                                    data.get("transport", "stdio")
                                ),
                                command=data.get("command"),
                                args=data.get("args", []),
                                url=data.get("url"),
                            )
                            self.register_server(config)
                            count += 1
        except Exception as e:
            print(f"Error loading LiveMCPBench config: {e}")
            return 0
        return count

    def register_server(self, config: MCPConnectionConfig) -> None:
        """Register a new MCP server configuration.

        Args:
            config: Server connection configuration.
        """
        self._servers[config.server_name] = config

    def get_server(self, name: str) -> Optional[MCPConnectionConfig]:
        """Get a server's configuration by name.

        Args:
            name: Server name.

        Returns:
            Server config or None if not found.
        """
        return self._servers.get(name)

    def list_servers(self) -> Dict[str, MCPConnectionConfig]:
        """List all registered server configurations.

        Returns:
            Dictionary mapping server names to their configs.
        """
        return dict(self._servers)

    def health_check(self, server_name: str) -> bool:
        """Check if a specific server is healthy.

        Args:
            server_name: Name of server to check.

        Returns:
            True if server responds, False otherwise.
        """
        try:
            client = self._get_or_create_client(server_name)
            if client and not client._connected:
                return client.connect()
            return client is not None and client._connected
        except Exception:
            return False

    def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered servers.

        Returns:
            Dictionary mapping server names to health status.
        """
        results = {}
        for name in self._servers:
            results[name] = self.health_check(name)
        return results

    def get_all_tools(self) -> Dict[str, List[ToolSchema]]:
        """Get tools from all registered servers.

        Returns:
            Dictionary mapping server names to their tool lists.
        """
        all_tools = {}
        for name in self._servers:
            client = self._get_or_create_client(name)
            if client and client._connected:
                tools = client.list_tools()
                all_tools[name] = tools
        return all_tools

    def _get_or_create_client(self, server_name: str) -> Optional[MCPClient]:
        """Get existing client or create a new one.

        Args:
            server_name: Server name.

        Returns:
            MCPClient instance or None if server not registered.
        """
        config = self._servers.get(server_name)
        if not config:
            return None
        if server_name not in self._clients:
            self._clients[server_name] = MCPClient(config)
        return self._clients[server_name]

    def _load_from_file(self, filepath: str) -> None:
        """Load server configurations from a JSON file.

        Args:
            filepath: Path to JSON config file.
        """
        try:
            import json

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for server_data in data.get("servers", []):
                config = MCPConnectionConfig(
                    server_name=server_data.get("name", ""),
                    transport_type=TransportType(server_data.get("transport", "stdio")),
                    command=server_data.get("command"),
                    args=server_data.get("args", []),
                    url=server_data.get("url"),
                )
                self.register_server(config)
        except Exception as e:
            print(f"Error loading registry file: {e}")


class LiveMCPBenchLoader:
    """Loader for LiveMCPBench benchmark server configurations.

    Parses LiveMCPBench's server configuration format and registers
    servers with the registry.
    """

    def __init__(self, registry: MCPServerRegistry):
        """Initialize loader with a registry.

        Args:
            registry: The server registry to populate.
        """
        self.registry = registry

    def load_mcp_bench_config(self, bench_path: str) -> List[MCPConnectionConfig]:
        """Load and parse LiveMCPBench server configurations.

        Args:
            bench_path: Path to LiveMCPBench configuration directory.

        Returns:
            List of parsed server configurations.
        """
        configs = []
        try:
            import json
            import os

            if os.path.isdir(bench_path):
                for filename in os.listdir(bench_path):
                    if filename.endswith(".json"):
                        filepath = os.path.join(bench_path, filename)
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            config = MCPConnectionConfig(
                                server_name=data.get("name", filename.replace(".json", "")),
                                transport_type=TransportType(
                                    data.get("transport", "stdio")
                                ),
                                command=data.get("command"),
                                args=data.get("args", []),
                                url=data.get("url"),
                                timeout_seconds=data.get("timeout", 30),
                            )
                            configs.append(config)
                            self.registry.register_server(config)
        except Exception as e:
            print(f"Error loading MCP bench config: {e}")
        return configs

    def discover_tools(self) -> Dict[str, int]:
        """Auto-discover tools from all registered servers.

        Returns:
            Dictionary mapping server names to their tool counts.
        """
        tool_counts = {}
        all_tools = self.registry.get_all_tools()
        for server_name, tools in all_tools.items():
            tool_counts[server_name] = len(tools)
        return tool_counts