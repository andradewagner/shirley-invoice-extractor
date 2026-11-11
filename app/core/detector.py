import re
from enum import Enum


class DocumentFormat(str, Enum):
    PDF = "PDF"
    XML = "XML"


class UnsupportedDocumentFormat(ValueError):
    pass


class DocumentDetector:

    MAX_HEADER_SIZE = 4096

    @classmethod
    def detect(cls, header: bytes) -> DocumentFormat:

        if not isinstance(header, bytes):
            raise TypeError("O cabeçalho deve ser bytes")

        sample = header[:cls.MAX_HEADER_SIZE]

        if sample.startswith(b"%PDF-"):
            return DocumentFormat.PDF

        # Reconhecer BOM UTF-8 e espaços anteriores ao XML.
        sample = sample.removeprefix(b"\xef\xbb\xbf").lstrip()

        # Não permitir declarações DTD na detecção.
        if re.search(rb"<!DOCTYPE", sample, re.IGNORECASE):
            raise UnsupportedDocumentFormat(
                "Documentos XML com DTD não são permitidos"
            )

        # Declaração XML opcional.
        xml_declaration = re.match(
            rb"<\?xml\s+[^?]*\?>\s*",
            sample,
            re.IGNORECASE,
        )

        if xml_declaration:
            sample = sample[xml_declaration.end():]

        # Reconhecer elementos XML, com ou sem namespace.
        xml_root = re.match(
            rb"<(?:[A-Za-z_][\w.-]*:)?"
            rb"[A-Za-z_][\w.-]*"
            rb"(?:\s|>|/>)",
            sample,
        )

        if xml_root:
            return DocumentFormat.XML

        raise UnsupportedDocumentFormat(
            "Formato de documento não reconhecido"
        )
