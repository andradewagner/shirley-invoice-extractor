import subprocess
from pathlib import Path

import fitz


def text_from_pdf(path: Path) -> str:
    with fitz.open(path) as pdf:
        if pdf.page_count > 10:
            raise ValueError("PDF excede o limite de 10 páginas")

        if not any(page.get_text().strip() for page in pdf):
            raise ValueError("PDF digitalizado: OCR necessário")

    return subprocess.check_output(
        ["pdftotext", "-layout", str(path), "-"],
        text=True
    )
