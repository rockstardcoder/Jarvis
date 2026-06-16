import re
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup


class WebReader:

    def __init__(
        self
    ):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120 Safari/537.36 JarvisLocalAssistant/1.0"
                )
            }
        )

    def normalize_url(
        self,
        url: str
    ) -> str:
        url = str(
            url
        ).strip()

        if not url.startswith(
            (
                "http://",
                "https://"
            )
        ):
            url = "https://" + url

        return url

    def fetch(
        self,
        url: str,
        timeout: int = 12
    ) -> tuple[bool, str, str]:
        url = self.normalize_url(
            url
        )

        try:
            response = self.session.get(
                url,
                timeout=timeout
            )

            if response.status_code >= 400:
                return (
                    False,
                    "",
                    f"HTTP {response.status_code} while reading {url}"
                )

            return True, response.text, url

        except Exception as e:
            return False, "", f"Could not read webpage: {e}"

    def clean_soup(
        self,
        html: str
    ) -> BeautifulSoup:
        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "footer",
                "header",
                "nav",
                "form"
            ]
        ):
            tag.decompose()

        return soup

    def extract_title(
        self,
        soup: BeautifulSoup
    ) -> str:
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        heading = soup.find(
            [
                "h1",
                "h2"
            ]
        )

        if heading:
            return heading.get_text(
                " ",
                strip=True
            )

        return "Untitled page"

    def extract_text(
        self,
        soup: BeautifulSoup,
        max_chars: int = 4000
    ) -> str:
        text = soup.get_text(
            "\n",
            strip=True
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        if len(
            text
        ) > max_chars:
            return text[:max_chars].strip() + "\n\n[Text truncated]"

        return text.strip()

    def read_webpage(
        self,
        url: str
    ) -> str:
        ok, html, final_url_or_error = self.fetch(
            url
        )

        if not ok:
            return final_url_or_error

        soup = self.clean_soup(
            html
        )

        title = self.extract_title(
            soup
        )

        text = self.extract_text(
            soup,
            max_chars=2500
        )

        return (
            f"Page: {title}\n"
            f"URL: {final_url_or_error}\n\n"
            f"{text}"
        )

    def summarize_webpage(
        self,
        url: str
    ) -> str:
        page_text = self.read_webpage(
            url
        )

        if page_text.startswith(
            "Could not"
        ) or page_text.startswith(
            "HTTP "
        ):
            return page_text

        try:
            from jarvis.ai.ollama_client import OllamaClient

            client = OllamaClient()

            summary = client.generate_response(
                (
                    "Summarize this webpage in clear bullet points. "
                    "Do not invent facts outside the provided text.\n\n"
                    f"{page_text[:6000]}"
                )
            )

            if summary:
                return summary

        except Exception:
            pass

        return page_text[:1500]

    def extract_links(
        self,
        url: str
    ) -> str:
        ok, html, final_url_or_error = self.fetch(
            url
        )

        if not ok:
            return final_url_or_error

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        links = []
        seen = set()

        for node in soup.find_all(
            "a",
            href=True
        ):
            text = node.get_text(
                " ",
                strip=True
            )

            href = urljoin(
                final_url_or_error,
                node["href"]
            )

            if href in seen:
                continue

            seen.add(
                href
            )

            if not text:
                text = href

            links.append(
                (
                    text,
                    href
                )
            )

            if len(
                links
            ) >= 40:
                break

        if not links:
            return "No links found on this page."

        lines = [
            "Links found:"
        ]

        for index, (
            text,
            href
        ) in enumerate(
            links,
            start=1
        ):
            lines.append(
                f"{index}. {text} -> {href}"
            )

        return "\n".join(
            lines
        )

    def extract_tables(
        self,
        url: str
    ) -> str:
        ok, html, final_url_or_error = self.fetch(
            url
        )

        if not ok:
            return final_url_or_error

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        tables = soup.find_all(
            "table"
        )

        if not tables:
            return "No HTML tables found on this page."

        output = [
            f"Tables found on {final_url_or_error}:"
        ]

        for table_index, table in enumerate(
            tables[:5],
            start=1
        ):
            output.append(
                f"\nTable {table_index}:"
            )

            rows = table.find_all(
                "tr"
            )

            for row in rows[:12]:
                cells = row.find_all(
                    [
                        "th",
                        "td"
                    ]
                )

                values = [
                    cell.get_text(
                        " ",
                        strip=True
                    )
                    for cell in cells
                ]

                if values:
                    output.append(
                        " | ".join(
                            values
                        )
                    )

        return "\n".join(
            output
        )

    def duckduckgo_search(
        self,
        query: str
    ) -> str:
        search_url = (
            "https://duckduckgo.com/html/?q="
            + quote(
                query
            )
        )

        ok, html, final_url_or_error = self.fetch(
            search_url
        )

        if not ok:
            return final_url_or_error

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        results = []

        for result in soup.select(
            ".result"
        ):
            title_node = result.select_one(
                ".result__title a"
            )

            snippet_node = result.select_one(
                ".result__snippet"
            )

            if not title_node:
                continue

            title = title_node.get_text(
                " ",
                strip=True
            )

            href = title_node.get(
                "href",
                ""
            )

            snippet = ""

            if snippet_node:
                snippet = snippet_node.get_text(
                    " ",
                    strip=True
                )

            results.append(
                {
                    "title": title,
                    "url": href,
                    "snippet": snippet
                }
            )

            if len(
                results
            ) >= 8:
                break

        if not results:
            return (
                "No readable search results found. "
                "Search engine layout may have changed or blocked the request."
            )

        lines = [
            f"Search results for: {query}"
        ]

        for index, result in enumerate(
            results,
            start=1
        ):
            lines.append(
                f"\n{index}. {result['title']}"
            )

            if result["snippet"]:
                lines.append(
                    result["snippet"]
                )

            lines.append(
                result["url"]
            )

        return "\n".join(
            lines
        )

    def wikipedia(
        self,
        query: str
    ) -> str:
        try:
            search_url = (
                "https://en.wikipedia.org/w/api.php"
                "?action=opensearch"
                "&limit=1"
                "&namespace=0"
                "&format=json"
                "&search="
                + quote(
                    query
                )
            )

            search_response = self.session.get(
                search_url,
                timeout=12
            )

            search_data = search_response.json()

            titles = search_data[1]

            if not titles:
                return f"No Wikipedia page found for: {query}"

            title = titles[0]

            summary_url = (
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + quote(
                    title
                )
            )

            summary_response = self.session.get(
                summary_url,
                timeout=12
            )

            if summary_response.status_code >= 400:
                return (
                    f"Wikipedia page found: {title}\n"
                    "Could not read the summary endpoint."
                )

            data = summary_response.json()

            extract = data.get(
                "extract",
                ""
            )

            page_url = data.get(
                "content_urls",
                {}
            ).get(
                "desktop",
                {}
            ).get(
                "page",
                ""
            )

            return (
                f"Wikipedia page: {title}\n"
                f"URL: {page_url}\n\n"
                f"{extract}"
            )

        except Exception as e:
            return f"Could not read Wikipedia: {e}"