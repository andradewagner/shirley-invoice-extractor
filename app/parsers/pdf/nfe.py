import re

from app.parsers.common import CNPJ, DATE, MONEY, first_match


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

    # Validação final aplicada a qualquer origem do nome.
    if name:
        name = name.strip()

        if re.search(
            r'(?:https?://|www\.|\S+@\S+)',
            name,
            re.I
        ):
            name = None

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
