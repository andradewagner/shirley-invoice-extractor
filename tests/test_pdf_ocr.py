import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf

from app.parsers.pdf.reader import text_from_pdf


class PDFOcrTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)

    def create_pdf(self, name, scanned=False, mixed=False):
        path = self.folder / name

        source = pymupdf.open()
        page = source.new_page()

        page.insert_text(
            (72, 110),
            "DANFE",
            fontsize=30,
        )

        page.insert_text(
            (72, 170),
            "NOTA FISCAL TESTE",
            fontsize=22,
        )

        if scanned:
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2)
            )

            image = pixmap.tobytes("png")

            target = pymupdf.open()

            if mixed:
                first = target.new_page()
                first.insert_text(
                    (72, 100),
                    "PAGINA DIGITAL DE TESTE",
                    fontsize=16,
                )

            scanned_page = target.new_page()
            scanned_page.insert_image(
                scanned_page.rect,
                stream=image,
            )

            target.save(str(path))
            target.close()

        else:
            source.save(str(path))

        source.close()

        return path

    def test_pdf_digital_usa_poppler(self):
        path = self.create_pdf("digital.pdf")

        with patch(
            "app.parsers.pdf.reader.ocr_page"
        ) as mock_ocr:
            text = text_from_pdf(path)

        self.assertIn("DANFE", text)
        mock_ocr.assert_not_called()

    @unittest.skipUnless(
        shutil.which("tesseract"),
        "Tesseract não instalado",
    )
    def test_pdf_digitalizado_usa_ocr_real(self):
        path = self.create_pdf(
            "digitalizado.pdf",
            scanned=True,
        )

        text = text_from_pdf(path)

        self.assertIn("DANFE", text.upper())

    @unittest.skipUnless(
        shutil.which("tesseract"),
        "Tesseract não instalado",
    )
    def test_pdf_misto_preserva_texto_digital_e_ocr(self):
        path = self.create_pdf(
            "misto.pdf",
            scanned=True,
            mixed=True,
        )

        text = text_from_pdf(path)

        self.assertIn(
            "PAGINA DIGITAL DE TESTE",
            text.upper(),
        )

        self.assertIn("DANFE", text.upper())

    def test_erro_do_ocr_nao_e_ocultado(self):
        path = self.create_pdf(
            "falha.pdf",
            scanned=True,
        )

        with patch(
            "app.parsers.pdf.reader.ocr_page",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Falha simulada",
            ):
                text_from_pdf(path)


if __name__ == "__main__":
    unittest.main()
