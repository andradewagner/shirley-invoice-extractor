import unittest
from pathlib import Path

from extractor import extract


class ExtractorRegressionTests(unittest.TestCase):

    def test_extract_nfe(self):
        fixture = Path("tests/fixtures/nfe.pdf")

        if not fixture.exists():
            self.skipTest("Fixture NF-e não disponível")

        result = extract(fixture)

        self.assertEqual(result["document_type"], "NFE")
        self.assertEqual(result["invoice_number"], "56")
        self.assertEqual(result["total_amount"], "150.00")
        self.assertTrue(result["requires_review"])


if __name__ == "__main__":
    unittest.main()
