import re
import time

from jarvis.ai.llm_router import LLMRouter
from jarvis.ai.memory_store import MemoryStore
from jarvis.core.router import Router
from jarvis.llm.manager import LLMManager
from jarvis.services.training_logger import TrainingLogger
from jarvis.services.diagnostics_manager import DiagnosticsManager
from jarvis.services.voice.stt_service import STTService
from jarvis.services.voice.tts_service import TTSService
from jarvis.tools.browser_intelligence import BrowserIntelligenceTool
from jarvis.tools.system_info import SystemInfoTool
from jarvis.tools.tool_manager import ToolManager
from jarvis.tools.web_reader import WebReaderTool
from jarvis.tools.window_intelligence import WindowIntelligenceTool



POWER_ACTIONS = {
    "sleep": {
        "label": "sleep PC",
        "confirm": "confirm sleep"
    },
    "shutdown": {
        "label": "shutdown PC",
        "confirm": "confirm shutdown"
    },
    "restart": {
        "label": "restart PC",
        "confirm": "confirm restart"
    }
}


POWER_CONFIRM_TIMEOUT = 30
AI_ROUTER_INSTANCE = None
MEMORY_INSTANCE = None
LOGGER_INSTANCE = None
DIAGNOSTICS_INSTANCE = None

def get_ai_router():
    global AI_ROUTER_INSTANCE

    if AI_ROUTER_INSTANCE is None:
        AI_ROUTER_INSTANCE = LLMRouter()

    return AI_ROUTER_INSTANCE


def get_memory():
    global MEMORY_INSTANCE

    if MEMORY_INSTANCE is None:
        MEMORY_INSTANCE = MemoryStore()

    return MEMORY_INSTANCE

def get_logger():
    global LOGGER_INSTANCE

    if LOGGER_INSTANCE is None:
        LOGGER_INSTANCE = TrainingLogger()

    return LOGGER_INSTANCE

def get_diagnostics():
    global DIAGNOSTICS_INSTANCE

    if DIAGNOSTICS_INSTANCE is None:
        DIAGNOSTICS_INSTANCE = DiagnosticsManager()

    return DIAGNOSTICS_INSTANCE

def speak_response(
    tts: TTSService,
    text: str
):
    try:
        tts.speak(
            text
        )

    except Exception:
        pass


def print_jarvis(
    message: str,
    tts: TTSService | None = None,
    user_input: str = "",
    source: str = ""
):
    print(
        f"\nJarvis: {message}"
    )

    if user_input:
        try:
            get_logger().log_chat(
                user_input=user_input,
                jarvis_response=message,
                source=source
            )

        except Exception:
            pass

    if tts is not None:
        speak_response(
            tts,
            message
        )


def should_silence_voice_input_result(
    result: dict
) -> bool:
    message = str(
        result.get(
            "message",
            ""
        )
    ).lower()

    silent_phrases = [
        "listening timed out",
        "could not understand",
        "no speech was detected"
    ]

    return any(
        phrase in message
        for phrase in silent_phrases
    )


def generate_llm_response(
    llm,
    user_input: str
) -> str:
    try:
        return llm.generate(
            f"""
            You are Jarvis.

            Truth rules:
            - Do not claim live internet access.
            - Do not claim system facts unless a system tool checked them.
            - Do not claim actions were completed unless tools executed.

            User: {user_input}
            """
        )

    except Exception as e:
        return (
            "Gemini is currently unavailable. "
            f"Error: {e}"
        )


def execute_tool_route(
    route: dict,
    tool_manager: ToolManager
):
    route = route.copy()

    tool_name = route.pop(
        "tool",
        None
    )

    if not tool_name:
        return "No tool was selected."

    if tool_name == "system_info":
        return SystemInfoTool().execute(
            **route
        )

    if tool_name == "window_intelligence":
        return WindowIntelligenceTool().execute(
            **route
        )

    if tool_name == "browser_intelligence":
        return BrowserIntelligenceTool().execute(
            **route
        )

    if tool_name == "web_reader":
        return WebReaderTool().execute(
            **route
        )

    return tool_manager.execute(
        tool_name,
        **route
    )


def execute_route_sequence(
    routes: list[dict],
    tool_manager: ToolManager,
    state: dict,
    user_input: str
) -> str:
    responses = []

    for route in routes:
        response = execute_tool_route(
            route,
            tool_manager
        )

        responses.append(
            str(
                response
            )
        )

        try:
            get_logger().log_tool_result(
                user_input=user_input,
                route=route,
                result=str(
                    response
                )
            )

        except Exception:
            pass

    final_response = "\n".join(
        responses
    )

    state["last_user_command"] = user_input
    state["last_routes"] = routes
    state["last_tool_result"] = final_response

    get_memory().update_command_context(
        user_input,
        routes,
        final_response
    )

    return final_response


def is_powershell_command(
    text: str
) -> bool:
    lowered = text.lower().strip()

    blocked_starts = [
        "uv run python ",
        "python ",
        "pip ",
        "uv add ",
        "new-item ",
        "get-content ",
        "set-executionpolicy ",
        "cd ",
        "dir ",
        "ls ",
        "ollama pull ",
        "ollama run ",
        "ollama list"
    ]

    return any(
        lowered.startswith(
            item
        )
        for item in blocked_starts
    )


