import subprocess
import time
from pathlib import Path

import pymupdf

from app.parsers.pdf.ocr import ocr_page


MAX_PAGES = 10
MAX_PROCESSING_SECONDS = 45
MIN_TEXT_LENGTH = 30


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()

    if remaining <= 0:
        raise RuntimeError(
            "Tempo limite de processamento do PDF excedido"
        )

    return remaining


def _poppler_text(
    path: Path,
    deadline: float,
    page_number: int | None = None,
) -> str:
    command = ["pdftotext"]

    if page_number is not None:
        command.extend([
            "-f", str(page_number),
            "-l", str(page_number),
        ])

    command.extend([
        "-layout",
        str(path),
        "-",
    ])

    try:
        return subprocess.check_output(
            command,
            text=True,
            timeout=_remaining(deadline),
        )

    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            "Tempo limite do Poppler excedido"
        ) from error

    except FileNotFoundError as error:
        raise RuntimeError(
            "Poppler não está instalado"
        ) from error

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Falha ao extrair texto do PDF"
        ) from error


def text_from_pdf(path: Path) -> str:
    deadline = time.monotonic() + MAX_PROCESSING_SECONDS

    with pymupdf.open(path) as pdf:
        if pdf.page_count == 0:
            raise ValueError("PDF sem páginas")

        if pdf.page_count > MAX_PAGES:
            raise ValueError(
                f"PDF excede o limite de {MAX_PAGES} páginas"
            )

        needs_ocr = []

        for page in pdf:
            text = page.get_text().strip()

            scanned = (
                not text
                or (
                    len(text) < MIN_TEXT_LENGTH
                    and bool(page.get_images())
                )
            )

            needs_ocr.append(scanned)

        # Caminho original: PDF inteiramente digital.
        if not any(needs_ocr):
            return _poppler_text(path, deadline)

        # PDF digitalizado ou misto.
        parts = []

        for index, page in enumerate(pdf):
            if needs_ocr[index]:
                text = ocr_page(
                    page,
                    _remaining(deadline),
                )
            else:
                text = _poppler_text(
                    path,
                    deadline,
                    page_number=index + 1,
                )

            parts.append(text)

        combined = "\n\f\n".join(parts)

        if not combined.strip():
            raise ValueError(
                "Nenhum texto reconhecível no PDF"
            )

        return combined
