"""AgentExecutor는 도구 호출 시 RunnableConfig를 넘기지 않아, 세션 ID는 ContextVar로 전달합니다."""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

agent_session_id_ctx: ContextVar[Optional[UUID]] = ContextVar(
    "agent_session_id", default=None
)
