"""Core runtime engine handling hooks and menu interaction."""
from __future__ import annotations

import logging
import threading
import time
from typing import List, Optional

from pynput import keyboard, mouse

from .actions import registry
from .ai import AIAssistantConfig, assistant_from_settings
from .config import ActionBinding, AppConfig, ModeConfig, config_manager
from .gui.ai_window import AIWindow
from .gui.menu_overlay import MenuItem, MenuOverlay
from .gui.settings_window import SettingsWindow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self) -> None:
        self._config = config_manager.load()
        self._current_mode_index = 0
        self._overlay = MenuOverlay(
            appearance=self._config.menu,
            on_select=self._handle_select,
            on_cancel=self._handle_cancel,
        )
        ai_config = self._build_ai_config(self._config)
        self._assistant = assistant_from_settings(ai_config)
        self._ai_window: Optional[AIWindow] = None

        self._menu_lock = threading.RLock()
        self._menu_active = False
        self._primary_queue: List[ActionBinding] = []
        self._secondary_queue: List[ActionBinding] = []
        self._last_left_click = 0.0
        self._settings_open = False
        self._ai_active = False

        self._mouse_listener = mouse.Listener(on_click=self._on_click, on_scroll=self._on_scroll)
        self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)

    def start(self) -> None:
        logger.info("Starting WinEnhanceMouse engine")
        self._mouse_listener.start()
        self._keyboard_listener.start()
        self._mouse_listener.join()
        self._keyboard_listener.join()

    # Event handlers -----------------------------------------------------
    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not pressed:
            return
        if button == mouse.Button.middle:
            self._toggle_menu()
        elif not self._menu_active:
            return
        elif button == mouse.Button.left:
            self._handle_left_click()
        elif button == mouse.Button.right:
            self._handle_right_click()
        elif button == mouse.Button.x1:
            self._open_settings()
        elif button == mouse.Button.x2:
            self._execute_queues()

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self._menu_active:
            return
        if dy > 0:
            self._overlay.focus_prev()
        else:
            self._overlay.focus_next()

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == keyboard.Key.esc and self._menu_active:
            self._toggle_menu(force_close=True)
        if key == keyboard.Key.f9:
            self._toggle_ai_window()

    # Menu lifecycle -----------------------------------------------------
    def _toggle_menu(self, force_close: bool = False) -> None:
        with self._menu_lock:
            if self._menu_active and not force_close:
                logger.debug("Closing menu from toggle")
                self._overlay.close()
                self._menu_active = False
                return
            if force_close:
                self._overlay.close()
                self._menu_active = False
                return
            logger.debug("Opening menu")
            mode = self._current_mode
            items = [
                MenuItem(binding=binding, queue_level=1) for binding in mode.primary_queue
            ] + [
                MenuItem(binding=binding, queue_level=2) for binding in mode.secondary_queue
            ]
            self._overlay.open(items)
            self._primary_queue.clear()
            self._secondary_queue.clear()
            self._menu_active = True

    def _handle_left_click(self) -> None:
        now = time.time()
        double_click = now - self._last_left_click < 0.35
        self._last_left_click = now
        focused = self._current_focus_binding()
        if not focused:
            return
        if double_click:
            logger.debug("Adding %s to secondary queue", focused.id)
            self._secondary_queue.append(focused)
        else:
            logger.debug("Adding %s to primary queue", focused.id)
            self._primary_queue.append(focused)

    def _handle_right_click(self) -> None:
        if self._primary_queue:
            removed = self._primary_queue.pop()
            logger.debug("Removed %s from primary queue", removed.id)
        elif self._secondary_queue:
            removed = self._secondary_queue.pop()
            logger.debug("Removed %s from secondary queue", removed.id)
        else:
            self._toggle_menu(force_close=True)

    def _handle_select(self, item: MenuItem) -> None:
        if item.queue_level == 1:
            self._primary_queue.append(item.binding)
        else:
            self._secondary_queue.append(item.binding)

    def _handle_cancel(self) -> None:
        self._toggle_menu(force_close=True)

    def _current_focus_binding(self) -> Optional[ActionBinding]:
        mode = self._current_mode
        all_items = mode.primary_queue + mode.secondary_queue
        if not all_items:
            return None
        index = max(0, min(len(all_items) - 1, self._overlay.focus_index))
        return all_items[index]

    def _execute_queues(self) -> None:
        logger.info("Executing %d primary and %d secondary actions", len(self._primary_queue), len(self._secondary_queue))
        for binding in self._primary_queue:
            registry.execute(binding.id, binding.params)
        for binding in self._secondary_queue:
            registry.execute(binding.id, binding.params)
        self._toggle_menu(force_close=True)

    def _open_settings(self) -> None:
        if self._settings_open:
            return
        self._settings_open = True
        try:
            window = SettingsWindow(self._config)
            window.show()
            self._config = config_manager.require()
            self._overlay.appearance = self._config.menu
            self._assistant = assistant_from_settings(self._build_ai_config(self._config))
        finally:
            self._settings_open = False

    # AI integration ------------------------------------------------------
    def _toggle_ai_window(self) -> None:
        if not self._config.ai.enabled:
            logger.info("AI 功能未启用")
            return
        if self._ai_window:
            logger.debug("Closing AI window")
            self._ai_window._root.destroy()
            self._ai_window = None
            return
        self._ai_window = AIWindow(self._assistant)
        threading.Thread(target=self._ai_window.show, daemon=True).start()

    # Helpers -------------------------------------------------------------
    @property
    def _current_mode(self) -> ModeConfig:
        if not self._config.modes:
            raise RuntimeError("配置中没有可用模式")
        return self._config.modes[self._current_mode_index]

    def _build_ai_config(self, config: AppConfig) -> AIAssistantConfig:
        return AIAssistantConfig(
            enabled=config.ai.enabled,
            api_key=config.ai.api_key,
            model=config.ai.model,
            system_prompt=config.ai.system_prompt,
        )


__all__ = ["Engine"]
