from pathlib import Path

from pypdf import PdfWriter

from jarvis.services.pdf_tools import PDFTools
from jarvis.services.pdf_tools import PDF_INPUT_DIR


def create_sample_pdf(
    path: Path,
    page_count: int
):
    writer = PdfWriter()

    for _ in range(
        page_count
    ):
        writer.add_blank_page(
            width=595,
            height=842
        )

    with open(
        path,
        "wb"
    ) as f:
        writer.write(
            f
        )


def main():
    pdf_tools = PDFTools()
    pdf_tools.ensure_folders()

    sample_1 = PDF_INPUT_DIR / "sample_one.pdf"
    sample_2 = PDF_INPUT_DIR / "sample_two.pdf"

    create_sample_pdf(
        sample_1,
        2
    )

    create_sample_pdf(
        sample_2,
        3
    )

    print("=" * 50)
    print("Jarvis PDF Tools Test")
    print("=" * 50)

    print(
        pdf_tools.list_input_pdfs()
    )

    print(
        pdf_tools.get_pdf_info(
            str(sample_1)
        )
    )

    print(
        pdf_tools.extract_text(
            str(sample_1)
        )
    )

    print(
        pdf_tools.split_pdf(
            str(sample_1)
        ) 
    )

    print(
        pdf_tools.merge_pdfs()
    )

    print(
        pdf_tools.open_pdf_output_folder()
    )


if __name__ == "__main__":
    main()