def get_fast_local_response(
    text: str
) -> str | None:
    text = text.lower().strip().rstrip("?!. ")

    greetings = [
        "hi",
        "hii",
        "hello",
        "hey",
        "hey jarvis",
        "hello jarvis",
        "hi jarvis"
    ]

    if text in greetings:
        return "Hello, Sir."

    if text in [
        "what is your name",
        "who are you",
        "your name",
        "tell me your name",
        "name"
    ]:
        return "My name is Jarvis. I am your Windows desktop assistant."

    if text in [
        "how are you",
        "how are you jarvis"
    ]:
        return "I'm functioning within normal parameters."

    if text in [
        "thanks",
        "thank you",
        "thank you jarvis",
        "good boy"
    ]:
        return "You're welcome, Sir."

    if text in [
        "are you local",
        "are you running locally",
        "are you offline"
    ]:
        return (
            "Yes. My AI brain runs locally through Ollama. "
            "I can open/search web pages, but I cannot read live webpages yet."
        )

    if text in [
        "can you access the net",
        "can u access the net",
        "do you have internet",
        "can you use internet"
    ]:
        return (
            "I can open websites and perform searches. "
            "I cannot directly read live webpages yet until we add the web-reading module."
        )

    return None

def split_compound_command(
    user_input: str
) -> list[str]:
    text = str(
        user_input
    ).strip()

    if not text:
        return []

    parts = re.split(
        r"\s*(?:,\s*then\s+|\s+then\s+|\s+and then\s+)\s*",
        text,
        flags=re.IGNORECASE
    )

    expanded_parts = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        lowered = part.lower()

        open_and_search = re.match(
            r"open\s+(.+?)\s+and\s+search\s+(.+)$",
            lowered
        )

        if open_and_search:
            app_name = open_and_search.group(
                1
            ).strip()

            search_command = "search " + open_and_search.group(
                2
            ).strip()

            expanded_parts.append(
                f"open {app_name}"
            )

            expanded_parts.append(
                search_command
            )

            continue

        expanded_parts.append(
            part
        )

    return expanded_parts

def normalize_command_text(
    user_input: str
) -> str:
    text = str(
        user_input
    ).strip()

    lowered = text.lower()

    replacements = [
        ("can you please ", ""),
        ("can you ", ""),
        ("could you ", ""),
        ("please ", ""),
        ("open the ", "open "),
        ("close the ", "close "),
        ("launch the ", "open "),
        ("start the ", "open ")
    ]

    for old, new in replacements:
        if lowered.startswith(
            old
        ):
            return new + text[
                len(old):
            ].strip()

    return text


