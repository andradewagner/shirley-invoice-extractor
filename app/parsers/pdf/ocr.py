import math
import subprocess

import pymupdf


MAX_PIXELS = 4_000_000
MAX_SCALE = 2.0


def ocr_page(page: pymupdf.Page, timeout: float) -> str:
    """Reconhece uma página PDF usando Tesseract, sem arquivos temporários."""

    if timeout <= 0:
        raise RuntimeError("Tempo limite do OCR excedido")

    area = page.rect.width * page.rect.height

    if area <= 0:
        raise ValueError("Página PDF com dimensões inválidas")

    scale = min(
        MAX_SCALE,
        math.sqrt(MAX_PIXELS / area),
    )

    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(scale, scale),
        colorspace=pymupdf.csRGB,
        alpha=False,
    )

    image = pixmap.tobytes("png")

    try:
        result = subprocess.run(
            [
                "tesseract",
                "stdin",
                "stdout",
                "-l",
                "por+eng",
            ],
            input=image,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=True,
        )

    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            "Tempo limite do Tesseract excedido"
        ) from error

    except FileNotFoundError as error:
        raise RuntimeError(
            "Tesseract não está instalado"
        ) from error

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Falha ao executar o Tesseract"
        ) from error

    return result.stdout.decode("utf-8", errors="replace")
