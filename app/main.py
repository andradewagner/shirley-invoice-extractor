import os
import tempfile

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.detector import (
    DocumentDetector,
    DocumentFormat,
    UnsupportedDocumentFormat,
)
from app.parsers.xml.nfe import (
    FiscalXMLValidationError,
    parse_nfe_xml,
)
from extractor import extract


MAX_FILE_SIZE = 10 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


app = FastAPI(
    title="Shirley Invoice Extractor",
    description="Serviço independente de extração fiscal",
    version="1.3.0",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "shirley-invoice-extractor",
        "version": "1.3.0",
    }


@app.post("/v1/extract")
async def extract_invoice(file: UploadFile = File(...)):

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in (".pdf", ".xml"):
        raise HTTPException(
            status_code=400,
            detail="Somente arquivos PDF ou XML são permitidos",
        )

    temp_path = None

    try:
        total_size = 0
        header = bytearray()

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:

            temp_path = Path(temp_file.name)

            while chunk := await file.read(CHUNK_SIZE):

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Arquivo excede o limite de 10 MB",
                    )

                if len(header) < DocumentDetector.MAX_HEADER_SIZE:
                    remaining = (
                        DocumentDetector.MAX_HEADER_SIZE
                        - len(header)
                    )
                    header.extend(chunk[:remaining])

                temp_file.write(chunk)

        try:
            document_format = DocumentDetector.detect(
                bytes(header)
            )

        except UnsupportedDocumentFormat as error:
            detail = (
                "O arquivo enviado não é um PDF válido"
                if extension == ".pdf"
                else str(error)
            )

            raise HTTPException(
                status_code=400,
                detail=detail,
            ) from error

        # Impede divergência entre extensão e conteúdo.
        if (
            extension == ".pdf"
            and document_format != DocumentFormat.PDF
        ):
            raise HTTPException(
                status_code=400,
                detail="O arquivo enviado não é um PDF válido",
            )

        if (
            extension == ".xml"
            and document_format != DocumentFormat.XML
        ):
            raise HTTPException(
                status_code=400,
                detail="O arquivo enviado não é um XML reconhecido",
            )

        if document_format == DocumentFormat.PDF:

            result = await run_in_threadpool(
                extract,
                temp_path,
            )

        elif document_format == DocumentFormat.XML:

            result = await run_in_threadpool(
                parse_nfe_xml,
                temp_path,
            )

        else:
            raise HTTPException(
                status_code=415,
                detail="Formato não suportado",
            )

        return {
            "success": True,
            "data": result,
        }

    except (ValueError, FiscalXMLValidationError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar documento",
        )

    finally:

        await file.close()

        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
