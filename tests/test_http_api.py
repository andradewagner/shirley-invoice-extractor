import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


NFE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
  <infNFe versao="4.00">
    <ide>
      <mod>55</mod>
      <serie>1</serie>
      <nNF>123</nNF>
      <dhEmi>2026-11-11T10:30:00-03:00</dhEmi>
      <finNFe>1</finNFe>
    </ide>
    <emit>
      <CNPJ>00000000000100</CNPJ>
      <xNome>EMPRESA TESTE LTDA</xNome>
    </emit>
    <total>
      <ICMSTot>
        <vNF>250.75</vNF>
      </ICMSTot>
    </total>
  </infNFe>
</NFe>
"""


PDF_RESULT = {
    "document_type": "NFE",
    "invoice_number": "56",
    "issuer_cnpj": "14356429000120",
    "issuer_name": "EMPRESA TESTE LTDA",
    "issue_date": "2019-10-22",
    "total_amount": "150.00",
    "requires_review": True,
    "warnings": [],
}


class ExtractorHTTPTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def upload(self, content, filename):
        return self.client.post(
            "/v1/extract",
            files={
                "file": (
                    filename,
                    io.BytesIO(content),
                    "application/octet-stream",
                )
            },
        )

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["service"],
            "shirley-invoice-extractor",
        )

    def test_extract_nfe_xml(self):
        response = self.upload(
            NFE_XML,
            "documento.xml",
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"]["document_type"],
            "NFE",
        )
        self.assertEqual(
            result["data"]["document_model"],
            "55",
        )
        self.assertEqual(
            result["data"]["invoice_number"],
            "123",
        )
        self.assertEqual(
            result["data"]["total_amount"],
            "250.75",
        )

    def test_extract_pdf(self):
        with patch(
            "app.main.extract",
            return_value=PDF_RESULT,
        ) as mock_extract:

            response = self.upload(
                b"%PDF-1.7\nPDF sintetico",
                "documento.pdf",
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_extract.called)
        self.assertEqual(
            response.json()["data"],
            PDF_RESULT,
        )

    def test_invalid_pdf(self):
        response = self.upload(
            b"Documento invalido",
            "documento.pdf",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "O arquivo enviado não é um PDF válido",
        )

    def test_invalid_xml(self):
        response = self.upload(
            b"<NFe><infNFe></NFe>",
            "documento.xml",
        )

        self.assertEqual(response.status_code, 422)

    def test_xml_external_entity(self):
        xml = b"""<?xml version="1.0"?>
<!DOCTYPE NFe [
  <!ENTITY secret SYSTEM "file:///etc/passwd">
]>
<NFe>&secret;</NFe>
"""

        response = self.upload(
            xml,
            "documento.xml",
        )

        self.assertEqual(response.status_code, 400)

    def test_unsupported_fiscal_model(self):
        xml = NFE_XML.replace(
            b"<mod>55</mod>",
            b"<mod>65</mod>",
        )

        response = self.upload(
            xml,
            "documento.xml",
        )

        self.assertEqual(response.status_code, 422)

    def test_file_size_limit(self):
        content = (
            b"%PDF-"
            + b"0" * (11 * 1024 * 1024)
        )

        response = self.upload(
            content,
            "documento.pdf",
        )

        self.assertEqual(response.status_code, 413)

    def test_unsupported_extension(self):
        response = self.upload(
            b"conteudo de teste",
            "documento.txt",
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
