import os
import re
from datetime import datetime
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter


PDF_DIR = Path(
    "data/pdf"
)

PDF_INPUT_DIR = PDF_DIR / "input"
PDF_OUTPUT_DIR = PDF_DIR / "output"
PDF_TEXT_DIR = PDF_DIR / "text"


class PDFTools:

    def ensure_folders(
        self
    ):
        PDF_INPUT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        PDF_OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        PDF_TEXT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    def timestamp(
        self
    ) -> str:
        return datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

    def sanitize_filename(
        self,
        text: str
    ) -> str:
        text = str(text).lower().strip()

        text = re.sub(
            r"[^a-z0-9]+",
            "_",
            text
        )

        text = text.strip("_")

        if not text:
            text = "pdf_file"

        return text[:70]

    def resolve_path(
        self,
        path_text: str
    ) -> Path:
        path_text = str(path_text).strip()

        path_text = path_text.strip(
            "\"'"
        )

        path = Path(
            path_text
        ).expanduser()

        return path

    def validate_pdf(
        self,
        path_text: str
    ):
        path = self.resolve_path(
            path_text
        )

        if not path.exists():
            return None, f"PDF not found: {path}"

        if not path.is_file():
            return None, f"Path is not a file: {path}"

        if path.suffix.lower() != ".pdf":
            return None, f"File is not a PDF: {path}"

        return path, None

    def create_output_path(
        self,
        name: str,
        suffix: str,
        extension: str = ".pdf"
    ) -> Path:
        self.ensure_folders()

        filename = (
            f"{self.sanitize_filename(name)}_"
            f"{suffix}_"
            f"{self.timestamp()}"
            f"{extension}"
        )

        return PDF_OUTPUT_DIR / filename

    def open_pdf_folder(
        self
    ) -> str:
        try:
            self.ensure_folders()

            os.startfile(
                str(PDF_DIR.resolve())
            )

            return "Opening PDF folder."

        except Exception as e:
            return f"Failed to open PDF folder: {e}"

    def open_pdf_input_folder(
        self
    ) -> str:
        try:
            self.ensure_folders()

            os.startfile(
                str(PDF_INPUT_DIR.resolve())
            )

            return "Opening PDF input folder."

        except Exception as e:
            return f"Failed to open PDF input folder: {e}"

    def open_pdf_output_folder(
        self
    ) -> str:
        try:
            self.ensure_folders()

            os.startfile(
                str(PDF_OUTPUT_DIR.resolve())
            )

            return "Opening PDF output folder."

        except Exception as e:
            return f"Failed to open PDF output folder: {e}"

    def list_input_pdfs(
        self
    ) -> str:
        self.ensure_folders()

        pdfs = sorted(
            PDF_INPUT_DIR.glob(
                "*.pdf"
            )
        )

        if not pdfs:
            return (
                "No PDFs found in data/pdf/input. "
                "Put PDF files there first."
            )

        lines = [
            "PDFs in input folder:"
        ]

        for index, pdf in enumerate(
            pdfs,
            start=1
        ):
            lines.append(
                f"{index}. {pdf.name}"
            )

        return "\n".join(
            lines
        )

    def get_pdf_info(
        self,
        path_text: str
    ) -> str:
        path, error = self.validate_pdf(
            path_text
        )

        if error:
            return error

        try:
            reader = PdfReader(
                str(path)
            )

            metadata = reader.metadata or {}

            title = metadata.get(
                "/Title",
                ""
            )

            author = metadata.get(
                "/Author",
                ""
            )

            return (
                f"PDF info:\n"
                f"File: {path.name}\n"
                f"Path: {path}\n"
                f"Pages: {len(reader.pages)}\n"
                f"Title: {title or 'Not available'}\n"
                f"Author: {author or 'Not available'}"
            )

        except Exception as e:
            return f"Failed to read PDF info: {e}"

    def extract_text(
        self,
        path_text: str
    ) -> str:
        path, error = self.validate_pdf(
            path_text
        )

        if error:
            return error

        try:
            self.ensure_folders()

            reader = PdfReader(
                str(path)
            )

            output_lines = []

            for index, page in enumerate(
                reader.pages,
                start=1
            ):
                output_lines.append(
                    f"\n--- Page {index} ---\n"
                )

                text = page.extract_text() or ""

                if text.strip():
                    output_lines.append(
                        text.strip()
                    )
                else:
                    output_lines.append(
                        "[No selectable text found on this page]"
                    )

            output_path = PDF_TEXT_DIR / (
                f"{self.sanitize_filename(path.stem)}_"
                f"text_"
                f"{self.timestamp()}.txt"
            )

            output_path.write_text(
                "\n".join(output_lines),
                encoding="utf-8"
            )

            return f"PDF text extracted: {output_path}"

        except Exception as e:
            return f"Failed to extract text from PDF: {e}"

    def split_pdf(
        self,
        path_text: str
    ) -> str:
        path, error = self.validate_pdf(
            path_text
        )

        if error:
            return error

        try:
            self.ensure_folders()

            reader = PdfReader(
                str(path)
            )

            page_count = len(
                reader.pages
            )

            if page_count == 0:
                return "PDF has no pages."

            output_folder = PDF_OUTPUT_DIR / (
                f"{self.sanitize_filename(path.stem)}_"
                f"split_"
                f"{self.timestamp()}"
            )

            output_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            for index, page in enumerate(
                reader.pages,
                start=1
            ):
                writer = PdfWriter()
                writer.add_page(
                    page
                )

                output_path = output_folder / (
                    f"page_{index:03d}.pdf"
                )

                with open(
                    output_path,
                    "wb"
                ) as f:
                    writer.write(
                        f
                    )

            return (
                f"PDF split complete. "
                f"{page_count} pages saved to: {output_folder}"
            )

        except Exception as e:
            return f"Failed to split PDF: {e}"

    def get_pdfs_from_folder(
        self,
        folder_path: Path
    ) -> list[Path]:
        if not folder_path.exists():
            return []

        if not folder_path.is_dir():
            return []

        return sorted(
            folder_path.glob(
                "*.pdf"
            )
        )

    def merge_pdfs(
        self,
        folder_text: str | None = None
    ) -> str:
        try:
            self.ensure_folders()

            if folder_text:
                folder = self.resolve_path(
                    folder_text
                )
            else:
                folder = PDF_INPUT_DIR

            pdfs = self.get_pdfs_from_folder(
                folder
            )

            if len(pdfs) < 2:
                return (
                    f"Need at least 2 PDFs to merge in: {folder}"
                )

            writer = PdfWriter()

            total_pages = 0

            for pdf in pdfs:
                reader = PdfReader(
                    str(pdf)
                )

                for page in reader.pages:
                    writer.add_page(
                        page
                    )
                    total_pages += 1

            output_path = self.create_output_path(
                "merged_pdf",
                "merged"
            )

            with open(
                output_path,
                "wb"
            ) as f:
                writer.write(
                    f
                )

            return (
                f"Merged {len(pdfs)} PDFs "
                f"with {total_pages} pages: {output_path}"
            )

        except Exception as e:
            return f"Failed to merge PDFs: {e}"

    def images_to_pdf(
        self,
        folder_text: str | None = None
    ) -> str:
        try:
            self.ensure_folders()

            if folder_text:
                folder = self.resolve_path(
                    folder_text
                )
            else:
                folder = PDF_INPUT_DIR

            if not folder.exists() or not folder.is_dir():
                return f"Image folder not found: {folder}"

            image_extensions = [
                "*.png",
                "*.jpg",
                "*.jpeg",
                "*.webp",
                "*.bmp"
            ]

            image_paths = []

            for pattern in image_extensions:
                image_paths.extend(
                    folder.glob(
                        pattern
                    )
                )

            image_paths = sorted(
                image_paths
            )

            if not image_paths:
                return f"No images found in folder: {folder}"

            images = []

            for image_path in image_paths:
                image = Image.open(
                    image_path
                ).convert(
                    "RGB"
                )

                images.append(
                    image
                )

            output_path = self.create_output_path(
                "images",
                "converted"
            )

            first_image = images[0]
            remaining_images = images[1:]

            first_image.save(
                output_path,
                save_all=True,
                append_images=remaining_images
            )

            for image in images:
                image.close()

            return (
                f"Converted {len(image_paths)} images "
                f"to PDF: {output_path}"
            )

        except Exception as e:
            return f"Failed to convert images to PDF: {e}"