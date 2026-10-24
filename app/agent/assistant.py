"""OpenAI Agents SDK Agent 정의.

아직 도구를 연결하지 않았습니다(TOOLS 는 빈 목록).
ITSM 도구를 추가할 위치는 TOOLS 와 README 의 "도구를 추가할 위치"를, ITSM 연동 문서는 docs/itsm/ 을 참고하세요.
"""

from __future__ import annotations

from agents import Agent, Model, ModelSettings, Tool
from openai.types.shared import Reasoning

from app.agent.context import AgentUserContext
from app.config import AGENT_REASONING_EFFORT

# 이후 실험에서 ITSM 도구를 이 목록에 등록합니다. 현재는 비어 있어야 합니다.
TOOLS: list[Tool] = []

INSTRUCTIONS = "당신은 사내 IT 서비스 관리(ITSM) 시스템을 쓰는 동료들을 돕는 친절한 도우미 친구입니다. 한국어로 간결하게 답합니다."


def build_agent(model: str | Model) -> Agent[AgentUserContext]:
    return Agent[AgentUserContext](
        name="ITSM Assistant",
        instructions=INSTRUCTIONS,
        model=model,
        model_settings=ModelSettings(reasoning=Reasoning(effort=AGENT_REASONING_EFFORT)),
        tools=list(TOOLS),
    )
