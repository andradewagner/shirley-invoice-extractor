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

    total = None

    lines = text.splitlines()

    for index, line in enumerate(lines):
        label = re.search(
            r'VALOR TOTAL DA NFS-E',
            line,
            re.I
        )

        if not label:
            continue

        # Primeiro verifica se o valor está na mesma linha.
        remainder = line[label.end():].strip()

        if remainder:
            match = re.fullmatch(
                r'(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})',
                remainder
            )

            if match:
                total = match.group(1)

        # Se o título estiver sozinho, verifica a linha seguinte.
        elif index + 1 < len(lines):
            candidate = lines[index + 1].strip()

            match = re.fullmatch(
                r'(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})',
                candidate
            )

            if match:
                total = match.group(1)

        break

    return number, cnpj, name, issue, total
