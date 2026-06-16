from jarvis.tools.base_tool import BaseTool
from jarvis.services.document_maker import DocumentMaker


class DocumentMakerTool(BaseTool):

    name = "document_maker"

    def execute(
        self,
        action: str,
        topic: str | None = None,
        doc_type: str = "professional"
    ):

        document_maker = DocumentMaker()

        if action == "create_document":
            if not topic:
                return "No document topic was provided."

            return document_maker.create_document(
                topic=topic,
                doc_type=doc_type
            )

        if action == "open_document_folder":
            return document_maker.open_document_folder()

        return f"Unknown document action: {action}"