"""Manager for CTF agent system prompts and prompt templates."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PromptTemplate:
    """A prompt template for the CTF agent.

    Attributes:
        name: Template name.
        description: What this template is for.
        content: The actual prompt text.
        variables: Template variables (e.g., {target}, {model}).
    """

    name: str = ""
    description: str = ""
    content: str = ""
    variables: List[str] = field(default_factory=list)


class PromptManager:
    """Manages system prompts and templates for the CTF agent.

    Provides methods to load, render, and customize prompt templates
    for different CTF solving scenarios and tool configurations.
    """

    DEFAULT_PROMPTS = {
        "ctf_solver_default": """You are an AI security agent specialized in solving CTF (Capture The Flag) challenges.
Your goal is to discover vulnerabilities, exploit them, and capture flags from target systems.

Available tools will be provided. Use them according to the following methodology:

## Attack Methodology

### Phase 1: Reconnaissance
- Scan the target for open ports and services
- Identify the operating system and software versions
- Map the attack surface

### Phase 2: Enumeration
- Gather detailed information about discovered services
- Enumerate directories, users, and configurations
- Identify potential vulnerabilities

### Phase 3: Exploitation
- Use appropriate tools to exploit discovered vulnerabilities
- Try multiple attack vectors if initial attempts fail
- Document all attempts and results

### Phase 4: Post-Exploitation
- Search the compromised system for flags
- Escalate privileges if necessary
- Explore lateral movement opportunities

### Phase 5: Flag Capture
- Extract the flag when found
- Verify the flag format
- Report success with complete attack chain documentation

## Rules
- Use tools sequentially and analyze results before deciding next steps
- If a tool fails, try alternative approaches
- Record all findings including failed attempts
- Think step-by-step about the attack surface
- Capture flags in format: flag{{...}}""",

        "naive_baseline": """You are a basic security testing agent.
Your task is to scan the target {target} and find any open ports or services.

Use the available tools to:
1. Scan the target for open ports
2. Report what you find

Be thorough but efficient. Flag format: flag{{...}}""",

        "tool_rich": """You are an advanced AI security agent with access to a comprehensive tool suite.

## Available Tools
{tools_list}

## Target Information
- Host: {target}
- Port Range: {ports}

## Objective
Find and capture the flag from the target system.

## Instructions
1. Start with reconnaissance using appropriate scanning tools
2. Based on results, enumerate services and find vulnerabilities
3. Exploit vulnerabilities and gain access
4. Search for flags and capture them

Be methodical, document your steps, and persist through failures.
Flag pattern: {flag_pattern}""",

        "explainable_chain_of_thought": """You are an AI security agent that MUST explain every decision.

For each action you take, provide:
- **Observation**: What you currently know about the target
- **Hypothesis**: What vulnerability you suspect exists
- **Action**: What tool you will use and why
- **Expected Outcome**: What you expect to happen
- **Actual Result**: What actually happened
- **Next Step**: What you will do next based on the result

This chain-of-thought reasoning MUST be included in your responses.

Target: {target}

Use the available tools methodically. Capture flags in format: flag{{...}}""",
    }

    def __init__(self, prompts_dir: Optional[str] = None):
        """Initialize prompt manager.

        Args:
            prompts_dir: Optional directory containing .md prompt files.
        """
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
        if prompts_dir:
            self.load_from_directory(prompts_dir)

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name.

        Args:
            name: Template name.

        Returns:
            PromptTemplate or None if not found.
        """
        return self._templates.get(name)

    def render_prompt(self, name: str, variables: Optional[dict] = None) -> str:
        """Render a prompt template with variable substitution.

        Args:
            name: Template name.
            variables: Dictionary of variable values.

        Returns:
            Rendered prompt string.
        """
        template = self._templates.get(name)
        if not template:
            return ""

        content = template.content
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                content = content.replace(placeholder, str(value))

        return content

    def list_templates(self) -> List[str]:
        """List all available template names.

        Returns:
            List of template names.
        """
        return list(self._templates.keys())

    def add_template(self, template: PromptTemplate) -> None:
        """Add a new prompt template.

        Args:
            template: Prompt template to add.
        """
        self._templates[template.name] = template

    def load_from_directory(self, directory: str) -> int:
        """Load prompt templates from a directory of markdown files.

        Args:
            directory: Path to directory containing .md files.

        Returns:
            Number of templates loaded.
        """
        count = 0
        try:
            if os.path.isdir(directory):
                for filename in os.listdir(directory):
                    if filename.endswith(".md"):
                        filepath = os.path.join(directory, filename)
                        name = filename.replace(".md", "")
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        self._templates[name] = PromptTemplate(
                            name=name,
                            description=f"Loaded from {filename}",
                            content=content,
                            variables=self._extract_variables(content),
                        )
                        count += 1
        except Exception as e:
            print(f"Error loading prompts from directory: {e}")
        return count

    def get_ctf_prompt_with_tools(self, tools_description: str, target: str) -> str:
        """Generate a CTF solver prompt with tool descriptions.

        Args:
            tools_description: Description of available tools.
            target: Target host/IP.

        Returns:
            Complete system prompt with tool information.
        """
        base_prompt = self.render_prompt("ctf_solver_default")
        return f"{base_prompt}\n\n## Available Tools\n{tools_description}\n\nTarget: {target}"

    def get_baseline_prompt(self, target: str) -> str:
        """Generate a baseline (naive) agent prompt.

        Args:
            target: Target host/IP.

        Returns:
            Baseline prompt string.
        """
        return self.render_prompt("naive_baseline", {"target": target})

    def get_explainable_prompt(self, target: str) -> str:
        """Generate an explainable chain-of-thought prompt.

        Args:
            target: Target host/IP.

        Returns:
            Explainable prompt string.
        """
        return self.render_prompt("explainable_chain_of_thought", {"target": target})

    def _load_default_templates(self) -> None:
        """Load built-in default prompt templates."""
        for name, content in self.DEFAULT_PROMPTS.items():
            self._templates[name] = PromptTemplate(
                name=name,
                description=f"Built-in {name} template",
                content=content,
                variables=self._extract_variables(content),
            )

    @staticmethod
    def _extract_variables(content: str) -> List[str]:
        """Extract template variables from content.

        Args:
            content: Template content with {variable} placeholders.

        Returns:
            List of variable names.
        """
        import re

        matches = re.findall(r"\{(\w+)\}", content)
        # Filter out escaped braces
        return [m for m in matches if not m.startswith("{")]