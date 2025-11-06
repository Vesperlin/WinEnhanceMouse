"""Implementation of the middle-click pop-up menu overlay."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Callable, List, Sequence

import tkinter as tk

from ..config import ActionBinding, MenuAppearance

logger = logging.getLogger(__name__)


@dataclass
class MenuItem:
    binding: ActionBinding
    queue_level: int  # 1 for primary, 2 for secondary


class MenuOverlay:
    """Controls the lifecycle of the translucent floating menu."""

    def __init__(
        self,
        appearance: MenuAppearance,
        on_select: Callable[[MenuItem], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.appearance = appearance
        self.on_select = on_select
        self.on_cancel = on_cancel
        self._root: tk.Tk | None = None
        self._items: List[MenuItem] = []
        self._focus_index = 0
        self._visible = False
        self._thread: threading.Thread | None = None

    def open(self, items: Sequence[MenuItem]) -> None:
        logger.debug("Opening menu overlay with %d items", len(items))
        self._items = list(items)
        self._focus_index = 0
        if not self._root:
            self._spawn_window()
        self._invoke(lambda: self._render_items())
        self._invoke(lambda: self._root.deiconify())
        self._invoke(lambda: self._root.lift())
        self._visible = True

    def close(self) -> None:
        if self._root:
            self._invoke(lambda: self._root.withdraw())
        self._visible = False
        logger.debug("Menu overlay closed")

    def visible(self) -> bool:
        return self._visible

    @property
    def focus_index(self) -> int:
        return self._focus_index

    def focus_next(self) -> None:
        if not self._items:
            return
        self._focus_index = (self._focus_index + 1) % len(self._items)
        self._invoke(lambda: self._render_items())

    def focus_prev(self) -> None:
        if not self._items:
            return
        self._focus_index = (self._focus_index - 1) % len(self._items)
        self._invoke(lambda: self._render_items())

    def select_current(self) -> None:
        if not self._items:
            return
        item = self._items[self._focus_index]
        logger.debug("Selected item %s", item)
        self.on_select(item)

    def cancel(self) -> None:
        self.on_cancel()

    # Internal helpers -----------------------------------------------------
    def _spawn_window(self) -> None:
        self._thread = threading.Thread(target=self._init_window, daemon=True)
        self._thread.start()
        while self._root is None:
            pass

    def _init_window(self) -> None:
        self._root = tk.Tk()
        self._root.title("WinEnhanceMouse")
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.95)
        self._root.configure(bg="#1f2933")
        self._root.overrideredirect(True)
        self._list_frame = tk.Frame(self._root, bg="#1f2933")
        self._list_frame.pack(fill=tk.BOTH, expand=True)
        self._root.withdraw()
        self._root.mainloop()

    def _render_items(self) -> None:
        if not self._root:
            return
        for widget in self._list_frame.winfo_children():
            widget.destroy()
        width = self.appearance.width
        row_height = self.appearance.row_height
        for index, item in enumerate(self._items):
            focused = index == self._focus_index
            bg = "#334155" if focused else "#1f2933"
            fg = "#f8fafc" if item.queue_level == 1 else "#38bdf8"
            frame = tk.Frame(self._list_frame, width=width, height=row_height, bg=bg)
            frame.pack(fill=tk.BOTH, expand=True)
            label = tk.Label(
                frame,
                text=f"{item.binding.label} ({'一层' if item.queue_level == 1 else '二层'})",
                anchor="w",
                padx=12,
                pady=6,
                bg=bg,
                fg=fg,
                font=("Microsoft YaHei", self.appearance.font_size),
            )
            label.pack(fill=tk.BOTH, expand=True)
        self._list_frame.update_idletasks()
        self._position_window()

    def _position_window(self) -> None:
        if not self._root:
            return
        self._root.update_idletasks()
        width = self._root.winfo_width()
        height = self._root.winfo_height()
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        if self.appearance.position == "bottom_right":
            x = screen_width - width - 40
            y = screen_height - height - 80
        elif self.appearance.position == "bottom_left":
            x = 40
            y = screen_height - height - 80
        elif self.appearance.position == "top_right":
            x = screen_width - width - 40
            y = 80
        else:
            x = 40
            y = 80
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def _invoke(self, callback: Callable[[], None]) -> None:
        if not self._root:
            return
        self._root.after(0, callback)


__all__ = ["MenuOverlay", "MenuItem"]
