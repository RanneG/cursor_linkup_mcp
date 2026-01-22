"""
Sub-Agent System for MCP Server
Enables spawning specialized agents to handle complex tasks autonomously.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Any
from llama_index.llms.ollama import Ollama


class AgentType(Enum):
    RESEARCH = "research"      # Web search + reasoning
    DOCUMENT = "document"      # RAG + reasoning  
    ANALYST = "analyst"        # Pure reasoning (analyze provided context)
    GENERAL = "general"        # All tools available


@dataclass
class AgentResult:
    """Result returned by a sub-agent"""
    success: bool
    report: str
    tool_calls_made: list[str]
    agent_type: str


# System prompts for each agent type
AGENT_PROMPTS = {
    AgentType.RESEARCH: """You are a Research Agent specialized in gathering and synthesizing information from the web.

Your task is to thoroughly research the given topic and provide a comprehensive report.

CAPABILITIES:
- You can search the web for information
- You excel at finding relevant sources and extracting key insights
- You synthesize information from multiple sources

OUTPUT FORMAT:
Provide a structured report with:
1. **Key Findings**: Main discoveries from your research
2. **Details**: Supporting information and context
3. **Sources**: Where you found the information (if available)

Be thorough but concise. Focus on actionable insights.""",

    AgentType.DOCUMENT: """You are a Document Agent specialized in analyzing and querying document collections.

Your task is to find relevant information from the available documents and synthesize an answer.

CAPABILITIES:
- You can query the document database using semantic search
- You excel at finding specific information within documents
- You can synthesize information from multiple document sections

OUTPUT FORMAT:
Provide a structured response with:
1. **Answer**: Direct answer to the query
2. **Supporting Evidence**: Relevant quotes or references from documents
3. **Context**: Additional context that might be helpful

Be precise and cite specific document sections when possible.""",

    AgentType.ANALYST: """You are an Analyst Agent specialized in analyzing data, code, and complex information.

Your task is to analyze the provided context and deliver insights.

CAPABILITIES:
- Deep analysis of code, data, or text
- Pattern recognition and anomaly detection
- Structured reasoning and problem decomposition

OUTPUT FORMAT:
Provide a structured analysis with:
1. **Summary**: High-level overview of your analysis
2. **Findings**: Specific observations and insights
3. **Recommendations**: Actionable suggestions (if applicable)

Be analytical and thorough. Support conclusions with evidence from the context.""",

    AgentType.GENERAL: """You are a General-Purpose Agent capable of handling diverse tasks.

Your task is to complete the assigned work using all available capabilities.

CAPABILITIES:
- Web research for current information
- Document querying for internal knowledge
- Analysis and reasoning for complex problems

OUTPUT FORMAT:
Provide a clear, structured response appropriate to the task:
- For research: findings with sources
- For analysis: insights with supporting evidence
- For questions: direct answers with context

