"""AI assistant abstraction."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class AIAssistantConfig:
    enabled: bool
    api_key: str
    model: str
    system_prompt: str


class AIAssistant:
    """High-level AI assistant that can generate suggestions or code."""

    def __init__(self, config: AIAssistantConfig) -> None:
        self.config = config
        self._client: OpenAI | None = None
        if config.enabled:
            self._client = OpenAI(api_key=config.api_key or None)

    def chat(self, messages: Iterable[dict]) -> str:
        if not self.config.enabled:
            return "AI 功能未开启。请在设置中启用并配置 API Key。"
        if not self._client:
            raise RuntimeError("OpenAI 客户端未正确初始化")
        history: List[dict] = [
            {"role": "system", "content": self.config.system_prompt},
            *messages,
        ]
        logger.debug("Sending chat completion request with %d messages", len(history))
        response = self._client.chat.completions.create(model=self.config.model, messages=history)
        return response.choices[0].message.content or ""


def assistant_from_settings(settings: AIAssistantConfig) -> AIAssistant:
    return AIAssistant(settings)
