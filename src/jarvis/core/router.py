import json
from pathlib import Path


WEB_SHORTCUTS_FILE = Path(
    "data/web_shortcuts.json"
)


class Router:

    BROWSERS = [
        "microsoft edge",
        "google chrome",
        "edge",
        "chrome",
        "brave",
        "firefox",
        "comet"
    ]

    def load_web_shortcuts(
        self
    ) -> set[str]:
        try:
            if not WEB_SHORTCUTS_FILE.exists():
                return set()

            with open(
                WEB_SHORTCUTS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            if not isinstance(
                data,
                dict
            ):
                return set()

            return {
                str(key).lower().strip()
                for key in data.keys()
                if str(key).strip()
            }

        except Exception:
            return set()

    def looks_like_url(
        self,
        text: str
    ) -> bool:
        text = text.lower().strip()

        if text.startswith(
            (
                "http://",
                "https://",
                "www."
            )
        ):
            return True

        if "." in text and " " not in text:
            return True

        return False

    def split_browser(
        self,
        text: str
    ):
        text = text.strip()

        connectors = [
            " in ",
            " from ",
            " on ",
            " using ",
            " with "
        ]

        for connector in connectors:
            for browser in self.BROWSERS:
                suffix = f"{connector}{browser}"

                if text.endswith(
                    suffix
                ):
                    clean_text = text[
                        :-len(suffix)
                    ].strip()

                    return clean_text, browser

        return text, None

    def route(
        self,
        user_input: str
    ):

        text = (
            user_input
            .lower()
            .strip()
        )

        web_shortcuts = self.load_web_shortcuts()

        refresh_commands = [
            "refresh apps",
            "rescan apps",
            "scan pc",
            "refresh pc"
        ]

        for cmd in refresh_commands:
            if text == cmd:
                return {
                    "tool": "refresh_apps"
                }

        if text in [
            "list apps",
            "show apps",
            "show applications",
            "list applications"
        ]:
            return {
                "tool": "list_apps"
            }

        search_app_prefixes = [
            "find app ",
            "search app ",
            "search apps ",
            "find apps "
        ]

        for prefix in search_app_prefixes:
            if text.startswith(
                prefix
            ):
                query = text.replace(
                    prefix,
                    "",
                    1
                ).strip()

                return {
                    "tool": "list_apps",
                    "query": query
                }

        if text in [
            "volume up",
            "increase volume",
            "turn volume up",
            "raise volume"
        ]:
            return {
                "tool": "system_control",
                "action": "volume_up"
            }

        if text in [
            "volume down",
            "decrease volume",
            "turn volume down",
            "lower volume"
        ]:
            return {
                "tool": "system_control",
                "action": "volume_down"
            }

        if text in [
            "mute",
            "mute volume",
            "unmute",
            "unmute volume"
        ]:
            return {
                "tool": "system_control",
                "action": "mute"
            }

        if text in [
            "lock pc",
            "lock computer",
            "lock my pc",
            "lock screen"
        ]:
            return {
                "tool": "system_control",
                "action": "lock"
            }

        if text in [
            "sleep pc",
            "sleep computer",
            "put pc to sleep",
            "put computer to sleep"
        ]:
            return {
                "tool": "system_control",
                "action": "sleep"
            }

        if text in [
            "shutdown pc",
            "shut down pc",
            "shutdown computer",
            "shut down computer"
        ]:
            return {
                "tool": "system_control",
                "action": "shutdown"
            }

        if text in [
            "restart pc",
            "restart computer",
            "reboot pc",
            "reboot computer"
        ]:
            return {
                "tool": "system_control",
                "action": "restart"
            }

        settings_commands = {
            "open settings": "home",
            "open windows settings": "home",
            "open display settings": "display",
            "open sound settings": "sound",
            "open audio settings": "sound",
            "open bluetooth settings": "bluetooth",
            "open network settings": "network",
            "open wifi settings": "wifi",
            "open wi-fi settings": "wi-fi",
            "open ethernet settings": "ethernet",
            "open power settings": "power",
            "open battery settings": "battery",
            "open storage settings": "storage",
            "open apps settings": "apps",
            "open uninstall settings": "uninstall",
            "open update settings": "windows update",
            "open windows update": "windows update",
            "open privacy settings": "privacy",
            "open mouse settings": "mouse",
            "open keyboard settings": "keyboard",
            "open time settings": "time",
            "open date settings": "date"
        }

        if text in settings_commands:
            return {
                "tool": "system_control",
                "action": "settings",
                "value": settings_commands[text]
            }

        browser_commands = {
            "new tab": "new_tab",
            "open new tab": "new_tab",
            "close tab": "close_tab",
            "close current tab": "close_tab",
            "reopen closed tab": "reopen_closed_tab",
            "reopen last closed tab": "reopen_closed_tab",
            "open new browser window": "new_window",
            "new browser window": "new_window",
            "open incognito": "incognito",
            "open incognito window": "incognito",
            "open private window": "incognito",
            "close browser window": "close_window",
            "next tab": "next_tab",
            "previous tab": "previous_tab",
            "prev tab": "previous_tab",
            "refresh page": "refresh",
            "reload page": "refresh",
            "hard refresh": "hard_refresh",
            "hard refresh page": "hard_refresh",
            "stop loading": "stop_loading",
            "stop page loading": "stop_loading",
            "browser back": "back",
            "go back": "back",
            "browser forward": "forward",
            "go forward": "forward",
            "go to homepage": "homepage",
            "homepage": "homepage",
            "focus address bar": "focus_address",
            "address bar": "focus_address",
            "open downloads": "downloads",
            "open browser downloads": "downloads",
            "open history": "history",
            "open browser history": "history",
            "open bookmarks": "bookmarks",
            "open bookmarks page": "bookmarks",
            "open bookmark manager": "bookmarks",
            "add bookmark": "add_bookmark",
            "bookmark page": "add_bookmark",
            "bookmark all tabs": "bookmark_all_tabs",
            "find on page": "find",
            "print page": "print",
            "save page": "save_page",
            "view source": "view_source",
            "view page source": "view_source",
            "open developer tools": "dev_tools",
            "developer tools": "dev_tools",
            "copy current url": "copy_url",
            "copy page url": "copy_url",
            "copy url": "copy_url",
            "open url from clipboard": "paste_and_go",
            "paste and go": "paste_and_go",
            "duplicate tab": "duplicate_tab",
            "move tab left": "move_tab_left",
            "move tab right": "move_tab_right",
            "zoom in": "zoom_in",
            "zoom out": "zoom_out",
            "reset zoom": "reset_zoom",
            "fullscreen browser": "fullscreen",
            "browser fullscreen": "fullscreen",
            "scroll down": "scroll_down",
            "scroll up": "scroll_up",
            "scroll to top": "scroll_top",
            "scroll to bottom": "scroll_bottom",
            "play video": "play_pause",
            "pause video": "play_pause",
            "toggle play pause": "play_pause",
            "play pause": "play_pause",
            "mute video": "mute_video",
            "unmute video": "mute_video",
            "seek forward": "seek_forward",
            "seek backward": "seek_backward",
            "next video": "next_video",
            "previous video": "previous_video",
            "fullscreen video": "fullscreen_video",
            "toggle captions": "captions",
            "enable captions": "captions",
            "disable captions": "captions",
            "speed up video": "speed_up",
            "slow down video": "speed_down"
        }

        browser_text, browser = self.split_browser(
            text
        )

        if browser_text in browser_commands:
            return {
                "tool": "browser_control",
                "action": browser_commands[browser_text],
                "browser": browser
            }

        if browser_text.startswith(
            "find on page "
        ):
            value = browser_text.replace(
                "find on page ",
                "",
                1
            ).strip()

            return {
                "tool": "browser_control",
                "action": "find_text",
                "value": value,
                "browser": browser
            }

        if browser_text.startswith(
            "switch to tab "
        ):
            value = browser_text.replace(
                "switch to tab ",
                "",
                1
            ).strip()

            return {
                "tool": "browser_control",
                "action": "switch_tab_number",
                "value": value,
                "browser": browser
            }

        clipboard_exact_commands = {
            "show clipboard": "show_clipboard",
            "read clipboard": "show_clipboard",
            "clear clipboard": "clear_clipboard",
            "empty clipboard": "clear_clipboard",
            "open clipboard history": "open_clipboard_history",
            "clipboard history": "open_clipboard_history",
            "copy current date": "copy_date",
            "copy date": "copy_date",
            "copy current time": "copy_time",
            "copy time": "copy_time",
            "copy current date and time": "copy_datetime",
            "copy date and time": "copy_datetime",
            "paste": "paste",
            "paste clipboard": "paste",
            "copy selected text": "copy_selected",
            "copy selection": "copy_selected",
            "cut selected text": "cut_selected",
            "cut selection": "cut_selected",
            "select all": "select_all",
            "select all text": "select_all",
            "press enter": "press_enter",
            "hit enter": "press_enter",
            "press tab": "press_tab",
            "press escape": "press_escape",
            "press esc": "press_escape"
        }

        if text in clipboard_exact_commands:
            return {
                "tool": "clipboard_control",
                "action": clipboard_exact_commands[text]
            }

        clipboard_copy_prefixes = [
            "copy text ",
            "copy to clipboard ",
            "put text in clipboard ",
            "set clipboard "
        ]

        for prefix in clipboard_copy_prefixes:
            if text.startswith(
                prefix
            ):
                value = user_input[
                    len(prefix):
                ].strip()

                return {
                    "tool": "clipboard_control",
                    "action": "copy_text",
                    "value": value
                }

        type_text_prefixes = [
            "type text ",
            "type "
        ]

        for prefix in type_text_prefixes:
            if text.startswith(
                prefix
            ):
                value = user_input[
                    len(prefix):
                ].strip()

                return {
                    "tool": "clipboard_control",
                    "action": "type_text",
                    "value": value
                }

        window_commands = {
            "minimize active window": "minimize",
            "minimize window": "minimize",
            "maximize active window": "maximize",
            "maximize window": "maximize",
            "restore active window": "restore",
            "restore window": "restore",
            "close active window": "close",
            "close window": "close",
            "snap left": "snap_left",
            "snap window left": "snap_left",
            "snap right": "snap_right",
            "snap window right": "snap_right",
            "snap up": "snap_up",
            "snap window up": "snap_up",
            "snap down": "snap_down",
            "snap window down": "snap_down",
            "move window to next monitor": "next_monitor",
            "move window to other monitor": "next_monitor",
            "move window to previous monitor": "previous_monitor",
            "show desktop": "show_desktop",
            "open task view": "task_view",
            "task view": "task_view",
            "switch window": "switch_window",
            "switch windows": "switch_window",
            "minimize all windows": "minimize_all",
            "restore minimized windows": "restore_minimized"
        }

        if text in window_commands:
            return {
                "tool": "window_control",
                "action": window_commands[text]
            }

        screenshot_commands = {
            "take screenshot": "full_screenshot",
            "take full screenshot": "full_screenshot",
            "screenshot": "full_screenshot",
            "capture screen": "full_screenshot",
            "capture full screen": "full_screenshot",
            "take active window screenshot": "active_window_screenshot",
            "screenshot active window": "active_window_screenshot",
            "capture active window": "active_window_screenshot",
            "copy screenshot": "copy_full_screenshot",
            "copy screenshot to clipboard": "copy_full_screenshot",
            "copy screen": "copy_full_screenshot",
            "copy active window screenshot": "copy_active_window_screenshot",
            "copy active window": "copy_active_window_screenshot",
            "open screenshot folder": "open_screenshot_folder",
            "open screenshots folder": "open_screenshot_folder",
            "open snipping tool": "open_snipping_tool",
            "snipping tool": "open_snipping_tool",
            "open screen snip": "open_screen_snip",
            "screen snip": "open_screen_snip",
            "take selected screenshot": "open_screen_snip",
            "take selected area screenshot": "open_screen_snip"
        }

        if text in screenshot_commands:
            return {
                "tool": "screenshot_control",
                "action": screenshot_commands[text]
            }
        




        ppt_folder_commands = [
            "open ppt folder",
            "open ppts folder",
            "open presentation folder",
            "open presentations folder",
            "open ppt output folder"
        ]

        if text in ppt_folder_commands:
            return {
                "tool": "ppt_maker",
                "action": "open_ppt_folder"
            }

        ppt_prefixes = [
            (
                "create professional ppt about ",
                "professional"
            ),
            (
                "make professional ppt about ",
                "professional"
            ),
            (
                "create professional presentation about ",
                "professional"
            ),
            (
                "make professional presentation about ",
                "professional"
            ),
            (
                "create school ppt about ",
                "school"
            ),
            (
                "make school ppt about ",
                "school"
            ),
            (
                "create school presentation about ",
                "school"
            ),
            (
                "make school presentation about ",
                "school"
            ),
            (
                "create simple ppt about ",
                "simple"
            ),
            (
                "make simple ppt about ",
                "simple"
            ),
            (
                "create simple presentation about ",
                "simple"
            ),
            (
                "make simple presentation about ",
                "simple"
            ),
            (
                "create ppt about ",
                "professional"
            ),
            (
                "make ppt about ",
                "professional"
            ),
            (
                "generate ppt about ",
                "professional"
            ),
            (
                "create presentation about ",
                "professional"
            ),
            (
                "make presentation about ",
                "professional"
            ),
            (
                "generate presentation about ",
                "professional"
            )
        ]

        for prefix, style in ppt_prefixes:
            if text.startswith(
                prefix
            ):
                topic = user_input[
                    len(prefix):
                ].strip()

                return {
                    "tool": "ppt_maker",
                    "action": "create_ppt",
                    "topic": topic,
                    "style": style
                }

        document_folder_commands = [
            "open document folder",
            "open documents folder",
            "open doc folder",
            "open docs folder",
            "open document output folder"
        ]

        if text in document_folder_commands:
            return {
                "tool": "document_maker",
                "action": "open_document_folder"
            }

        document_prefixes = [
            (
                "create professional document about ",
                "professional"
            ),
            (
                "make professional document about ",
                "professional"
            ),
            (
                "create professional report about ",
                "professional"
            ),
            (
                "make professional report about ",
                "professional"
            ),
            (
                "create report about ",
                "professional"
            ),
            (
                "make report about ",
                "professional"
            ),
            (
                "create document about ",
                "professional"
            ),
            (
                "make document about ",
                "professional"
            ),
            (
                "create doc about ",
                "professional"
            ),
            (
                "make doc about ",
                "professional"
            ),
            (
                "create school report about ",
                "school"
            ),
            (
                "make school report about ",
                "school"
            ),
            (
                "create assignment about ",
                "school"
            ),
            (
                "make assignment about ",
                "school"
            ),
            (
                "create essay about ",
                "essay"
            ),
            (
                "make essay about ",
                "essay"
            ),
            (
                "write essay about ",
                "essay"
            ),
            (
                "create notes about ",
                "notes"
            ),
            (
                "make notes about ",
                "notes"
            ),
            (
                "write notes about ",
                "notes"
            )
        ]

        for prefix, doc_type in document_prefixes:
            if text.startswith(
                prefix
            ):
                topic = user_input[
                    len(prefix):
                ].strip()

                return {
                    "tool": "document_maker",
                    "action": "create_document",
                    "topic": topic,
                    "doc_type": doc_type
                }
            

        pdf_exact_commands = {
            "open pdf folder": "open_pdf_folder",
            "open pdf tools folder": "open_pdf_folder",
            "open pdf input folder": "open_pdf_input_folder",
            "open pdf output folder": "open_pdf_output_folder",
            "list pdfs": "list_input_pdfs",
            "list input pdfs": "list_input_pdfs",
            "show pdfs": "list_input_pdfs",
            "show input pdfs": "list_input_pdfs",
            "merge pdfs": "merge_pdfs",
            "merge input pdfs": "merge_pdfs",
            "merge pdfs in input folder": "merge_pdfs",
            "images to pdf": "images_to_pdf",
            "convert images to pdf": "images_to_pdf"
        }

        if text in pdf_exact_commands:
            return {
                "tool": "pdf_tools",
                "action": pdf_exact_commands[text]
            }

        pdf_path_prefixes = [
            (
                "pdf info ",
                "pdf_info"
            ),
            (
                "get pdf info ",
                "pdf_info"
            ),
            (
                "extract text from pdf ",
                "extract_text"
            ),
            (
                "extract pdf text ",
                "extract_text"
            ),
            (
                "split pdf ",
                "split_pdf"
            ),
            (
                "split pdf pages ",
                "split_pdf"
            )
        ]

        for prefix, action in pdf_path_prefixes:
            if text.startswith(
                prefix
            ):
                path = user_input[
                    len(prefix):
                ].strip()

                return {
                    "tool": "pdf_tools",
                    "action": action,
                    "path": path
                }

        pdf_folder_prefixes = [
            (
                "merge pdfs in folder ",
                "merge_pdfs"
            ),
            (
                "merge pdfs from folder ",
                "merge_pdfs"
            ),
            (
                "images to pdf from folder ",
                "images_to_pdf"
            ),
            (
                "convert images to pdf from folder ",
                "images_to_pdf"
            )
        ]

        for prefix, action in pdf_folder_prefixes:
            if text.startswith(
                prefix
            ):
                folder = user_input[
                    len(prefix):
                ].strip()

                return {
                    "tool": "pdf_tools",
                    "action": action,
                    "folder": folder
                }





        search_prefixes = {
            "search google ": "google",
            "google ": "google",
            "search youtube ": "youtube",
            "youtube search ": "youtube",
            "search bing ": "bing",
            "bing ": "bing",
            "search duckduckgo ": "duckduckgo",
            "duckduckgo ": "duckduckgo",
            "search ": "google"
        }

        for prefix, engine in search_prefixes.items():
            if text.startswith(
                prefix
            ):
                query = text.replace(
                    prefix,
                    "",
                    1
                ).strip()

                query, browser = self.split_browser(
                    query
                )

                return {
                    "tool": "web_control",
                    "action": "search",
                    "engine": engine,
                    "target": query,
                    "browser": browser
                }

        url_prefixes = [
            "open url ",
            "open website ",
            "open site ",
            "go to ",
            "visit "
        ]

        for prefix in url_prefixes:
            if text.startswith(
                prefix
            ):
                target = text.replace(
                    prefix,
                    "",
                    1
                ).strip()

                target, browser = self.split_browser(
                    target
                )

                return {
                    "tool": "web_control",
                    "action": "open_url",
                    "target": target,
                    "browser": browser
                }

        if text.startswith(
            "open "
        ):
            target = text.replace(
                "open ",
                "",
                1
            ).strip()

            target, browser = self.split_browser(
                target
            )

            if target in web_shortcuts:
                return {
                    "tool": "web_control",
                    "action": "open_shortcut",
                    "target": target,
                    "browser": browser
                }

            if self.looks_like_url(
                target
            ):
                return {
                    "tool": "web_control",
                    "action": "open_url",
                    "target": target,
                    "browser": browser
                }

        clean_text, browser = self.split_browser(
            text
        )

        if clean_text in web_shortcuts:
            return {
                "tool": "web_control",
                "action": "open_shortcut",
                "target": clean_text,
                "browser": browser
            }

        if text in [
            "refresh folders",
            "rescan folders",
            "scan folders",
            "refresh folder index"
        ]:
            return {
                "tool": "file_control",
                "action": "refresh_folders"
            }

        folder_search_prefixes = [
            "find folder ",
            "find folders ",
            "search folder ",
            "search folders "
        ]

        for prefix in folder_search_prefixes:
            if text.startswith(
                prefix
            ):
                target = text.replace(
                    prefix,
                    "",
                    1
                ).strip()

                return {
                    "tool": "file_control",
                    "action": "find_folder",
                    "target": target
                }

        folder_open_prefixes = [
            "open folder ",
            "open directory ",
            "open dir "
        ]

        for prefix in folder_open_prefixes:
            if text.startswith(
                prefix
            ):
                target = text.replace(
                    prefix,
                    "",
                    1
                ).strip()

                return {
                    "tool": "file_control",
                    "action": "open_folder",
                    "target": target
                }

        if text.startswith(
            "open path "
        ):
            target = text.replace(
                "open path ",
                "",
                1
            ).strip()

            return {
                "tool": "file_control",
                "action": "open_path",
                "target": target
            }

        if (
            text.startswith("open ")
            and text.endswith(" folder")
        ):
            target = text.replace(
                "open ",
                "",
                1
            )

            target = target[
                :-len(" folder")
            ].strip()

            return {
                "tool": "file_control",
                "action": "open_folder",
                "target": target
            }

        open_commands = [
            "open ",
            "launch ",
            "start "
        ]

        close_commands = [
            "close ",
            "quit ",
            "kill ",
            "stop "
        ]

        for cmd in open_commands:
            if text.startswith(
                cmd
            ):
                app = text.replace(
                    cmd,
                    "",
                    1
                ).strip()

                return {
                    "tool": "open_app",
                    "app_name": app
                }

        for cmd in close_commands:
            if text.startswith(
                cmd
            ):
                app = text.replace(
                    cmd,
                    "",
                    1
                ).strip()

                return {
                    "tool": "close_app",
                    "app_name": app
                }

        return None