import unittest

from app.core.detector import (
    DocumentDetector,
    DocumentFormat,
    UnsupportedDocumentFormat,
)


class DocumentDetectorTests(unittest.TestCase):

    def test_pdf(self):
        header = b"%PDF-1.7\n"

        result = DocumentDetector.detect(header)

        self.assertEqual(result, DocumentFormat.PDF)

    def test_xml_with_declaration(self):
        header = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b"<NFe></NFe>"
        )

        result = DocumentDetector.detect(header)

        self.assertEqual(result, DocumentFormat.XML)

    def test_xml_without_declaration(self):
        result = DocumentDetector.detect(
            b"<NFe></NFe>"
        )

        self.assertEqual(result, DocumentFormat.XML)

    def test_xml_with_namespace(self):
        result = DocumentDetector.detect(
            b"<nfe:NFe xmlns:nfe='http://example.com'></nfe:NFe>"
        )

        self.assertEqual(result, DocumentFormat.XML)

    def test_xml_with_bom(self):
        result = DocumentDetector.detect(
            b"\xef\xbb\xbf  <NFe></NFe>"
        )

        self.assertEqual(result, DocumentFormat.XML)

    def test_invalid_document(self):
        with self.assertRaises(
            UnsupportedDocumentFormat
        ):
            DocumentDetector.detect(
                b"Arquivo sem formato reconhecido"
            )

    def test_empty_document(self):
        with self.assertRaises(
            UnsupportedDocumentFormat
        ):
            DocumentDetector.detect(b"")

    def test_xml_with_dtd_rejected(self):
        with self.assertRaises(
            UnsupportedDocumentFormat
        ):
            DocumentDetector.detect(
                b'<!DOCTYPE NFe SYSTEM "external.dtd"><NFe/>'
            )


if __name__ == "__main__":
    unittest.main()
