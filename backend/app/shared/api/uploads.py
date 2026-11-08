"""Lectura de archivos CSV subidos por el cliente (frontera de confianza) y descarga de plantillas."""
import codecs

from fastapi import Response, UploadFile

from app.core.exceptions import UnprocessableError

MAX_CSV_BYTES = 5 * 1024 * 1024


async def read_csv_upload(file: UploadFile) -> str:
    raw = await file.read(MAX_CSV_BYTES + 1)
    if len(raw) > MAX_CSV_BYTES:
        raise UnprocessableError("El archivo supera el límite de 5 MB")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Excel guarda en Windows-1252 si no se elige «CSV UTF-8»: sin esto, ñ y tildes se dañan.
        return raw.decode("cp1252", errors="replace")


def csv_template_response(content: str, filename: str) -> Response:
    # El BOM hace que Excel en español abra el UTF-8 con tildes bien; ';' es su separador por defecto.
    return Response(
        content=codecs.BOM_UTF8 + content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