def get_direct_route(
    user_input: str
) -> dict | None:
    text = user_input.lower().strip().rstrip("?!. ")

    direct_routes = {
        "open youtube": {
            "tool": "web_control",
            "action": "open_shortcut",
            "target": "youtube"
        },
        "open yt": {
            "tool": "web_control",
            "action": "open_shortcut",
            "target": "youtube"
        },
        "close this tab": {
            "tool": "browser_control",
            "action": "close_tab"
        },
        "close current tab": {
            "tool": "browser_control",
            "action": "close_tab"
        },
        "close the tab": {
            "tool": "browser_control",
            "action": "close_tab"
        },
        "close tab": {
            "tool": "browser_control",
            "action": "close_tab"
        },
        "go to next tab": {
            "tool": "browser_control",
            "action": "next_tab"
        },
        "next tab": {
            "tool": "browser_control",
            "action": "next_tab"
        },
        "go to previous tab": {
            "tool": "browser_control",
            "action": "previous_tab"
        },
        "previous tab": {
            "tool": "browser_control",
            "action": "previous_tab"
        },
        "refresh the page": {
            "tool": "browser_control",
            "action": "refresh"
        },
        "refresh page": {
            "tool": "browser_control",
            "action": "refresh"
        },
        "refresh the webpage": {
            "tool": "browser_control",
            "action": "refresh"
        },
        "scroll down": {
            "tool": "browser_control",
            "action": "scroll_down"
        },
        "scroll up": {
            "tool": "browser_control",
            "action": "scroll_up"
        },
        "current url": {
            "tool": "browser_intelligence",
            "action": "current_url"
        },
        "read current url": {
            "tool": "browser_intelligence",
            "action": "current_url"
        },
        "what is current url": {
            "tool": "browser_intelligence",
            "action": "current_url"
        },
        "current tab title": {
            "tool": "browser_intelligence",
            "action": "current_title"
        },
        "read current tab title": {
            "tool": "browser_intelligence",
            "action": "current_title"
        },
        "list browser windows": {
            "tool": "browser_intelligence",
            "action": "list_browser_windows"
        },
        "close downloads folder": {
            "tool": "window_intelligence",
            "action": "close_file_explorer",
            "target": "downloads"
        },
        "close downloads": {
            "tool": "window_intelligence",
            "action": "close_file_explorer",
            "target": "downloads"
        },
        "close file explorer": {
            "tool": "window_intelligence",
            "action": "close_file_explorer"
        },
        "close explorer": {
            "tool": "window_intelligence",
            "action": "close_file_explorer"
        },
        "close task manager": {
            "tool": "window_intelligence",
            "action": "close_task_manager"
        },
        "close task": {
            "tool": "window_intelligence",
            "action": "close_task_manager"
        },
        "list windows": {
            "tool": "window_intelligence",
            "action": "list_windows"
        },
        "show windows": {
            "tool": "window_intelligence",
            "action": "list_windows"
        },
        "window list": {
            "tool": "window_intelligence",
            "action": "list_windows"
        },
        "list file explorer windows": {
            "tool": "window_intelligence",
            "action": "list_file_explorer"
        },
        "detect file explorer folders": {
            "tool": "window_intelligence",
            "action": "list_file_explorer"
        },
        "system status": {
            "tool": "system_info",
            "action": "usage"
        },
        "full system status": {
            "tool": "system_info",
            "action": "full_status"
        },
        "percentage usage": {
            "tool": "system_info",
            "action": "usage"
        },
        "what is the usage": {
            "tool": "system_info",
            "action": "usage"
        },
        "gpu usage": {
            "tool": "system_info",
            "action": "gpu_usage"
        },
        "cpu usage": {
            "tool": "system_info",
            "action": "cpu_usage"
        },
        "ram usage": {
            "tool": "system_info",
            "action": "ram_usage"
        },
        "battery status": {
            "tool": "system_info",
            "action": "battery"
        },
        "laptop battery status": {
            "tool": "system_info",
            "action": "battery"
        },
        "storage usage": {
            "tool": "system_info",
            "action": "storage"
        },
        "disk usage": {
            "tool": "system_info",
            "action": "storage"
        },
        "network status": {
            "tool": "system_info",
            "action": "network"
        },
        "network speed": {
            "tool": "system_info",
            "action": "network"
        },
        "thermal status": {
            "tool": "system_info",
            "action": "thermal"
        },
        "fan status": {
            "tool": "system_info",
            "action": "thermal"
        },
        "temperature status": {
            "tool": "system_info",
            "action": "thermal"
        },
        "check system status": {
            "tool": "system_info",
            "action": "usage"
        },
        "what is my ip": {
            "tool": "system_info",
            "action": "network"
        },
        "do you know my ip": {
            "tool": "system_info",
            "action": "network"
        },
        "check my ip": {
            "tool": "system_info",
            "action": "network"
        },
        "close taskmanager": {
            "tool": "window_intelligence",
            "action": "close_task_manager"
        },
        "close task manager window": {
            "tool": "window_intelligence",
            "action": "close_task_manager"
        },
    }

    if text in direct_routes:
        return direct_routes[text]

    youtube_patterns = [
        r"search\s+(.+?)\s+on\s+youtube$",
        r"search\s+youtube\s+for\s+(.+)$",
        r"youtube\s+search\s+(.+)$",
        r"find\s+(.+?)\s+on\s+youtube$"
    ]

    for pattern in youtube_patterns:
        match = re.match(
            pattern,
            text
        )

        if match:
            return {
                "tool": "web_control",
                "action": "search",
                "engine": "youtube",
                "target": match.group(1).strip()
            }

    google_match = re.match(
        r"search\s+(.+?)\s+on\s+google(?:\s+in\s+(.+))?$",
        text
    )

    if google_match:
        route = {
            "tool": "web_control",
            "action": "search",
            "engine": "google",
            "target": google_match.group(1).strip()
        }

        browser = google_match.group(2)

        if browser:
            route["browser"] = browser.strip()

        return route

    close_tab_title_match = re.match(
        r"close\s+(?:tab|browser tab)\s+(?:named|called|titled)\s+(.+)$",
        text
    )

    if close_tab_title_match:
        return {
            "tool": "browser_intelligence",
            "action": "close_tab_by_title",
            "target": close_tab_title_match.group(1).strip()
        }

    switch_tab_title_match = re.match(
        r"(?:switch|go)\s+to\s+(?:tab|browser tab)\s+(?:named|called|titled)\s+(.+)$",
        text
    )

    if switch_tab_title_match:
        return {
            "tool": "browser_intelligence",
            "action": "switch_tab_by_title",
            "target": switch_tab_title_match.group(1).strip()
        }

    close_window_title_match = re.match(
        r"close\s+window\s+(?:named|called|titled)\s+(.+)$",
        text
    )

    if close_window_title_match:
        return {
            "tool": "window_intelligence",
            "action": "close_by_title",
            "target": close_window_title_match.group(1).strip()
        }

    switch_window_title_match = re.match(
        r"(?:switch|go)\s+to\s+window\s+(?:named|called|titled)\s+(.+)$",
        text
    )

    if switch_window_title_match:
        return {
            "tool": "window_intelligence",
            "action": "switch_by_title",
            "target": switch_window_title_match.group(1).strip()
        }

    read_url_match = re.match(
        r"(?:read|open and read)\s+(?:webpage|website|page)\s+(.+)$",
        text
    )

    if read_url_match:
        return {
            "tool": "web_reader",
            "action": "read_url",
            "target": read_url_match.group(1).strip()
        }

    summarize_url_match = re.match(
        r"summarize\s+(?:webpage|website|page)\s+(.+)$",
        text
    )

    if summarize_url_match:
        return {
            "tool": "web_reader",
            "action": "summarize_url",
            "target": summarize_url_match.group(1).strip()
        }

    links_match = re.match(
        r"extract\s+links\s+from\s+(.+)$",
        text
    )

    if links_match:
        return {
            "tool": "web_reader",
            "action": "extract_links",
            "target": links_match.group(1).strip()
        }

    tables_match = re.match(
        r"extract\s+tables\s+from\s+(.+)$",
        text
    )

    if tables_match:
        return {
            "tool": "web_reader",
            "action": "extract_tables",
            "target": tables_match.group(1).strip()
        }

    wiki_match = re.match(
        r"(?:wikipedia|search wikipedia for|read wikipedia for|check wikipedia for|check on wikipedia for)\s+(.+)$",
        text
    )

    if wiki_match:
        return {
            "tool": "web_reader",
            "action": "wikipedia",
            "target": wiki_match.group(1).strip()
        }

    search_results_match = re.match(
        r"(?:read search results for|search results for)\s+(.+)$",
        text
    )

    if search_results_match:
        return {
            "tool": "web_reader",
            "action": "search_results",
            "target": search_results_match.group(1).strip()
        }
    
    simple_youtube_match = re.match(
        r"search\s+(.+?)\s+youtube$",
        text
    )

    if simple_youtube_match:
        return {
            "tool": "web_control",
            "action": "search",
            "engine": "youtube",
            "target": simple_youtube_match.group(1).strip()
        }

    open_and_search_match = re.match(
        r"open\s+(.+?)\s+and\s+search\s+(.+?)\s+on\s+google(?:\s+in\s+(.+))?$",
        text
    )

    if open_and_search_match:
        app_name = open_and_search_match.group(
            1
        ).strip()

        search_target = open_and_search_match.group(
            2
        ).strip()

        browser = open_and_search_match.group(
            3
        )

        route = {
            "tool": "web_control",
            "action": "search",
            "engine": "google",
            "target": search_target
        }

        if browser:
            route["browser"] = browser.strip()

        else:
            route["browser"] = app_name

        return route

    return None

