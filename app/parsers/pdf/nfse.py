import re

from app.parsers.common import CNPJ, MONEY, first_match


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
