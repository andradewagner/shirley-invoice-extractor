import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.parsers.pdf.reader import text_from_pdf
from app.parsers.pdf.nfe import parse_nfe
from app.parsers.pdf.nfse import parse_nfse


def extract(path: Path):
    text = text_from_pdf(path)

    if re.search(r'DANFSe|Número da NFS-e', text, re.I):
        document_type = "NFSE"
        fields = parse_nfse(text)

    elif re.search(r'\bDANFE\b', text, re.I):
        document_type = "NFE"
        fields = parse_nfe(text)

    else:
        raise ValueError("Layout fiscal não reconhecido")

    number, cnpj, name, date, amount = fields

    warnings = []

    if re.search(
        r'HOMOLOGACAO|HOMOLOGAÇÃO|SEM VALOR FISCAL',
        text,
        re.I
    ):
        warnings.append(
            "Documento de homologação ou sem valor fiscal"
        )

    result = {
        "document_type": document_type,
        "invoice_number": number,
        "issuer_cnpj": cnpj,
        "issuer_name": name,
        "issue_date": (
            datetime.strptime(date, "%d/%m/%Y")
            .date().isoformat()
            if date else None
        ),
        "total_amount": (
            str(Decimal(
                amount.replace(".", "").replace(",", ".")
            ))
            if amount else None
        ),
        "requires_review": True,
        "warnings": warnings
    }

    required = [
        "invoice_number",
        "issuer_cnpj",
        "issuer_name",
        "issue_date",
        "total_amount"
    ]

    missing = [field for field in required if not result[field]]

    if missing:
        result["warnings"].append(
            "Campos não extraídos: " + ", ".join(missing)
        )

    return result