def should_use_ai_tool_router(
    text: str
) -> bool:
    text = text.lower().strip()

    tool_keywords = [
        "open ",
        "close ",
        "search ",
        "google ",
        "youtube ",
        "wikipedia",
        "read webpage",
        "read website",
        "read page",
        "summarize webpage",
        "summarize website",
        "extract links",
        "extract tables",
        "search results",
        "tab",
        "browser",
        "current url",
        "current tab",
        "comet",
        "edge",
        "chrome",
        "screenshot",
        "screen snip",
        "snipping tool",
        "presentation",
        "ppt",
        "powerpoint",
        "document",
        "report",
        "essay",
        "pdf",
        "folder",
        "file",
        "clipboard",
        "copy ",
        "paste",
        "type ",
        "select all",
        "window",
        "minimize",
        "maximize",
        "snap",
        "volume",
        "mute",
        "sleep",
        "shutdown",
        "restart",
        "lock pc",
        "lock my pc",
        "usage",
        "gpu",
        "cpu",
        "ram",
        "system status",
        "battery",
        "storage",
        "disk usage",
        "network",
        "thermal",
        "fan",
        "temperature"
    ]

    return any(
        keyword in text
        for keyword in tool_keywords
    )

def needs_live_web_reading(
    text: str
) -> bool:
    text = text.lower()

    web_phrases = [
        "check wikipedia",
        "on wikipedia",
        "latest",
        "current",
        "today",
        "right now",
        "exact numericals",
        "exact numbers",
        "live score",
        "current score"
    ]

    return any(
        phrase in text
        for phrase in web_phrases
    )


def handle_grounded_memory_or_system_questions(
    text: str,
    tts: TTSService,
    tool_manager: ToolManager,
    state: dict
) -> bool:
    memory = get_memory()

    if text in [
        "what is my gpu",
        "my gpu",
        "what gpu do i have"
    ]:
        saved_gpu = memory.get_system_fact(
            "gpu"
        )

        if saved_gpu:
            print_jarvis(
                f"Your saved GPU is {saved_gpu}.",
                tts
            )

            return True

        response = execute_tool_route(
            {
                "tool": "system_info",
                "action": "gpu"
            },
            tool_manager
        )

        print_jarvis(
            response,
            tts
        )

        return True

    if text in [
        "what is my cpu",
        "my cpu",
        "what processor do i have",
        "what is my processor"
    ]:
        saved_cpu = memory.get_system_fact(
            "cpu"
        )

        if saved_cpu:
            print_jarvis(
                f"Your saved CPU is {saved_cpu}.",
                tts
            )

            return True

        response = execute_tool_route(
            {
                "tool": "system_info",
                "action": "cpu"
            },
            tool_manager
        )

        print_jarvis(
            response,
            tts
        )

        return True

    if text in [
        "what is my ram",
        "my ram",
        "how much ram do i have",
        "what is the total ram of this computer"
    ]:
        saved_ram = memory.get_system_fact(
            "ram"
        )

        if saved_ram:
            print_jarvis(
                f"Your saved RAM is {saved_ram}.",
                tts
            )

            return True

        response = execute_tool_route(
            {
                "tool": "system_info",
                "action": "ram"
            },
            tool_manager
        )

        print_jarvis(
            response,
            tts
        )

        return True

    if text in [
        "what are my specs",
        "my specs",
        "system specs",
        "system information"
    ]:
        response = execute_tool_route(
            {
                "tool": "system_info",
                "action": "summary"
            },
            tool_manager
        )

        print_jarvis(
            response,
            tts
        )

        return True

    return False


def handle_memory_commands(
    user_input: str,
    text: str,
    tts: TTSService
) -> bool:
    memory = get_memory()

    forget_map = {
        "forget my gpu": "gpu",
        "forget gpu": "gpu",
        "forget my cpu": "cpu",
        "forget cpu": "cpu",
        "forget my processor": "cpu",
        "forget processor": "cpu",
        "forget my ram": "ram",
        "forget ram": "ram",
        "forget memory": "ram"
    }

    if text in forget_map:
        print_jarvis(
            memory.forget_system_fact(
                forget_map[text]
            ),
            tts,
            user_input=user_input,
            source="memory"
        )

        return True

    if text in [
        "clear system memory",
        "clear pc memory",
        "clear saved pc memory",
        "clear hardware memory"
    ]:
        result = memory.clear_system_memory()

        get_logger().log_memory_change(
            user_input=user_input,
            change_type="clear_system_memory",
            result=result
        )

        print_jarvis(
            result,
            tts,
            user_input=user_input,
            source="memory"
        )

        return True

    if text in [
        "show memory",
        "show jarvis memory",
        "show saved memory"
    ]:
        print_jarvis(
            memory.get_context_text(),
            tts,
            user_input=user_input,
            source="memory"
        )

        return True

    if text in [
        "what do you remember about my pc",
        "what do you remember about my computer",
        "show pc memory",
        "show system memory",
        "what are my saved specs"
    ]:
        print_jarvis(
            memory.get_system_memory_text(),
            tts,
            user_input=user_input,
            source="memory"
        )

        return True

    system_response = memory.extract_and_store_system_profile(
        user_input
    )

    if system_response:
        get_logger().log_memory_change(
            user_input=user_input,
            change_type="system_profile_update",
            result=system_response
        )

        print_jarvis(
            system_response,
            tts,
            user_input=user_input,
            source="memory"
        )

        return True

    memory_response = memory.remember_from_text(
        user_input
    )

    if memory_response:
        print_jarvis(
            memory_response,
            tts,
            user_input=user_input,
            source="memory"
        )

        return True

    return False


