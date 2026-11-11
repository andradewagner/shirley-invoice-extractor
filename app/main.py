import os
import tempfile

from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from starlette.concurrency import run_in_threadpool

from extractor import extract


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


app = FastAPI(
    title="Shirley Invoice Extractor",
    description="Serviço de extração fiscal do Shirley EcoSystem",
    version="1.0.0"
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "shirley-invoice-extractor",
        "version": "1.0.0"
    }


@app.post("/v1/extract")
async def extract_invoice(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Somente arquivos PDF são permitidos"
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        ) as temp_file:

            temp_path = Path(temp_file.name)

            total_size = 0
            header = b""

            while chunk := await file.read(1024 * 1024):

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Arquivo excede o limite de 10 MB"
                    )

                if len(header) < 5:
                    header += chunk[:5 - len(header)]

                temp_file.write(chunk)

        if not header.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="O arquivo enviado não é um PDF válido"
            )

        result = await run_in_threadpool(
            extract,
            temp_path
        )

        return {
            "success": True,
            "data": result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar documento"
        )

    finally:

        await file.close()

        if temp_path and temp_path.exists():
            os.unlink(temp_path)