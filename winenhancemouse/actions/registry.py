"""Action registry mapping identifiers to executable routines."""
from __future__ import annotations

import logging
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional

import pyautogui
import pyperclip

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05


@dataclass
class ActionContext:
    """Context that is passed to an action when executed."""

    params: Dict[str, Any]


ActionCallable = Callable[[ActionContext], None]


class ActionRegistry:
    """Registry for mapping action identifiers to callables."""

    def __init__(self) -> None:
        self._actions: Dict[str, ActionCallable] = {}

    def register(self, identifier: str, handler: ActionCallable) -> None:
        if identifier in self._actions:
            raise ValueError(f"Action '{identifier}' already registered")
        self._actions[identifier] = handler
        logger.debug("Registered action %s", identifier)

    def execute(self, identifier: str, params: Optional[Dict[str, Any]] = None) -> None:
        if identifier not in self._actions:
            raise KeyError(f"Unknown action '{identifier}'")
        context = ActionContext(params=params or {})
        logger.info("Executing action %s with params %s", identifier, context.params)
        self._actions[identifier](context)

    def ids(self) -> Iterable[str]:
        return self._actions.keys()


registry = ActionRegistry()


# Helper functions ------------------------------------------------------------

def _hotkey(*keys: str) -> None:
    normalized = ["winleft" if key == "win" else key for key in keys]
    pyautogui.hotkey(*normalized)


def _press(keys: str) -> None:
    _hotkey(*keys.split("+"))


def _type(text: str) -> None:
    pyautogui.typewrite(text)


# Browser & clipboard ---------------------------------------------------------


def _browser_search_clipboard(ctx: ActionContext) -> None:
    text = pyperclip.paste()
    if text:
        pyautogui.hotkey("ctrl", "l")
        _type(text)
        pyautogui.press("enter")


registry.register("browser_search_clipboard", _browser_search_clipboard)


def _browser_search_selection(ctx: ActionContext) -> None:
    backup = pyperclip.paste()
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.1)
    text = pyperclip.paste()
    if text:
        pyautogui.hotkey("ctrl", "l")
        _type(text)
        pyautogui.press("enter")
    pyperclip.copy(backup)


registry.register("browser_search_selection", _browser_search_selection)


def _browser_new_tab(ctx: ActionContext) -> None:
    _press("ctrl+t")


registry.register("browser_new_tab", _browser_new_tab)


def _browser_close_tab(ctx: ActionContext) -> None:
    _press("ctrl+w")


registry.register("browser_close_tab", _browser_close_tab)


def _browser_next_tab(ctx: ActionContext) -> None:
    _press("ctrl+tab")


registry.register("browser_next_tab", _browser_next_tab)


def _browser_prev_tab(ctx: ActionContext) -> None:
    _press("ctrl+shift+tab")


registry.register("browser_prev_tab", _browser_prev_tab)


def _browser_devtools(ctx: ActionContext) -> None:
    _press("ctrl+shift+i")


registry.register("browser_devtools", _browser_devtools)


def _browser_top(ctx: ActionContext) -> None:
    _press("home")


registry.register("browser_top", _browser_top)


def _browser_translate_page(ctx: ActionContext) -> None:
    backup = pyperclip.paste()
    pyautogui.hotkey("ctrl", "l")
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.1)
    url = pyperclip.paste()
    pyautogui.hotkey("ctrl", "l")
    _type(f"https://translate.google.com/translate?sl=auto&tl=zh-CN&u={url}")
    pyautogui.press("enter")
    pyperclip.copy(backup)


registry.register("browser_translate_page", _browser_translate_page)


def _open_url(ctx: ActionContext) -> None:
    url = ctx.params.get("url")
    if not url:
        raise ValueError("'url' parameter required")
    webbrowser.open(url)


registry.register("open_url", _open_url)


def _clipboard_history(ctx: ActionContext) -> None:
    _press("win+v")


registry.register("clipboard_history", _clipboard_history)


def _screen_capture(ctx: ActionContext) -> None:
    _press("win+shift+s")


registry.register("screen_capture", _screen_capture)


def _browser_back(ctx: ActionContext) -> None:
    _press("alt+left")


registry.register("browser_back", _browser_back)


def _browser_forward(ctx: ActionContext) -> None:
    _press("alt+right")


registry.register("browser_forward", _browser_forward)


def _browser_settings(ctx: ActionContext) -> None:
    pyautogui.hotkey("ctrl", "l")
    _type("chrome://settings/")
    pyautogui.press("enter")