def handle_ai_status_commands(
    text: str,
    tts: TTSService
) -> bool:
    ai_router = get_ai_router()
    client = ai_router.client

    if text in [
        "ollama status",
        "ai status",
        "show ollama status",
        "show ai status"
    ]:
        print_jarvis(
            client.get_status_text(),
            tts
        )

        return True

    if text in [
        "list ai models",
        "list ollama models",
        "show ai models",
        "show ollama models"
    ]:
        ok, models, message = client.list_models()

        if not ok:
            print_jarvis(
                message,
                tts
            )

            return True

        if not models:
            print_jarvis(
                "No Ollama models found.",
                tts
            )

            return True

        response = "Installed Ollama models:\n"

        for model in models:
            response += f"- {model}\n"

        print_jarvis(
            response.strip(),
            tts
        )

        return True

    if text in [
        "warm up ai",
        "warmup ai",
        "warm up ollama",
        "load ai model",
        "load ollama model"
    ]:
        print_jarvis(
            client.warm_up(),
            tts
        )

        return True

    return False

def handle_ai_debug_commands(
    text: str,
    state: dict,
    tts: TTSService
) -> bool:
    if text in [
        "ai debug on",
        "debug ai on",
        "show ai routes on"
    ]:
        state["ai_debug"] = True

        print_jarvis(
            "AI debug mode enabled.",
            tts
        )

        return True

    if text in [
        "ai debug off",
        "debug ai off",
        "show ai routes off"
    ]:
        state["ai_debug"] = False

        print_jarvis(
            "AI debug mode disabled.",
            tts
        )

        return True

    if text in [
        "ai debug status",
        "debug ai status"
    ]:
        status = (
            "enabled"
            if state.get(
                "ai_debug",
                False
            )
            else "disabled"
        )

        print_jarvis(
            f"AI debug mode is {status}.",
            tts
        )

        return True

    return False

