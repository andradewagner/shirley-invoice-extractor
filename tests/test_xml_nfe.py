import tempfile
import unittest
from pathlib import Path

from app.parsers.xml.nfe import (
    FiscalXMLValidationError,
    parse_nfe_xml,
)


NAMESPACE = "http://www.portalfiscal.inf.br/nfe"

XML_NFE = f"""<?xml version="1.0" encoding="UTF-8"?>
<NFe xmlns="{NAMESPACE}">
  <infNFe Id="NFe{'1' * 44}" versao="4.00">
    <ide>
      <mod>55</mod>
      <serie>1</serie>
      <nNF>56</nNF>
      <dhEmi>2019-10-22T10:30:00-03:00</dhEmi>
      <finNFe>1</finNFe>
    </ide>
    <emit>
      <CNPJ>14356429000120</CNPJ>
      <xNome>EMPRESA EXEMPLO LTDA</xNome>
    </emit>
    <total>
      <ICMSTot>
        <vNF>150.00</vNF>
      </ICMSTot>
    </total>
  </infNFe>
</NFe>
"""


class NFEXMLTests(unittest.TestCase):

    def parse_content(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "documento.xml"
            path.write_bytes(content.encode("utf-8"))
            return parse_nfe_xml(path)

    def test_document_type(self):
        result = self.parse_content(XML_NFE)
        self.assertEqual(result["document_type"], "NFE")
        self.assertEqual(result["document_model"], "55")

    def test_invoice_fields(self):
        result = self.parse_content(XML_NFE)

        self.assertEqual(result["invoice_number"], "56")
        self.assertEqual(result["series"], "1")
        self.assertEqual(
            result["issuer_cnpj"],
            "14356429000120"
        )
        self.assertEqual(
            result["issuer_name"],
            "EMPRESA EXEMPLO LTDA"
        )
        self.assertEqual(result["issue_date"], "2019-10-22")
        self.assertEqual(result["total_amount"], "150.00")

    def test_access_key(self):
        result = self.parse_content(XML_NFE)
        self.assertEqual(result["access_key"], "1" * 44)

    def test_fiscal_status_is_not_assumed(self):
        result = self.parse_content(XML_NFE)

        self.assertEqual(result["fiscal_status"], "UNKNOWN")
        self.assertTrue(result["requires_review"])

    def test_nfeproc_envelope(self):
        content = (
            f'<nfeProc xmlns="{NAMESPACE}">'
            + XML_NFE.split("?>", 1)[1]
            + "</nfeProc>"
        )

        result = self.parse_content(content)

        self.assertEqual(result["document_type"], "NFE")

    def test_reject_nfce_model(self):
        content = XML_NFE.replace(
            "<mod>55</mod>",
            "<mod>65</mod>"
        )

        with self.assertRaises(FiscalXMLValidationError):
            self.parse_content(content)

    def test_reject_external_entity(self):
        content = """<?xml version="1.0"?>
<!DOCTYPE NFe [
  <!ENTITY secret SYSTEM "file:///etc/passwd">
]>
<NFe>&secret;</NFe>
"""

        with self.assertRaises(FiscalXMLValidationError):
            self.parse_content(content)

    def test_reject_invalid_xml(self):
        with self.assertRaises(FiscalXMLValidationError):
            self.parse_content("<NFe><infNFe></NFe>")

    def test_reject_invalid_amount(self):
        content = XML_NFE.replace(
            "<vNF>150.00</vNF>",
            "<vNF>ABC</vNF>"
        )

        with self.assertRaises(FiscalXMLValidationError):
            self.parse_content(content)


if __name__ == "__main__":
    unittest.main()
