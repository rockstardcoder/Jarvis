from jarvis.services.web_reader import WebReader
from jarvis.tools.base_tool import BaseTool


class WebReaderTool(BaseTool):

    name = "web_reader"

    def execute(
        self,
        action: str,
        target: str | None = None,
        query: str | None = None,
        url: str | None = None
    ):
        service = WebReader()

        value = target or query or url

        if action == "read_url":
            if not value:
                return "No URL was provided."

            return service.read_webpage(
                value
            )

        if action == "summarize_url":
            if not value:
                return "No URL was provided."

            return service.summarize_webpage(
                value
            )

        if action == "extract_links":
            if not value:
                return "No URL was provided."

            return service.extract_links(
                value
            )

        if action == "extract_tables":
            if not value:
                return "No URL was provided."

            return service.extract_tables(
                value
            )

        if action == "search_results":
            if not value:
                return "No search query was provided."

            return service.duckduckgo_search(
                value
            )

        if action == "wikipedia":
            if not value:
                return "No Wikipedia query was provided."

            return service.wikipedia(
                value
            )

        return f"Unknown web reader action: {action}"