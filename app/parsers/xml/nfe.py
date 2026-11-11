from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET

from defusedxml import ElementTree as SafeET
from defusedxml.common import DefusedXmlException


NFE_NAMESPACE = "http://www.portalfiscal.inf.br/nfe"
MAX_XML_SIZE = 10 * 1024 * 1024
MAX_XML_ELEMENTS = 100_000


class FiscalXMLValidationError(ValueError):
    """XML fiscal inválido ou não suportado."""


def _tag(name: str) -> str:
    return f"{{{NFE_NAMESPACE}}}{name}"


def _child(parent, name):
    if parent is None:
        return None

    for tag in (_tag(name), name):
        element = parent.find(tag)

        if element is not None:
            return element

    return None


def _text(parent, name):
    element = _child(parent, name)

    if element is None or element.text is None:
        return None

    return element.text.strip() or None


def _date(value):
    if not value:
        return None

    try:
        if "T" in value:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).date().isoformat()

        return date.fromisoformat(value).isoformat()

    except ValueError as error:
        raise FiscalXMLValidationError(
            "Data de emissão inválida"
        ) from error


def _amount(value):
    if not value:
        return None

    try:
        amount = Decimal(value)

        if not amount.is_finite() or amount < 0:
            raise InvalidOperation

        return str(amount.quantize(Decimal("0.01")))

    except (InvalidOperation, ValueError) as error:
        raise FiscalXMLValidationError(
            "Valor total da NF-e inválido"
        ) from error


def parse_nfe_xml(path: Path) -> dict:
    path = Path(path)

    if path.stat().st_size > MAX_XML_SIZE:
        raise FiscalXMLValidationError(
            "XML excede o limite de 10 MB"
        )

    try:
        content = path.read_bytes()
        root = SafeET.fromstring(content)

    except (ET.ParseError, DefusedXmlException) as error:
        raise FiscalXMLValidationError(
            "XML inválido ou contém construções proibidas"
        ) from error

    if sum(1 for _ in root.iter()) > MAX_XML_ELEMENTS:
        raise FiscalXMLValidationError(
            "XML excede o limite de elementos"
        )

    # Aceitar NFe e nfeProc.
    if root.tag in (_tag("NFe"), "NFe"):
        nfe = root

    elif root.tag in (_tag("nfeProc"), "nfeProc"):
        nfe = _child(root, "NFe")

    else:
        raise FiscalXMLValidationError(
            "Documento não é uma NF-e"
        )

    if nfe is None:
        raise FiscalXMLValidationError(
            "Elemento NFe não encontrado"
        )

    info = _child(nfe, "infNFe")

    if info is None:
        raise FiscalXMLValidationError(
            "Elemento infNFe não encontrado"
        )

    ide = _child(info, "ide")
    emit = _child(info, "emit")
    total = _child(info, "total")
    icms_total = _child(total, "ICMSTot")

    model = _text(ide, "mod")

    if model != "55":
        raise FiscalXMLValidationError(
            f"Modelo fiscal não suportado: {model}"
        )

    invoice_number = _text(ide, "nNF")
    series = _text(ide, "serie")
    issuer_cnpj = _text(emit, "CNPJ")
    issuer_name = _text(emit, "xNome")

    issue_date = _date(
        _text(ide, "dhEmi") or _text(ide, "dEmi")
    )

    total_amount = _amount(
        _text(icms_total, "vNF")
    )

    access_id = info.get("Id")
    access_key = None

    if access_id and access_id.startswith("NFe"):
        candidate = access_id[3:]

        if len(candidate) == 44 and candidate.isdigit():
            access_key = candidate

    required_fields = {
        "invoice_number": invoice_number,
        "issuer_cnpj": issuer_cnpj,
        "issuer_name": issuer_name,
        "issue_date": issue_date,
        "total_amount": total_amount,
    }

    missing = [
        field
        for field, value in required_fields.items()
        if not value
    ]

    warnings = []

    if missing:
        warnings.append(
            "Campos não extraídos: " + ", ".join(missing)
        )

    if not access_key:
        warnings.append(
            "Chave de acesso não identificada"
        )

    return {
        "document_type": "NFE",
        "document_model": model,
        "source_format": "XML",
        "invoice_number": invoice_number,
        "series": series,
        "access_key": access_key,
        "issuer_cnpj": issuer_cnpj,
        "issuer_name": issuer_name,
        "issue_date": issue_date,
        "total_amount": total_amount,
        "operation_type": _text(ide, "finNFe"),
        "fiscal_status": "UNKNOWN",
        "requires_review": True,
        "warnings": warnings,
    }
