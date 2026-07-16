from dataclasses import asdict, dataclass

import yaml
from agents import Agent
from playwright.async_api import Browser, BrowserContext

from app.hooks import CustomAgentHooks
from app.tools.extractor import ExtractorAgentTools
from app.tools.interactor import InteractorAgentTools
from app.tools.navigator import NavigatorAgentTools


@dataclass
class AgentInfo:
    name: str
    instructions: str
    handoff_description: str | None = None


@dataclass
class AgentsSettings:
    interactor: AgentInfo
    extractor: AgentInfo
    navigator: AgentInfo


def load_agents_settings() -> AgentsSettings:
    with open('agents.yaml') as f:
        agents_settings_dict = {
            k: AgentInfo(**v) for k, v in yaml.safe_load(f).items()
        }
        return AgentsSettings(**agents_settings_dict)


def get_main_agent(browser: Browser, context: BrowserContext) -> Agent:
    agents_settings = load_agents_settings()

    extractor_agent_tools = ExtractorAgentTools(browser, context)
    extractor_agent = Agent(
        **asdict(agents_settings.extractor),
        tools=extractor_agent_tools.get_all(),  # type: ignore[arg-type]
        hooks=CustomAgentHooks(),
    )

    navigator_agent_tools = NavigatorAgentTools(browser, context)
    navigator_agent = Agent(
        **asdict(agents_settings.navigator),
        tools=navigator_agent_tools.get_all(),  # type: ignore[arg-type]
        hooks=CustomAgentHooks(),
    )

    interactor_agent_tools = InteractorAgentTools(browser, context)
    interactor_agent = Agent(
        **asdict(agents_settings.interactor),
        tools=interactor_agent_tools.get_all(),  # type: ignore[arg-type]
        handoffs=[extractor_agent, navigator_agent],
        hooks=CustomAgentHooks(),
    )
    return interactor_agent