registry.register("browser_open_settings", _browser_settings)


def _browser_search_in_page(ctx: ActionContext) -> None:
    _press("ctrl+f")


registry.register("browser_search_in_page", _browser_search_in_page)


# Window management ----------------------------------------------------------

def _window_minimize(ctx: ActionContext) -> None:
    _press("win+down")


registry.register("window_minimize", _window_minimize)


def _window_maximize(ctx: ActionContext) -> None:
    _press("win+up")


registry.register("window_maximize", _window_maximize)


def _window_restore(ctx: ActionContext) -> None:
    _press("win+down")


registry.register("window_restore", _window_restore)


def _window_left(ctx: ActionContext) -> None:
    _press("win+left")


registry.register("window_left", _window_left)


def _window_right(ctx: ActionContext) -> None:
    _press("win+right")


registry.register("window_right", _window_right)


def _window_task_view(ctx: ActionContext) -> None:
    _press("win+tab")


registry.register("window_task_view", _window_task_view)


def _window_snap_layout(index: int) -> None:
    _hotkey("win", "z")
    time.sleep(0.2)
    pyautogui.press(str(index))


def _snap_top(ctx: ActionContext) -> None:
    layout = ctx.params.get("layout", 1)
    _window_snap_layout(layout)


registry.register("window_snap_top", _snap_top)


def _snap_bottom(ctx: ActionContext) -> None:
    layout = ctx.params.get("layout", 2)
    _window_snap_layout(layout)


registry.register("window_snap_bottom", _snap_bottom)


def _snap_free(ctx: ActionContext) -> None:
    layout = ctx.params.get("layout", 3)
    _window_snap_layout(layout)


registry.register("window_snap_layout", _snap_free)


def _window_desktop_new(ctx: ActionContext) -> None:
    _press("win+ctrl+d")


registry.register("desktop_new", _window_desktop_new)


def _window_desktop_close(ctx: ActionContext) -> None:
    _press("win+ctrl+f4")


registry.register("desktop_close", _window_desktop_close)


def _window_prev_desktop(ctx: ActionContext) -> None:
    _press("win+ctrl+left")


registry.register("desktop_prev", _window_prev_desktop)


def _window_next_desktop(ctx: ActionContext) -> None:
    _press("win+ctrl+right")


registry.register("desktop_next", _window_next_desktop)


def _show_desktop(ctx: ActionContext) -> None:
    _press("win+d")


registry.register("show_desktop", _show_desktop)


def _toggle_pin(ctx: ActionContext) -> None:
    _press("win+ctrl+t")


registry.register("toggle_pin", _toggle_pin)


def _switch_window(ctx: ActionContext) -> None:
    _press("alt+tab")


registry.register("switch_window", _switch_window)


def _close_window(ctx: ActionContext) -> None:
    _press("alt+f4")


registry.register("window_close", _close_window)


# System control & media -----------------------------------------------------

def _refresh(ctx: ActionContext) -> None:
    _press("f5")


registry.register("refresh", _refresh)


def _play_pause(ctx: ActionContext) -> None:
    pyautogui.press("playpause")


registry.register("toggle_play_pause", _play_pause)


def _media_prev(ctx: ActionContext) -> None:
    pyautogui.press("prevtrack")


registry.register("media_prev", _media_prev)


def _media_next(ctx: ActionContext) -> None:
    pyautogui.press("nexttrack")


registry.register("media_next", _media_next)


def _volume_up(ctx: ActionContext) -> None:
    steps = int(ctx.params.get("steps", 1))
    for _ in range(steps):
        pyautogui.press("volumeup")


registry.register("volume_up", _volume_up)


def _volume_down(ctx: ActionContext) -> None:
    steps = int(ctx.params.get("steps", 1))
    for _ in range(steps):
        pyautogui.press("volumedown")


registry.register("volume_down", _volume_down)


def _mute(ctx: ActionContext) -> None:
    pyautogui.press("volumemute")


registry.register("volume_mute", _mute)


def _lock_screen(ctx: ActionContext) -> None:
    _press("win+l")


registry.register("lock_screen", _lock_screen)


def _sleep(ctx: ActionContext) -> None:
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], check=False)


registry.register("sleep", _sleep)


def _task_manager(ctx: ActionContext) -> None:
    _press("ctrl+shift+esc")


registry.register("task_manager", _task_manager)


def _shutdown(ctx: ActionContext) -> None:
    subprocess.run(["shutdown", "/s", "/t", "0"], check=False)


registry.register("shutdown", _shutdown)


