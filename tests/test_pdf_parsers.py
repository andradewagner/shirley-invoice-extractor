import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.engine import extract


NFE_TEXT = """
EMPRESA EXEMPLO LTDA          DANFE
Nº 000.000.056
14.356.429/0001-20

DESTINATÁRIO / REMETENTE
DATA DA EMISSÃO
22/10/2019

CÁLCULO DO IMPOSTO
VALOR TOTAL DA NOTA
150,00

TRANSPORTADOR
"""


NFSE_TEXT = """
DANFSe
Número da NFS-e    Data e Hora da emissão da NFS-e
56    22/10/2019 11:22:33

EMITENTE DA NFS-e
Nome / Nome Empresarial
EMPRESA EXEMPLO LTDA
14.356.429/0001-20

TOMADOR DO SERVIÇO

VALOR TOTAL DA NFS-E
150,00
"""


class FiscalExtractionTests(unittest.TestCase):

    def extract_text(self, text):
        with patch(
            "app.core.engine.text_from_pdf",
            return_value=text
        ):
            return extract(Path("/tmp/documento-sintetico.pdf"))

    def test_nfe_identification(self):
        result = self.extract_text(NFE_TEXT)

        self.assertEqual(
            result["document_type"],
            "NFE"
        )

    def test_nfe_fields(self):
        result = self.extract_text(NFE_TEXT)

        self.assertEqual(result["invoice_number"], "56")
        self.assertEqual(
            result["issuer_cnpj"],
            "14.356.429/0001-20"
        )
        self.assertEqual(
            result["issuer_name"],
            "EMPRESA EXEMPLO LTDA"
        )
        self.assertEqual(
            result["issue_date"],
            "2019-10-22"
        )
        self.assertEqual(
            result["total_amount"],
            "150.00"
        )

    def test_nfse_identification(self):
        result = self.extract_text(NFSE_TEXT)

        self.assertEqual(
            result["document_type"],
            "NFSE"
        )

    def test_nfse_fields(self):
        result = self.extract_text(NFSE_TEXT)

        self.assertEqual(
            result["invoice_number"],
            "56"
        )
        self.assertEqual(
            result["issuer_cnpj"],
            "14.356.429/0001-20"
        )
        self.assertEqual(
            result["issuer_name"],
            "EMPRESA EXEMPLO LTDA"
        )
        self.assertEqual(
            result["issue_date"],
            "2019-10-22"
        )
        self.assertEqual(
            result["total_amount"],
            "150.00"
        )

    def test_unknown_layout(self):
        with self.assertRaisesRegex(
            ValueError,
            "Layout fiscal não reconhecido"
        ):
            self.extract_text(
                "Documento comercial sem identificação fiscal"
            )

    def test_homologation_warning(self):
        result = self.extract_text(
            NFE_TEXT + "\nSEM VALOR FISCAL"
        )

        self.assertTrue(result["requires_review"])
        self.assertTrue(
            any(
                "homologação" in warning.lower()
                for warning in result["warnings"]
            )
        )

    def test_nfe_nao_usa_website_como_emitente(self):
        text = NFE_TEXT.replace(
            "EMPRESA EXEMPLO LTDA          DANFE",
            "www.exemplo.com.br          DANFE"
        )

        result = self.extract_text(text)

        self.assertIsNone(result["issuer_name"])
        self.assertTrue(result["requires_review"])

    def test_nfse_nao_confunde_imposto_com_total(self):
        text = NFSE_TEXT.replace(
            "VALOR TOTAL DA NFS-E\n150,00",
            "VALOR TOTAL DA NFS-E\n"
            "INFORMAÇÕES TRIBUTÁRIAS\n"
            "ISS RETIDO: 0,00\n"
            "VALOR LÍQUIDO: 150,00"
        )

        result = self.extract_text(text)

        self.assertIsNone(result["total_amount"])
        self.assertTrue(result["requires_review"])

    def test_nfse_preserva_valor_zero_explicito(self):
        text = NFSE_TEXT.replace(
            "VALOR TOTAL DA NFS-E\n150,00",
            "VALOR TOTAL DA NFS-E\n0,00"
        )

        result = self.extract_text(text)

        self.assertEqual(result["total_amount"], "0.00")


if __name__ == "__main__":
    unittest.main()
