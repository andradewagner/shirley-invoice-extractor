import re

CNPJ = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
MONEY = re.compile(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b")
DATE = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")


def first_match(pattern, text):
    match = re.search(pattern, text, re.I | re.M)
    return match.group(1).strip() if match else None
