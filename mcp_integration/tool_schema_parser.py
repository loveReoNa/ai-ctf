"""Schema parser for LLM-to-Tool mapping - optimizes tool descriptions for agent consumption."""

from typing import Dict, List, Optional

from mcp_integration.mcp_client import ToolSchema


class ToolSchemaParser:
    """Parses tool schemas into LLM-optimized function descriptions.

    Transforms raw MCP tool schemas into concise, token-efficient
    descriptions suitable for inclusion in LLM system prompts.
    """

    def __init__(self, max_description_tokens: int = 500):
        """Initialize schema parser.

        Args:
            max_description_tokens: Estimated max tokens for a single
                tool description in the system prompt.
        """
        self.max_description_tokens = max_description_tokens

    def parse_schema_to_function_def(self, schema: ToolSchema) -> dict:
        """Convert a tool schema to a function definition dict.

        Args:
            schema: Tool schema to convert.

        Returns:
            Function definition compatible with OpenAI function calling format.
        """
        return {
            "type": "function",
            "function": {
                "name": schema.name,
                "description": self._truncate_description(
                    schema.description, schema.server_name
                ),
                "parameters": schema.input_schema,
            },
        }

    def parse_all_schemas(
        self, schemas: List[ToolSchema]
    ) -> List[dict]:
        """Convert all tool schemas to function definitions.

        Args:
            schemas: List of tool schemas.

        Returns:
            List of function definition dicts.
        """
        return [self.parse_schema_to_function_def(s) for s in schemas]

    def generate_tools_markdown(self, schemas: List[ToolSchema]) -> str:
        """Generate a Markdown listing of all tools for the system prompt.

        Args:
            schemas: List of tool schemas to document.

        Returns:
            Markdown-formatted tool listing.
        """
        lines = []
        for schema in schemas:
            lines.append(f"### {schema.name}")
            lines.append(f"- **Category**: {schema.tool_category}")
            lines.append(f"- **Server**: {schema.server_name}")
            lines.append(f"- **Description**: {schema.description}")
            if schema.input_schema:
                props = schema.input_schema.get("properties", {})
                required = schema.input_schema.get("required", [])
                for param_name, param_info in props.items():
                    req_mark = " (required)" if param_name in required else ""
                    lines.append(
                        f"  - `{param_name}`: {param_info.get('description', 'No description')}{req_mark}"
                    )
            lines.append("")
        return "\n".join(lines)

    def generate_tools_prompt_section(self, schemas: List[ToolSchema]) -> str:
        """Generate a compact tool description block for LLM system prompt.

        Args:
            schemas: List of tool schemas.

        Returns:
            Compact prompt text describing all available tools.
        """
        if not schemas:
            return "No tools available."

        lines = ["## Available Tools\n"]
        for schema in schemas:
            params = []
            if schema.input_schema:
                props = schema.input_schema.get("properties", {})
                params = [
                    f"{k} ({v.get('type', 'any')})"
                    for k, v in props.items()
                ]
            param_str = ", ".join(params) if params else "no parameters"
            lines.append(
                f"- **{schema.name}** [{schema.server_name}/{schema.tool_category}]: "
                f"{schema.description} | Params: {param_str}"
            )
        return "\n".join(lines)

    def get_schemas_by_category(
        self, schemas: List[ToolSchema]
    ) -> Dict[str, List[ToolSchema]]:
        """Group schemas by their tool category.

        Args:
            schemas: List of tool schemas.

        Returns:
            Dictionary mapping category names to tool lists.
        """
        categories: Dict[str, List[ToolSchema]] = {}
        for schema in schemas:
            cat = schema.tool_category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(schema)
        return categories

    def _truncate_description(self, description: str, server_name: str) -> str:
        """Truncate description to fit within token budget.

        Args:
            description: Original tool description.
            server_name: Server name for context.

        Returns:
            Potentially truncated description.
        """
        # Simple word-based truncation (1 token ≈ 0.75 words)
        max_words = int(self.max_description_tokens * 0.6)
        words = description.split()
        if len(words) <= max_words:
            return description
        truncated = " ".join(words[:max_words])
        return f"[{server_name}] {truncated}..."


class ToolQualityFilter:
    """Filters tool schemas based on quality metrics.

    Ensures only well-documented, properly specified tools
    are presented to the LLM agent to minimize confusion.
    """

    MIN_DESCRIPTION_LENGTH = 10
    MIN_PARAMETER_DESCRIPTION_QUALITY = 0.3

    def filter_tools(
        self, schemas: List[ToolSchema]
    ) -> tuple[List[ToolSchema], List[ToolSchema]]:
        """Filter tools into accepted and rejected lists.

        Args:
            schemas: List of tool schemas to filter.

        Returns:
            Tuple of (accepted_tools, rejected_tools).
        """
        accepted = []
        rejected = []
        for schema in schemas:
            if self._is_quality_tool(schema):
                accepted.append(schema)
            else:
                rejected.append(schema)
        return accepted, rejected

    def _is_quality_tool(self, schema: ToolSchema) -> bool:
        """Check if a tool schema meets quality standards.

        Args:
            schema: Tool schema to check.

        Returns:
            True if the tool meets quality criteria.
        """
        if len(schema.description.strip()) < self.MIN_DESCRIPTION_LENGTH:
            return False
        if not schema.name or not schema.name.strip():
            return False
        return True

    def compute_quality_score(self, schema: ToolSchema) -> float:
        """Compute a quality score for a tool schema.

        Args:
            schema: Tool schema to score.

        Returns:
            Quality score from 0.0 to 1.0.
        """
        score = 0.0
        # Description completeness
        desc_len = len(schema.description.strip())
        score += min(desc_len / 100.0, 0.4)
        # Has input schema
        if schema.input_schema and schema.input_schema.get("properties"):
            score += 0.3
        # Has category
        if schema.tool_category:
            score += 0.1
        # Has server name
        if schema.server_name:
            score += 0.1
        # Name is meaningful
        if len(schema.name) > 3:
            score += 0.1
        return min(score, 1.0)