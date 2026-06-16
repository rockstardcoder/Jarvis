import time
from typing import Callable

import psutil
import win32api
import win32clipboard
import win32con
import win32gui
import win32process

VK_PLUS = 0xBB
VK_MINUS = 0xBD
VK_COMMA = 0xBC
VK_PERIOD = 0xBE


class BrowserControl:

    BROWSER_PROCESSES = {
        "edge": ["msedge.exe"],
        "microsoft edge": ["msedge.exe"],
        "chrome": ["chrome.exe"],
        "google chrome": ["chrome.exe"],
        "brave": ["brave.exe"],
        "firefox": ["firefox.exe"],
        "comet": ["comet.exe"],
    }

    ALL_BROWSER_PROCESSES = [
        "msedge.exe",
        "chrome.exe",
        "brave.exe",
        "firefox.exe",
        "comet.exe",
    ]

    def key_down(self, key_code: int):
        win32api.keybd_event(
            key_code,
            0,
            0,
            0
        )

    def key_up(self, key_code: int):
        win32api.keybd_event(
            key_code,
            0,
            win32con.KEYEVENTF_KEYUP,
            0
        )

    def press_key(
        self,
        key_code: int,
        delay: float = 0.05
    ):
        self.key_down(key_code)
        time.sleep(delay)
        self.key_up(key_code)
        time.sleep(delay)

    def hotkey(
        self,
        *keys: int
    ):
        for key in keys:
            self.key_down(key)
            time.sleep(0.02)

        time.sleep(0.05)

        for key in reversed(keys):
            self.key_up(key)
            time.sleep(0.02)

        time.sleep(0.08)

    def set_clipboard_text(
        self,
        text: str
    ):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()

        except Exception:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def get_browser_process_names(
        self,
        browser: str | None = None
    ) -> list[str]:
        if browser:
            browser = browser.lower().strip()

            if browser in self.BROWSER_PROCESSES:
                return self.BROWSER_PROCESSES[browser]

        return self.ALL_BROWSER_PROCESSES

    def find_browser_windows(
        self,
        browser: str | None = None
    ) -> list[int]:
        browser_processes = self.get_browser_process_names(
            browser
        )

        windows = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd).strip()

            if not title:
                return

            try:
                _, pid = win32process.GetWindowThreadProcessId(
                    hwnd
                )

                process = psutil.Process(pid)
                process_name = process.name().lower()

                if process_name in browser_processes:
                    windows.append(hwnd)

            except Exception:
                return

        win32gui.EnumWindows(callback, None)

        return windows

    def focus_browser(
        self,
        browser: str | None = None
    ) -> bool:
        windows = self.find_browser_windows(browser)

        if not windows:
            return False

        hwnd = windows[0]

        try:
            win32gui.ShowWindow(
                hwnd,
                win32con.SW_RESTORE
            )

            time.sleep(0.1)

            win32gui.SetForegroundWindow(hwnd)

            time.sleep(0.2)

            return True

        except Exception:
            return False

    def restore_window(
        self,
        hwnd
    ):
        try:
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)

        except Exception:
            pass

    def run_action(
        self,
        action: Callable,
        browser: str | None = None,
        restore_focus: bool = True
    ) -> bool:
        previous_window = win32gui.GetForegroundWindow()

        focused = self.focus_browser(browser)

        if not focused:
            return False

        try:
            action()
            time.sleep(0.2)
            return True

        finally:
            if restore_focus:
                self.restore_window(previous_window)

    def new_tab(self):
        self.hotkey(win32con.VK_CONTROL, ord("T"))

    def close_tab(self):
        self.hotkey(win32con.VK_CONTROL, ord("W"))

    def reopen_closed_tab(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            ord("T")
        )

    def new_window(self):
        self.hotkey(win32con.VK_CONTROL, ord("N"))

    def incognito(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            ord("N")
        )

    def close_window(self):
        self.hotkey(win32con.VK_MENU, win32con.VK_F4)

    def next_tab(self):
        self.hotkey(win32con.VK_CONTROL, win32con.VK_TAB)

    def previous_tab(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            win32con.VK_TAB
        )

    def refresh(self):
        self.hotkey(win32con.VK_CONTROL, ord("R"))

    def hard_refresh(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            ord("R")
        )

    def stop_loading(self):
        self.press_key(win32con.VK_ESCAPE)

    def back(self):
        self.hotkey(win32con.VK_MENU, win32con.VK_LEFT)

    def forward(self):
        self.hotkey(win32con.VK_MENU, win32con.VK_RIGHT)

    def homepage(self):
        self.hotkey(win32con.VK_MENU, win32con.VK_HOME)

    def focus_address(self):
        self.hotkey(win32con.VK_CONTROL, ord("L"))

    def downloads(self):
        self.hotkey(win32con.VK_CONTROL, ord("J"))

    def history(self):
        self.hotkey(win32con.VK_CONTROL, ord("H"))

    def bookmarks(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            ord("O")
        )

    def add_bookmark(self):
        self.hotkey(win32con.VK_CONTROL, ord("D"))

    def bookmark_all_tabs(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            ord("D")
        )

    def find(self):
        self.hotkey(win32con.VK_CONTROL, ord("F"))

    def find_text(
        self,
        text: str
    ):
        self.find()
        time.sleep(0.1)
        self.set_clipboard_text(text)
        self.hotkey(win32con.VK_CONTROL, ord("V"))

    def print_page(self):
        self.hotkey(win32con.VK_CONTROL, ord("P"))

    def save_page(self):
        self.hotkey(win32con.VK_CONTROL, ord("S"))

    def view_source(self):
        self.hotkey(win32con.VK_CONTROL, ord("U"))

    def dev_tools(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            ord("I")
        )

    def copy_url(self):
        self.hotkey(win32con.VK_CONTROL, ord("L"))
        time.sleep(0.1)
        self.hotkey(win32con.VK_CONTROL, ord("C"))

    def paste_and_go(self):
        self.hotkey(win32con.VK_CONTROL, ord("L"))
        time.sleep(0.1)
        self.hotkey(win32con.VK_CONTROL, ord("V"))
        time.sleep(0.1)
        self.press_key(win32con.VK_RETURN)

    def duplicate_tab(self):
        self.copy_url()
        time.sleep(0.1)
        self.new_tab()
        time.sleep(0.1)
        self.hotkey(win32con.VK_CONTROL, ord("V"))
        time.sleep(0.1)
        self.press_key(win32con.VK_RETURN)

    def move_tab_left(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            win32con.VK_PRIOR
        )

    def move_tab_right(self):
        self.hotkey(
            win32con.VK_CONTROL,
            win32con.VK_SHIFT,
            win32con.VK_NEXT
        )
    def zoom_in(self):
        self.hotkey(win32con.VK_CONTROL, VK_PLUS)

    def zoom_out(self):
        self.hotkey(win32con.VK_CONTROL, VK_MINUS)

    def reset_zoom(self):
        self.hotkey(win32con.VK_CONTROL, ord("0"))

    def fullscreen(self):
        self.press_key(win32con.VK_F11)

    def scroll_down(self):
        self.press_key(win32con.VK_NEXT)

    def scroll_up(self):
        self.press_key(win32con.VK_PRIOR)

    def scroll_top(self):
        self.press_key(win32con.VK_HOME)

    def scroll_bottom(self):
        self.press_key(win32con.VK_END)

    def play_pause(self):
        self.press_key(win32con.VK_SPACE)

    def mute_video(self):
        self.press_key(ord("M"))

    def seek_forward(self):
        self.press_key(win32con.VK_RIGHT)

    def seek_backward(self):
        self.press_key(win32con.VK_LEFT)

    def next_video(self):
        self.hotkey(win32con.VK_SHIFT, ord("N"))

    def previous_video(self):
        self.hotkey(win32con.VK_SHIFT, ord("P"))

    def fullscreen_video(self):
        self.press_key(ord("F"))

    def captions(self):
        self.press_key(ord("C"))

    def speed_up(self):
        self.hotkey(
            win32con.VK_SHIFT,
            VK_PERIOD
        )
    def speed_down(self):
        self.hotkey(
            win32con.VK_SHIFT,
            VK_COMMA
        )

    def switch_tab_number(
        self,
        number: int
    ):
        number = max(
            1,
            min(
                9,
                number
            )
        )

        self.hotkey(
            win32con.VK_CONTROL,
            ord(str(number))
        )

    def execute(
        self,
        action: str,
        value: str | None = None,
        browser: str | None = None
    ) -> str:
        action = action.lower().strip()

        if action == "find_text":
            if not value:
                return "No find text was provided."

            success = self.run_action(
                lambda: self.find_text(value),
                browser=browser,
                restore_focus=False
            )

            if success:
                return f"Finding {value} on page."

            return "No browser window was found."

        if action == "switch_tab_number":
            try:
                number = int(value or "1")
            except ValueError:
                number = 1

            success = self.run_action(
                lambda: self.switch_tab_number(number),
                browser=browser
            )

            if success:
                return f"Switching to tab {number}."

            return "No browser window was found."

        actions = {
            "new_tab": (self.new_tab, "Opening new tab."),
            "close_tab": (self.close_tab, "Closing current tab."),
            "reopen_closed_tab": (self.reopen_closed_tab, "Reopening last closed tab."),
            "new_window": (self.new_window, "Opening new browser window."),
            "incognito": (self.incognito, "Opening private browser window."),
            "close_window": (self.close_window, "Closing browser window."),
            "next_tab": (self.next_tab, "Switching to next tab."),
            "previous_tab": (self.previous_tab, "Switching to previous tab."),
            "refresh": (self.refresh, "Refreshing page."),
            "hard_refresh": (self.hard_refresh, "Hard refreshing page."),
            "stop_loading": (self.stop_loading, "Stopping page loading."),
            "back": (self.back, "Going back."),
            "forward": (self.forward, "Going forward."),
            "homepage": (self.homepage, "Going to homepage."),
            "focus_address": (self.focus_address, "Focusing address bar."),
            "downloads": (self.downloads, "Opening downloads."),
            "history": (self.history, "Opening history."),
            "bookmarks": (self.bookmarks, "Opening bookmark manager."),
            "add_bookmark": (self.add_bookmark, "Adding bookmark."),
            "bookmark_all_tabs": (self.bookmark_all_tabs, "Bookmarking all tabs."),
            "find": (self.find, "Opening find on page."),
            "print": (self.print_page, "Opening print dialog."),
            "save_page": (self.save_page, "Saving page."),
            "view_source": (self.view_source, "Opening page source."),
            "dev_tools": (self.dev_tools, "Opening developer tools."),
            "copy_url": (self.copy_url, "Copied current page URL."),
            "paste_and_go": (self.paste_and_go, "Opening URL from clipboard."),
            "duplicate_tab": (self.duplicate_tab, "Duplicating current tab."),
            "move_tab_left": (self.move_tab_left, "Moving tab left."),
            "move_tab_right": (self.move_tab_right, "Moving tab right."),
            "zoom_in": (self.zoom_in, "Zooming in."),
            "zoom_out": (self.zoom_out, "Zooming out."),
            "reset_zoom": (self.reset_zoom, "Resetting zoom."),
            "fullscreen": (self.fullscreen, "Toggling browser fullscreen."),
            "scroll_down": (self.scroll_down, "Scrolling down."),
            "scroll_up": (self.scroll_up, "Scrolling up."),
            "scroll_top": (self.scroll_top, "Scrolling to top."),
            "scroll_bottom": (self.scroll_bottom, "Scrolling to bottom."),
            "play_pause": (self.play_pause, "Toggling play pause."),
            "mute_video": (self.mute_video, "Toggling video mute."),
            "seek_forward": (self.seek_forward, "Seeking forward."),
            "seek_backward": (self.seek_backward, "Seeking backward."),
            "next_video": (self.next_video, "Going to next video."),
            "previous_video": (self.previous_video, "Going to previous video."),
            "fullscreen_video": (self.fullscreen_video, "Toggling video fullscreen."),
            "captions": (self.captions, "Toggling captions."),
            "speed_up": (self.speed_up, "Increasing playback speed."),
            "speed_down": (self.speed_down, "Decreasing playback speed."),
        }

        if action not in actions:
            return f"Unknown browser action: {action}"

        function, message = actions[action]

        no_restore_actions = {
            "focus_address",
            "find",
            "downloads",
            "history",
            "bookmarks",
            "add_bookmark",
            "bookmark_all_tabs",
            "print",
            "save_page",
            "view_source",
            "dev_tools",
            "fullscreen",
            "fullscreen_video"
        }

        success = self.run_action(
            function,
            browser=browser,
            restore_focus=action not in no_restore_actions
        )

        if success:
            return message

        return "No browser window was found."