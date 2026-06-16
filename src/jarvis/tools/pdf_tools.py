from jarvis.tools.base_tool import BaseTool
from jarvis.services.pdf_tools import PDFTools


class PDFToolsTool(BaseTool):

    name = "pdf_tools"

    def execute(
        self,
        action: str,
        path: str | None = None,
        folder: str | None = None
    ):

        pdf_tools = PDFTools()

        if action == "open_pdf_folder":
            return pdf_tools.open_pdf_folder()

        if action == "open_pdf_input_folder":
            return pdf_tools.open_pdf_input_folder()

        if action == "open_pdf_output_folder":
            return pdf_tools.open_pdf_output_folder()

        if action == "list_input_pdfs":
            return pdf_tools.list_input_pdfs()

        if action == "pdf_info":
            if not path:
                return "No PDF path was provided."

            return pdf_tools.get_pdf_info(
                path
            )

        if action == "extract_text":
            if not path:
                return "No PDF path was provided."

            return pdf_tools.extract_text(
                path
            )

        if action == "split_pdf":
            if not path:
                return "No PDF path was provided."

            return pdf_tools.split_pdf(
                path
            )

        if action == "merge_pdfs":
            return pdf_tools.merge_pdfs(
                folder
            )

        if action == "images_to_pdf":
            return pdf_tools.images_to_pdf(
                folder
            )

        return f"Unknown PDF action: {action}"