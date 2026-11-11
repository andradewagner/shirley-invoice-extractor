import tempfile
import unittest
from pathlib import Path

import pymupdf

from app.parsers.pdf.reader import text_from_pdf


class PDFReaderRegressionTests(unittest.TestCase):

    def test_synthetic_pdf_text_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"

            document = pymupdf.open()
            page = document.new_page()

            page.insert_text(
                (72, 72),
                "DOCUMENTO FISCAL SINTETICO",
                fontsize=12,
            )

            page.insert_text(
                (72, 100),
                "DANFE - TESTE AUTOMATIZADO",
                fontsize=12,
            )

            document.save(str(path))
            document.close()

            text = text_from_pdf(path)

            self.assertIn(
                "DOCUMENTO FISCAL SINTETICO",
                text,
            )

            self.assertIn(
                "DANFE - TESTE AUTOMATIZADO",
                text,
            )


if __name__ == "__main__":
    unittest.main()
