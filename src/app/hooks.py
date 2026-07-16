from typing import Any

from agents import Agent, AgentHooks, FunctionTool, RunContextWrapper
from agents.tool import Tool

from app.logging import logger

MAX_TOOL_RESULT_LENGTH = 100


class CustomAgentHooks(AgentHooks):
    async def on_handoff(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        source: Agent[Any],
    ) -> None:
        logger.info(f'{source.name} uses {agent.name}\n')

    async def on_tool_start(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        tool: Tool,
    ) -> None:
        if not isinstance(tool, FunctionTool):
            return

        msg = f'{agent.name} uses {tool.name}'
        args = getattr(context, 'tool_arguments', None)
        if args and args != '{}':
            msg += f' with {context.tool_arguments}'  # type: ignore[attr-defined]
        logger.info(msg)

    async def on_tool_end(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        tool: Tool,
        result: object,
    ) -> None:
        if not isinstance(tool, FunctionTool):
            return

        logger.info(f'Result: {str(result)[:MAX_TOOL_RESULT_LENGTH]}...\n')
