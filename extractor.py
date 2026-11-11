import argparse
import json
import re
import subprocess
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import fitz

CNPJ = re.compile(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b')
MONEY = re.compile(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b')
DATE = re.compile(r'\b\d{2}/\d{2}/\d{4}\b')


def text_from_pdf(path: Path) -> str:
    with fitz.open(path) as pdf:
        if pdf.page_count > 10:
            raise ValueError("PDF excede o limite de 10 páginas")

        if not any(page.get_text().strip() for page in pdf):
            raise ValueError("PDF digitalizado: OCR necessário")

    return subprocess.check_output(
        ["pdftotext", "-layout", str(path), "-"],
        text=True
    )


def first_match(pattern, text):
    match = re.search(pattern, text, re.I | re.M)
    return match.group(1).strip() if match else None


def parse_nfse(text):
    number = first_match(
        r'Número da NFS-e[^\n]*\n\s*(\d+)\b',
        text
    )

    issue = first_match(
        r'Número da NFS-e[^\n]*Data e Hora da emissão da NFS-e'
        r'[^\n]*\n[^\n]*?(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}:\d{2}',
        text
    )

    section = (
        text.split("EMITENTE DA NFS-e", 1)[-1]
        .split("TOMADOR DO SERVIÇO", 1)[0]
    )

    cnpj_match = CNPJ.search(section)
    cnpj = cnpj_match.group() if cnpj_match else None

    name = None
    lines = section.splitlines()

    for i, line in enumerate(lines):
        if re.search(r'Nome\s*/\s*Nome Empresarial', line, re.I):
            if i + 1 < len(lines):
                name = re.split(
                    r'\s{2,}', lines[i + 1].strip()
                )[0].strip()
            break

    total_section = text.split("VALOR TOTAL DA NFS-E", 1)[-1]

    total_match = MONEY.search(total_section)
    total = total_match.group() if total_match else None

    return number, cnpj, name, issue, total


def parse_nfe(text):
    header = text.split("DESTINATÁRIO / REMETENTE", 1)[0]

    number = first_match(
        r'\bN[º°o]\s*\.?\s*([\d.]{3,})',
        header
    )

    if number:
        number = str(int(number.replace(".", "")))

    cnpjs = CNPJ.findall(header)
    cnpj = cnpjs[-1] if cnpjs else None

    name = first_match(
        r'^\s*(.+?)\s{2,}DANFE\b',
        header
    )

    if not name:
        name = first_match(
            r'RECEBEMOS DE\s+(.+?)\s+OS PRODUTOS',
            header
        )

    if not name:
        name = first_match(
            r'Recebemos de\s+(.+?)\s+os produtos',
            header
        )

    recipient = (
        text.split("DESTINATÁRIO / REMETENTE", 1)[-1]
        .split("CÁLCULO DO IMPOSTO", 1)[0]
    )

    issue = None
    lines = recipient.splitlines()

    for i, line in enumerate(lines):
        if "DATA DA EMISSÃO" in line.upper():
            for candidate in lines[i + 1:i + 3]:
                dates = DATE.findall(candidate)
                if dates:
                    issue = dates[-1]
                    break
            break

    tax = (
        text.split("CÁLCULO DO IMPOSTO", 1)[-1]
        .split("TRANSPORTADOR", 1)[0]
    )

    total = None
    lines = tax.splitlines()

    for i, line in enumerate(lines):
        if "VALOR TOTAL DA NOTA" in line.upper():
            for candidate in lines[i + 1:i + 3]:
                values = MONEY.findall(candidate)
                if values:
                    total = values[-1]
                    break
            break

    return number, cnpj, name, issue, total


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path, nargs="+")
    args = parser.parse_args()

    for pdf in args.pdf:
        try:
            print(json.dumps(
                {"file": pdf.name, **extract(pdf)},
                ensure_ascii=False,
                indent=2
            ))
        except Exception as error:
            print(json.dumps({
                "file": pdf.name,
                "error": str(error)
            }, ensure_ascii=False))