def handle_training_data_commands(
    text: str,
    state: dict,
    tts: TTSService,
    user_input: str
) -> bool:
    diagnostics = get_diagnostics()
    logger = get_logger()

    if text in [
        "training data status",
        "diagnostics status",
        "show diagnostics status"
    ]:
        print_jarvis(
            diagnostics.get_status(),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "show diagnostics policy",
        "show privacy policy",
        "read diagnostics policy",
        "read privacy policy"
    ]:
        print_jarvis(
            diagnostics.read_privacy_policy(),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "enable diagnostics upload",
        "allow diagnostics upload",
        "enable training data upload",
        "allow training data upload"
    ]:
        state["pending_diagnostics_consent"] = True

        print_jarvis(
            (
                "Diagnostics upload requires consent. "
                "Read the privacy policy first with 'show diagnostics policy'. "
                "Then say 'confirm diagnostics consent' to enable uploads."
            ),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "confirm diagnostics consent",
        "confirm training data upload",
        "i accept diagnostics policy"
    ]:
        if not state.get(
            "pending_diagnostics_consent",
            False
        ):
            print_jarvis(
                (
                    "No diagnostics consent request is pending. "
                    "Say 'enable diagnostics upload' first."
                ),
                tts,
                user_input=user_input,
                source="diagnostics"
            )

            return True

        state["pending_diagnostics_consent"] = False

        print_jarvis(
            diagnostics.accept_policy_and_enable_upload(),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "disable diagnostics upload",
        "disable training data upload",
        "turn off diagnostics upload"
    ]:
        print_jarvis(
            diagnostics.disable_upload(),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text.startswith(
        "set diagnostics endpoint "
    ):
        endpoint = user_input[
            len(
                "set diagnostics endpoint "
            ):
        ].strip()

        print_jarvis(
            diagnostics.set_upload_endpoint(
                endpoint
            ),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "export training data",
        "export diagnostics",
        "export logs"
    ]:
        print_jarvis(
            diagnostics.export_logs(
                logger
            ),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "delete training data",
        "delete diagnostics",
        "delete logs",
        "clear training data"
    ]:
        state["pending_delete_training_data"] = True

        print_jarvis(
            (
                "This will delete local Training_Data logs. "
                "Say 'confirm delete training data' to continue, or 'cancel'."
            ),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "confirm delete training data",
        "confirm delete diagnostics",
        "confirm delete logs"
    ]:
        if not state.get(
            "pending_delete_training_data",
            False
        ):
            print_jarvis(
                "No Training_Data delete request is pending.",
                tts,
                user_input=user_input,
                source="diagnostics"
            )

            return True

        state["pending_delete_training_data"] = False

        print_jarvis(
            diagnostics.delete_logs(
                logger
            ),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    if text in [
        "send diagnostics",
        "upload diagnostics",
        "send training data",
        "upload training data"
    ]:
        print_jarvis(
            diagnostics.send_diagnostics(
                logger
            ),
            tts,
            user_input=user_input,
            source="diagnostics"
        )

        return True

    return False

def handle_voice_training(
    user_input: str,
    state: dict,
    stt: STTService,
    tts: TTSService
) -> bool:
    text = user_input.lower().strip()

    if text in [
        "list voice corrections",
        "show voice corrections",
        "voice corrections"
    ]:
        print_jarvis(
            stt.list_corrections(),
            tts
        )

        return True

    correction_prefix = "correct last command to "

    if text.startswith(
        correction_prefix
    ):
        correct_command = user_input[
            len(correction_prefix):
        ].strip()

        last_raw = state.get(
            "last_voice_raw",
            ""
        )

        if not last_raw:
            print_jarvis(
                "No previous voice command is available to correct.",
                tts
            )

            return True

        response = stt.add_correction(
            last_raw,
            correct_command
        )

        print_jarvis(
            response,
            tts
        )

        return True

    train_prefix = "train voice "

    if text.startswith(
        train_prefix
    ) and " means " in text:
        remaining = user_input[
            len(train_prefix):
        ].strip()

        lower_remaining = remaining.lower()
        split_text = " means "
        split_index = lower_remaining.find(
            split_text
        )

        wrong_phrase = remaining[
            :split_index
        ].strip()

        correct_command = remaining[
            split_index + len(split_text):
        ].strip()

        response = stt.add_correction(
            wrong_phrase,
            correct_command
        )

        print_jarvis(
            response,
            tts
        )

        return True

    return False


def handle_voice_input_settings(
    text: str,
    stt: STTService,
    tts: TTSService
) -> bool:
    if text in [
        "voice input on",
        "microphone on",
        "mic on"
    ]:
        stt.set_enabled(
            True
        )

        print_jarvis(
            "Voice input enabled.",
            tts
        )

        return True

    if text in [
        "voice input off",
        "microphone off",
        "mic off"
    ]:
        stt.set_enabled(
            False
        )

        print_jarvis(
            "Voice input disabled.",
            tts
        )

        return True

    if text in [
        "list microphones",
        "show microphones",
        "list mics",
        "show mics"
    ]:
        print_jarvis(
            stt.list_microphones(),
            tts
        )

        return True

    return False


def handle_voice_output_settings(
    text: str,
    tts: TTSService
) -> bool:
    if text == "voice off":
        tts.config.set_enabled(
            False
        )

        print(
            "\nJarvis: Voice output disabled."
        )

        return True

    if text == "voice on":
        tts.config.set_enabled(
            True
        )

        print_jarvis(
            "Voice output enabled.",
            tts
        )

        return True

    return False


def handle_pending_power_action(
    text: str,
    state: dict,
    tool_manager: ToolManager,
    tts: TTSService
) -> bool:
    pending_action = state.get(
        "pending_power_action"
    )

    pending_time = state.get(
        "pending_power_time",
        0
    )

    if not pending_action:
        return False

    expired = (
        time.time() - pending_time
    ) > POWER_CONFIRM_TIMEOUT

    if expired:
        state["pending_power_action"] = None
        state["pending_power_time"] = 0

        print_jarvis(
            "Power confirmation expired.",
            tts
        )

        return False

    if text in [
        "cancel",
        "cancel command",
        "cancel power command",
        "no"
    ]:
        state["pending_power_action"] = None
        state["pending_power_time"] = 0

        print_jarvis(
            "Power command cancelled.",
            tts
        )

        return True

    confirm_text = POWER_ACTIONS[pending_action]["confirm"]

    if text == confirm_text or text == "confirm":
        state["pending_power_action"] = None
        state["pending_power_time"] = 0

        response = tool_manager.execute(
            "system_control",
            action=pending_action
        )

        print_jarvis(
            response,
            tts
        )

        return True

    print_jarvis(
        (
            f"Pending power command: {POWER_ACTIONS[pending_action]['label']}. "
            f"Say '{confirm_text}' or 'cancel'."
        ),
        tts
    )

    return True


def handle_power_route(
    route: dict,
    state: dict,
    tts: TTSService
) -> bool:
    if (
        route.get("tool") == "system_control"
        and route.get("action") in POWER_ACTIONS
    ):
        action = route["action"]

        state["pending_power_action"] = action
        state["pending_power_time"] = time.time()

        print_jarvis(
            (
                f"Power command requested: {POWER_ACTIONS[action]['label']}. "
                f"Say '{POWER_ACTIONS[action]['confirm']}' to continue, "
                "or 'cancel'."
            ),
            tts
        )

        return True

    return False


def handle_followup_commands(
    text: str,
    tool_manager: ToolManager,
    state: dict,
    tts: TTSService
) -> bool:
    followup_phrases = [
        "go ahead",
        "do it",
        "retry",
        "try again",
        "you did not",
        "you didn't",
        "do that"
    ]

    if not any(
        phrase in text
        for phrase in followup_phrases
    ):
        return False

    routes = state.get(
        "last_routes",
        []
    )

    if not routes:
        routes = get_memory().get_last_routes()

    if not routes:
        print_jarvis(
            "No previous executable action is available to retry.",
            tts
        )

        return True

    response = execute_route_sequence(
        routes,
        tool_manager,
        state,
        state.get(
            "last_user_command",
            ""
        )
    )

    print_jarvis(
        response,
        tts
    )

    return True


def process_command(
    user_input: str,
    router: Router,
    tool_manager: ToolManager,
    llm,
    tts: TTSService,
    stt: STTService,
    state: dict,
    allow_compound: bool = True
) -> bool:
    user_input = str(
        user_input
    ).strip()

    if not user_input:
        return False

    if allow_compound:
        command_parts = split_compound_command(
            user_input
        )

        if len(
            command_parts
        ) > 1:
            for command_part in command_parts:
                should_exit = process_command(
                    command_part,
                    router,
                    tool_manager,
                    llm,
                    tts,
                    stt,
                    state,
                    allow_compound=False
                )

                if should_exit:
                    return True

            return False

    user_input = normalize_command_text(
        user_input
    )

    text = user_input.lower().strip()

    if is_powershell_command(
        text
    ):
        print_jarvis(
            (
                "That looks like a PowerShell command. "
                "Run it in the terminal, not inside Jarvis."
            ),
            tts
        )

        return False

    if text in [
        "exit",
        "quit jarvis",
        "exit jarvis",
        "bye jarvis",
        "exit please",
        "can you exit"
    ]:
        print_jarvis(
            "Goodbye, Sir.",
            tts
        )

        return True

    if handle_voice_training(
        user_input,
        state,
        stt,
        tts
    ):
        return False

    if handle_voice_output_settings(
        text,
        tts
    ):
        return False

    if handle_voice_input_settings(
        text,
        stt,
        tts
    ):
        return False

    if handle_ai_debug_commands(
        text,
        state,
        tts
    ):
        return False
    
    if handle_training_data_commands(
        text,
        state,
        tts,
        user_input
    ):
        return False

    if handle_pending_power_action(
        text,
        state,
        tool_manager,
        tts
    ):
        return False

    if handle_memory_commands(
        user_input,
        text,
        tts
    ):
        return False

    if handle_followup_commands(
        text,
        tool_manager,
        state,
        tts
    ):
        return False

    fast_response = get_fast_local_response(
        text
    )

    if fast_response:
        print_jarvis(
            fast_response,
            tts
        )

        return False

    if handle_grounded_memory_or_system_questions(
        text,
        tts,
        tool_manager,
        state
    ):
        return False

    direct_route = get_direct_route(
        user_input
    )

    if direct_route:
        if state.get(
            "ai_debug",
            False
        ):
            print(
                f"\n[DEBUG] Direct route: {direct_route}"
            )

        if handle_power_route(
            direct_route,
            state,
            tts
        ):
            return False

        response = execute_route_sequence(
            [direct_route],
            tool_manager,
            state,
            user_input
        )

        print_jarvis(
            response,
            tts,
            user_input=user_input,
            source="direct_route"
        )

        return False

    route = router.route(
        user_input
    )

    if route:
        if state.get(
            "ai_debug",
            False
        ):
            print(
                f"\n[DEBUG] Exact router route: {route}"
            )

        if handle_power_route(
            route,
            state,
            tts
        ):
            return False

        response = execute_route_sequence(
            [route],
            tool_manager,
            state,
            user_input
        )

        print_jarvis(
            response,
            tts,
            user_input=user_input,
            source="exact_router"
        )

        return False

    ai_router = get_ai_router()
    memory = get_memory()

    memory_context = memory.get_context_text()

    if not should_use_ai_tool_router(
        text
    ):
        ai_response = ai_router.generate_response(
            user_input,
            memory_context=memory_context,
            tool_context=state.get(
                "last_tool_result",
                ""
            )
        )

        if ai_response:
            print_jarvis(
                ai_response,
                tts
            )

            return False

        response = generate_llm_response(
            llm,
            user_input
        )

        print_jarvis(
            response,
            tts
        )

        return False

    ai_result = ai_router.plan(
        user_input,
        memory_context=memory_context
    )
 
    ai_result = ai_router.plan(
        user_input,
        memory_context=memory_context
    )

    try:
        get_logger().log_ai_plan(
            user_input,
            ai_result,
            memory_context=memory_context
        )

    except Exception:
        pass

    if state.get(
        "ai_debug",
        False
    ):
        print(
            f"\n[DEBUG] AI plan result: {ai_result}"
        )
 
 

    if ai_result.get(
        "success"
    ):
        routes = ai_result.get(
            "routes",
            []
        )

        for route_item in routes:
            if handle_power_route(
                route_item,
                state,
                tts
            ):
                return False

        response = execute_route_sequence(
            routes,
            tool_manager,
            state,
            user_input
        )

        print_jarvis(
            response,
            tts
        )

        return False

    ai_response = ai_router.generate_response(
        user_input,
        memory_context=memory_context,
        tool_context=state.get(
            "last_tool_result",
            ""
        )
    )
    try:
        get_logger().log_ai_failure(
            user_input,
            ai_result,
            memory_context=memory_context
        )

    except Exception:
        pass


    if ai_response:
        print_jarvis(
            ai_response,
            tts
        )

        return False

    response = generate_llm_response(
        llm,
        user_input
    )

    print_jarvis(
        response,
        tts
    )

    return False


def listen_once_as_command(
    stt: STTService,
    tts: TTSService,
    state: dict
):
    print_jarvis(
        "Listening.",
        tts
    )

    result = stt.listen_once()

    if not result["success"]:
        if should_silence_voice_input_result(
            result
        ):
            return None

        print_jarvis(
            result["message"],
            tts
        )

        return None

    raw_text = result.get(
        "raw_text",
        result["text"]
    )

    command = result["text"]

    state["last_voice_raw"] = raw_text
    state["last_voice_command"] = command

    try:
        get_logger().log_voice_event(
            raw_text=raw_text,
            corrected_text=command,
            success=True,
            mode="listen_once"
        )

    except Exception:
        pass

    print(
        f"\nYou said: {raw_text}"
    )

    if command != raw_text:
        print(
            f"Corrected to: {command}"
        )

    return command


def run_continuous_listen_mode(
    router: Router,
    tool_manager: ToolManager,
    llm,
    tts: TTSService,
    stt: STTService,
    state: dict
) -> bool:
    stt.set_enabled(
        True
    )

    print_jarvis(
        (
            "Continuous listening started. "
            "Say 'listen off' or 'stop listening' to stop."
        ),
        tts
    )

    while True:
        print(
            "\nJarvis: Listening..."
        )

        result = stt.listen_once()

        if not result["success"]:
            if should_silence_voice_input_result(
                result
            ):
                continue

            print(
                f"\nJarvis: {result['message']}"
            )
            continue

        raw_text = result.get(
            "raw_text",
            result["text"]
        )

        command = result["text"]

        state["last_voice_raw"] = raw_text
        state["last_voice_command"] = command

        try:
            get_logger().log_voice_event(
                raw_text=raw_text,
                corrected_text=command,
                success=True,
                mode="continuous"
            )

        except Exception:
            pass

        print(
            f"\nYou said: {raw_text}"
        )

        if command != raw_text:
            print(
                f"Corrected to: {command}"
            )

        command_text = command.lower().strip()

        if command_text in [
            "listen off",
            "stop listening",
            "stop listen",
            "stop voice input",
            "exit listening",
            "exit listen mode"
        ]:
            print_jarvis(
                "Continuous listening stopped.",
                tts
            )

            return False

        should_exit = process_command(
            command,
            router,
            tool_manager,
            llm,
            tts,
            stt,
            state
        )

        if should_exit:
            return True


def run_voice_mode(
    router: Router,
    tool_manager: ToolManager,
    llm,
    tts: TTSService,
    stt: STTService,
    state: dict
) -> bool:
    print_jarvis(
        (
            "Wake-word voice mode started. "
            "Say 'wake up Jarvis' followed by a command. "
            "Say 'stop listening' to leave voice mode."
        ),
        tts
    )

    while True:
        result = stt.listen_once()

        if not result["success"]:
            if should_silence_voice_input_result(
                result
            ):
                continue

            print(
                f"\nJarvis: {result['message']}"
            )
            continue

        raw_text = result.get(
            "raw_text",
            result["text"]
        )

        heard = result["text"]
        heard_lower = heard.lower().strip()

        state["last_voice_raw"] = raw_text
        state["last_voice_command"] = heard

        try:
            get_logger().log_voice_event(
                raw_text=raw_text,
                corrected_text=heard,
                success=True,
                mode="wake_word"
            )

        except Exception:
            pass

        print(
            f"\nHeard: {raw_text}"
        )

        if heard != raw_text:
            print(
                f"Corrected to: {heard}"
            )

        if heard_lower in [
            "stop listening",
            "exit voice mode",
            "voice mode off",
            "stop voice mode",
            "listen off"
        ]:
            print_jarvis(
                "Voice mode stopped.",
                tts
            )

            return False

        command = stt.extract_wake_command(
            heard
        )

        if command is None:
            print(
                "\nJarvis: Wake word not detected."
            )
            continue

        if not command:
            print_jarvis(
                "Yes, Sir?",
                tts
            )
            continue

        print(
            f"\nVoice command: {command}"
        )

        should_exit = process_command(
            command,
            router,
            tool_manager,
            llm,
            tts,
            stt,
            state
        )

        if should_exit:
            return True


def main():
    router = Router()
    tool_manager = ToolManager()
    tts = TTSService()
    stt = STTService()

    try:
        llm = LLMManager()

    except Exception:
        llm = None

    state = {
        "pending_power_action": None,
        "pending_power_time": 0,
        "last_voice_raw": "",
        "last_voice_command": "",
        "last_user_command": "",
        "last_routes": [],
        "last_tool_result": "",
        "ai_debug": False,
        "pending_delete_training_data": False,
        "pending_diagnostics_consent": False
    }

    print("=" * 40)
    print("Jarvis Online")
    print("Type 'exit' to quit.")
    print("Type 'voice off' to disable speech.")
    print("Type 'voice on' to enable speech.")
    print("Type 'listen' to speak one command.")
    print("Type 'listen on' for continuous listening.")
    print("Type 'voice mode' for wake-word voice mode.")
    print("=" * 40)

    startup_message = get_ai_router().startup_check()

    print(
        f"AI: {startup_message}"
    )

    try:
        get_logger().log_startup_snapshot(
            {
                "ai_startup_message": startup_message
            }
        )

    except Exception:
        pass

    while True:
        try:
            user_input = input(
                "\nYou: "
            ).strip()

        except KeyboardInterrupt:
            print()
            continue

        text = user_input.lower().strip()

        if text in [
            "listen",
            "listen once",
            "voice command",
            "speak command"
        ]:
            spoken_command = listen_once_as_command(
                stt,
                tts,
                state
            )

            if not spoken_command:
                continue

            user_input = spoken_command

        elif text in [
            "listen on",
            "start listening",
            "continuous listening",
            "continuous listening on",
            "voice input continuous",
            "hands free mode"
        ]:
            should_exit = run_continuous_listen_mode(
                router,
                tool_manager,
                llm,
                tts,
                stt,
                state
            )

            if should_exit:
                break

            continue

        elif text in [
            "listen off",
            "stop listening"
        ]:
            print_jarvis(
                "Continuous listening is not running.",
                tts
            )

            continue

        elif text in [
            "voice mode",
            "start voice mode",
            "always listening",
            "wake word mode"
        ]:
            should_exit = run_voice_mode(
                router,
                tool_manager,
                llm,
                tts,
                stt,
                state
            )

            if should_exit:
                break

            continue

        command_start_time = time.perf_counter()

        try:
            should_exit = process_command(
                user_input,
                router,
                tool_manager,
                llm,
                tts,
                stt,
                state
            )

        except Exception as e:
            get_logger().log_error(
                "main.process_command",
                e,
                {
                    "user_input": user_input
                }
            )

            print_jarvis(
                f"Command failed: {e}",
                tts,
                user_input=user_input,
                source="error"
            )

            should_exit = False

        finally:
            try:
                get_logger().log_command_timing(
                    user_input=user_input,
                    start_time=command_start_time,
                    should_exit=should_exit
                )

            except Exception:
                pass

        if should_exit:
            break

    try:
        tts.shutdown(
            wait=False
        )

    except Exception:
        pass


if __name__ == "__main__":
    main()