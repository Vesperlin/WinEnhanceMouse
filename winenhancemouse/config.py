"""Configuration management for WinEnhanceMouse."""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_DIR = Path.home() / ".winenhancemouse"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_config.json"


@dataclass
class ActionBinding:
    """Represents a binding between a menu entry and an action identifier."""

    id: str
    label: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModeConfig:
    """Represents a mode, containing first/second level queue bindings."""

    name: str
    primary_queue: List[ActionBinding] = field(default_factory=list)
    secondary_queue: List[ActionBinding] = field(default_factory=list)


@dataclass
class MenuAppearance:
    position: str = "bottom_right"
    width: int = 320
    row_height: int = 40
    font_size: int = 14


@dataclass
class AISettings:
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    system_prompt: str = "你是 Windows 增强鼠标助手，帮助用户进行高效操作。"
    allow_code_execution: bool = False


@dataclass
class AppConfig:
    modes: List[ModeConfig]
    menu: MenuAppearance
    ai: AISettings


class ConfigManager:
    """Thread-safe configuration manager responsible for loading and persisting settings."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._config: Optional[AppConfig] = None

    def load(self, path: Optional[Path] = None) -> AppConfig:
        path = path or CONFIG_PATH
        with self._lock:
            if not path.exists():
                self._ensure_default_config(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            self._config = self._parse_config(data)
            return self._config

    def save(self, config: Optional[AppConfig] = None, path: Optional[Path] = None) -> None:
        target = path or CONFIG_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            to_persist = config or self.require()
            data = self._serialize_config(to_persist)
            target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def require(self) -> AppConfig:
        with self._lock:
            if not self._config:
                raise RuntimeError("Configuration has not been loaded yet")
            return self._config

    # region Parsing helpers
    def _parse_config(self, data: Dict[str, Any]) -> AppConfig:
        modes = [
            ModeConfig(
                name=mode["name"],
                primary_queue=[ActionBinding(**item) for item in mode.get("bindings", {}).get("primary_queue", [])],
                secondary_queue=[ActionBinding(**item) for item in mode.get("bindings", {}).get("secondary_queue", [])],
            )
            for mode in data.get("modes", [])
        ]
        menu = MenuAppearance(**data.get("menu", {}))
        ai = AISettings(**data.get("ai", {}))
        return AppConfig(modes=modes, menu=menu, ai=ai)

    def _serialize_config(self, config: AppConfig) -> Dict[str, Any]:
        return {
            "modes": [
                {
                    "name": mode.name,
                    "bindings": {
                        "primary_queue": [
                            {"id": binding.id, "label": binding.label, "params": binding.params}
                            for binding in mode.primary_queue
                        ],
                        "secondary_queue": [
                            {"id": binding.id, "label": binding.label, "params": binding.params}
                            for binding in mode.secondary_queue
                        ],
                    },
                }
                for mode in config.modes
            ],
            "menu": {
                "position": config.menu.position,
                "width": config.menu.width,
                "row_height": config.menu.row_height,
                "font_size": config.menu.font_size,
            },
            "ai": {
                "enabled": config.ai.enabled,
                "provider": config.ai.provider,
                "model": config.ai.model,
                "api_key": config.ai.api_key,
                "system_prompt": config.ai.system_prompt,
                "allow_code_execution": config.ai.allow_code_execution,
            },
        }

    # endregion

    def _ensure_default_config(self, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        source = DEFAULT_CONFIG_PATH
        if not source.exists():
            raise FileNotFoundError(f"Default configuration template is missing at {source}")
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


config_manager = ConfigManager()

__all__ = [
    "ActionBinding",
    "ModeConfig",
    "MenuAppearance",
    "AISettings",
    "AppConfig",
    "ConfigManager",
    "config_manager",
]