Adapt your approach based on what the task requires."""
}


class SubAgent:
    """
    A sub-agent that can be spawned to handle specific tasks.
    Uses Ollama for reasoning and can optionally use tools.
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        llm: Ollama,
        tools: Optional[dict[str, Callable]] = None
    ):
        self.agent_type = agent_type
        self.llm = llm
        self.tools = tools or {}
        self.system_prompt = AGENT_PROMPTS[agent_type]
        self.tool_calls_made: list[str] = []
    
    async def _call_tool(self, tool_name: str, **kwargs) -> str:
        """Call a tool and return its result"""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not available to this agent"
        
        self.tool_calls_made.append(f"{tool_name}({kwargs})")
        
        tool_func = self.tools[tool_name]
        
        # Handle both sync and async tools
        import asyncio
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**kwargs)
        else:
            result = tool_func(**kwargs)
        
        return str(result)
    
    async def run(self, task: str, context: Optional[str] = None) -> AgentResult:
        """
        Execute the agent's task and return a result.
        
        Args:
            task: The task description for the agent
            context: Optional context/data to provide to the agent
        
        Returns:
            AgentResult with the agent's report
        """
        self.tool_calls_made = []
        
        # Build the full prompt as a single string (LlamaIndex Ollama uses complete() not chat())
        prompt_parts = [
            f"SYSTEM: {self.system_prompt}",
            ""
        ]
        
        # Add context if provided
        if context:
            prompt_parts.append(f"CONTEXT:\n{context}\n")
        
        prompt_parts.append(f"TASK: {task}")
        
        # If agent has tools, explain them
        if self.tools:
            available_tools = ", ".join(self.tools.keys())
            prompt_parts.append(f"\nAVAILABLE TOOLS: {available_tools}")
            prompt_parts.append("Note: Tools will be used on your behalf if needed for your task.")
        
        prompt_parts.append("\nPlease provide your response:")
        
        full_prompt = "\n".join(prompt_parts)
        
        try:
            # For agents with tools, we implement a simple ReAct-style loop
            if self.tools and self.agent_type in [AgentType.RESEARCH, AgentType.DOCUMENT, AgentType.GENERAL]:
                report = await self._run_with_tools(task, context)
            else:
                # Pure reasoning agent - use acomplete for async completion
                response = await self.llm.acomplete(full_prompt)
                report = str(response)
            
            return AgentResult(
                success=True,
                report=report,
                tool_calls_made=self.tool_calls_made,
                agent_type=self.agent_type.value
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                report=f"Agent encountered an error: {str(e)}",
                tool_calls_made=self.tool_calls_made,
                agent_type=self.agent_type.value
            )
    
    async def _run_with_tools(self, task: str, context: Optional[str] = None) -> str:
        """
        Run the agent with tool access using a simplified ReAct pattern.
        The agent first gathers information, then synthesizes a report.
        """
        gathered_info = []
        
        # Step 1: Determine what information is needed
        planning_prompt = f"""You are a planning assistant. Respond only with valid JSON.

Task to complete: {task}

Available tools: {', '.join(self.tools.keys())}

What tool calls would help gather the information needed? 
Respond with a JSON array of tool calls, each with "tool" and "query" keys.
Example: [{{"tool": "web_search", "query": "your search query"}}]

If no tools are needed, respond with an empty array: []
Keep it to 1-3 tool calls maximum.

JSON response:"""

        try:
            planning_response = await self.llm.acomplete(planning_prompt)
            plan_text = str(planning_response).strip()
            
            # Try to parse the plan
            # Handle markdown code blocks if present
            if "```" in plan_text:
                plan_text = plan_text.split("```")[1]
                if plan_text.startswith("json"):
                    plan_text = plan_text[4:]
                plan_text = plan_text.strip()
            
            tool_calls = json.loads(plan_text)
            
            # Step 2: Execute tool calls
            for call in tool_calls[:3]:  # Limit to 3 calls
                tool_name = call.get("tool")
                query = call.get("query", "")
                
                if tool_name in self.tools:
                    result = await self._call_tool(tool_name, query=query)
                    gathered_info.append(f"[{tool_name}] Query: {query}\nResult: {result}\n")
        
        except (json.JSONDecodeError, KeyError, TypeError):
            # If planning fails, try a single relevant tool call
            if "web_search" in self.tools and self.agent_type == AgentType.RESEARCH:
                result = await self._call_tool("web_search", query=task)
                gathered_info.append(f"[web_search] Query: {task}\nResult: {result}\n")
            elif "rag" in self.tools and self.agent_type == AgentType.DOCUMENT:
                result = await self._call_tool("rag", query=task)
                gathered_info.append(f"[rag] Query: {task}\nResult: {result}\n")
        
        # Step 3: Synthesize final report
        synthesis_context = "\n---\n".join(gathered_info) if gathered_info else "No additional information gathered."
        
        if context:
            synthesis_context = f"PROVIDED CONTEXT:\n{context}\n\nGATHERED INFORMATION:\n{synthesis_context}"
        
        synthesis_prompt = f"""{self.system_prompt}

TASK: {task}

INFORMATION GATHERED:
{synthesis_context}

Based on all available information, provide your final report:"""

        response = await self.llm.acomplete(synthesis_prompt)
        return str(response)


class AgentOrchestrator:
    """
    Manages the creation and execution of sub-agents.
    """
    
    def __init__(self, llm: Ollama, tools: Optional[dict[str, Callable]] = None):
        self.llm = llm
        self.available_tools = tools or {}
    
    def _get_agent_tools(self, agent_type: AgentType) -> dict[str, Callable]:
        """Get the tools available to a specific agent type"""
        if agent_type == AgentType.RESEARCH:
            return {k: v for k, v in self.available_tools.items() if k == "web_search"}
        elif agent_type == AgentType.DOCUMENT:
            return {k: v for k, v in self.available_tools.items() if k == "rag"}
        elif agent_type == AgentType.GENERAL:
            return self.available_tools.copy()
        else:  # ANALYST
            return {}
    
    async def spawn(
        self,
        agent_type: str,
        task: str,
        context: Optional[str] = None
    ) -> AgentResult:
        """
        Spawn a sub-agent to handle a task.
        
        Args:
            agent_type: Type of agent ("research", "document", "analyst", "general")
            task: The task for the agent to complete
            context: Optional context/data to provide
        
        Returns:
            AgentResult with the agent's report
        """
        try:
            agent_enum = AgentType(agent_type.lower())
        except ValueError:
            return AgentResult(
                success=False,
                report=f"Unknown agent type: {agent_type}. Available types: {[t.value for t in AgentType]}",
                tool_calls_made=[],
                agent_type=agent_type
            )
        
        agent_tools = self._get_agent_tools(agent_enum)
        agent = SubAgent(agent_enum, self.llm, agent_tools)
        
        return await agent.run(task, context)