def _restart(ctx: ActionContext) -> None:
    subprocess.run(["shutdown", "/r", "/t", "0"], check=False)


registry.register("restart", _restart)


# Text editing ---------------------------------------------------------------

def _copy(ctx: ActionContext) -> None:
    _press("ctrl+c")


registry.register("copy", _copy)


def _paste(ctx: ActionContext) -> None:
    _press("ctrl+v")


registry.register("paste", _paste)


def _cut(ctx: ActionContext) -> None:
    _press("ctrl+x")


registry.register("cut", _cut)


def _undo(ctx: ActionContext) -> None:
    _press("ctrl+z")


registry.register("undo", _undo)


def _redo(ctx: ActionContext) -> None:
    _press("ctrl+y")


registry.register("redo", _redo)


def _select_all(ctx: ActionContext) -> None:
    _press("ctrl+a")


registry.register("select_all", _select_all)


def _delete(ctx: ActionContext) -> None:
    pyautogui.press("delete")


registry.register("delete", _delete)


def _enter(ctx: ActionContext) -> None:
    pyautogui.press("enter")


registry.register("enter", _enter)


def _move_up(ctx: ActionContext) -> None:
    pyautogui.press("up")


registry.register("move_up", _move_up)


def _move_down(ctx: ActionContext) -> None:
    pyautogui.press("down")


registry.register("move_down", _move_down)


def _duplicate_line(ctx: ActionContext) -> None:
    _press("ctrl+d")


registry.register("duplicate_line", _duplicate_line)


def _delete_line(ctx: ActionContext) -> None:
    _press("ctrl+shift+k")


registry.register("delete_line", _delete_line)


def _line_home(ctx: ActionContext) -> None:
    pyautogui.press("home")


registry.register("line_home", _line_home)


def _line_end(ctx: ActionContext) -> None:
    pyautogui.press("end")


registry.register("line_end", _line_end)


def _toggle_input_method(ctx: ActionContext) -> None:
    _press("win+space")


registry.register("toggle_input_method", _toggle_input_method)


def _toggle_language(ctx: ActionContext) -> None:
    _press("alt+shift")


registry.register("toggle_language", _toggle_language)


def _switch_ime(ctx: ActionContext) -> None:
    _press("ctrl+shift")


registry.register("switch_ime", _switch_ime)


# Application launchers ------------------------------------------------------

def _open_browser(ctx: ActionContext) -> None:
    browser = ctx.params.get("browser", "msedge")
    subprocess.Popen([browser])


registry.register("open_browser", _open_browser)


def _open_app(ctx: ActionContext) -> None:
    path = ctx.params.get("path")
    if not path:
        raise ValueError("'path' parameter required")
    subprocess.Popen(path)


registry.register("open_app", _open_app)


def _open_notepad(ctx: ActionContext) -> None:
    subprocess.Popen(["notepad.exe"])


registry.register("open_notepad", _open_notepad)


def _open_explorer(ctx: ActionContext) -> None:
    subprocess.Popen(["explorer.exe"])


registry.register("open_explorer", _open_explorer)


def _run_script(ctx: ActionContext) -> None:
    script = ctx.params.get("script")
    if not script:
        raise ValueError("'script' parameter required")
    subprocess.Popen(["powershell", "-File", script])


registry.register("run_script", _run_script)


def _click_position(ctx: ActionContext) -> None:
    x = ctx.params.get("x")
    y = ctx.params.get("y")
    if x is None or y is None:
        raise ValueError("'x' and 'y' parameters required")
    pyautogui.click(x, y)


registry.register("click_position", _click_position)


def _open_settings(ctx: ActionContext) -> None:
    subprocess.Popen(["ms-settings:"])


registry.register("open_settings", _open_settings)


# Utility --------------------------------------------------------------------

def _custom_key_sequence(ctx: ActionContext) -> None:
    sequence = ctx.params.get("sequence")
    if not sequence:
        raise ValueError("'sequence' parameter required")
    for combo in sequence:
        if isinstance(combo, str):
            _press(combo)
        elif isinstance(combo, dict):
            if combo.get("type") == "text":
                _type(combo.get("value", ""))


registry.register("custom_sequence", _custom_key_sequence)


def _save_file(ctx: ActionContext) -> None:
    _press("ctrl+s")


registry.register("save_file", _save_file)


def _new_file(ctx: ActionContext) -> None:
    _press("ctrl+n")


registry.register("new_file", _new_file)


def _open_file(ctx: ActionContext) -> None:
    _press("ctrl+o")


registry.register("open_file", _open_file)
