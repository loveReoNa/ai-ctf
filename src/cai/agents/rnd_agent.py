"""
R&D Agent - General Purpose Security Research Agent
"""
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

from cai.sdk.agents import Agent, OpenAIChatCompletionsModel
from cai.util import create_system_prompt_renderer
from cai.agents.guardrails import get_security_guardrails

# Core reconnaissance tools
from cai.tools.reconnaissance.generic_linux_command import generic_linux_command
from cai.tools.reconnaissance.exec_code import execute_code
from cai.tools.reconnaissance.nmap import nmap
from cai.tools.reconnaissance.shodan import shodan_search, shodan_host_info
from cai.tools.reconnaissance.crypto_tools import strings_command, decode64, decode_hex_bytes

# Web security tools
from cai.tools.web.headers import web_request_framework
from cai.tools.web.js_surface_mapper import js_surface_mapper

# Network tools
from cai.tools.network.capture_traffic import capture_remote_traffic

# Web search tools (conditional)
from cai.tools.web.search_web import make_web_search_with_explanation

load_dotenv()
model_name = os.getenv("CAI_MODEL", "alias1")

# Determine API key
api_key = os.getenv("ALIAS_API_KEY", os.getenv("OPENAI_API_KEY", "sk-alias-1234567890"))

# Instructions for R&D Agent - General purpose with wide coverage
instructions = """You are an R&D (Research and Development) Security Agent with broad expertise across multiple cybersecurity domains.

Your primary objective is to conduct comprehensive security research, analysis, and problem-solving across diverse scenarios including:

## DOMAIN EXPERTISE:
1. **Network Security**: Port scanning, traffic analysis, network reconnaissance
2. **Web Application Security**: Vulnerability assessment, API testing, JS analysis
3. **System Security**: Linux command execution, code analysis, system enumeration
4. **Cryptographic Analysis**: Encryption/decryption, hash analysis, crypto challenges
5. **Threat Intelligence**: Shodan searches, OSINT gathering, threat hunting
6. **Incident Response**: Forensic analysis, log examination, attack investigation

## TOOL USAGE GUIDELINES:
- Use `generic_linux_command` for system-level operations and shell commands
- Use `execute_code` for running scripts, parsing data, or custom analysis
- Use `nmap` for network reconnaissance and port scanning
- Use `shodan_search` and `shodan_host_info` for external intelligence gathering
- Use `strings_command`, `decode64`, and `decode_hex_bytes` for cryptographic operations and analysis
- Use `web_request_framework` for HTTP-based security testing
- Use `js_surface_mapper` for JavaScript analysis in web applications
- Use `capture_remote_traffic` for network traffic analysis when needed

## PROBLEM-SOLVING APPROACH:
1. **Assess**: Understand the problem scope and requirements
2. **Plan**: Develop a systematic approach using appropriate tools
3. **Execute**: Carry out investigations methodically
4. **Analyze**: Interpret results and identify patterns
5. **Report**: Provide clear findings and recommendations

## SAFETY AND ETHICS:
- Always operate within authorized boundaries
- Respect privacy and data protection regulations
- Document your methodology for reproducibility
- Prioritize defensive security when appropriate

You are versatile and adaptive - tackle challenges across the cybersecurity spectrum with thoroughness and precision."""

# Assemble comprehensive toolset
tools = [
    # Core system tools
    generic_linux_command,
    execute_code,
    
    # Network reconnaissance
    nmap,
    
    # Web security tools
    web_request_framework,
    js_surface_mapper,
    
    # Cryptographic tools
    strings_command,
    decode64,
    decode_hex_bytes,
    
    # Network analysis
    capture_remote_traffic,
]

# Add Shodan tools if API key is available
if os.getenv("SHODAN_API_KEY"):
    tools.extend([shodan_search, shodan_host_info])

# Add web search if API key is available
if os.getenv("PERPLEXITY_API_KEY"):
    tools.append(make_web_search_with_explanation)

# Get security guardrails
input_guardrails, output_guardrails = get_security_guardrails()

# Instantiate the R&D Agent
rnd_agent = Agent(
    name="rnd_agent",
    description="""General-purpose security research agent with broad expertise across multiple cybersecurity domains.
                   Capable of network analysis, web security testing, cryptographic analysis, system reconnaissance,
                   and comprehensive security research.""",
    instructions=create_system_prompt_renderer(instructions),
    tools=tools,
    input_guardrails=input_guardrails,
    output_guardrails=output_guardrails,
    model=OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=AsyncOpenAI(api_key=api_key),
    ),
)

def transfer_to_rnd_agent(**kwargs):  # pylint: disable=unused-argument
    """
    Transfer to R&D Agent.
    Accepts arbitrary kwargs for compatibility; returns the agent instance.
    """
    return rnd_agent