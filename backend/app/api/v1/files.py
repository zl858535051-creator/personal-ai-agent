from fastapi import APIRouter, UploadFile

from app.api.deps import DbSession
from app.schemas.document import DocumentRead
from app.services.file_service import FileService

router = APIRouter()


@router.post("/upload", response_model=DocumentRead)
async def upload_file(file: UploadFile, db: DbSession) -> DocumentRead:
    return await FileService(db).upload_and_index(file)


@router.get("", response_model=list[DocumentRead])
def list_files(db: DbSession) -> list[DocumentRead]:
    return FileService(db).list_documents()


@router.delete("/{file_id}")
def delete_file(file_id: int, db: DbSession) -> dict[str, str]:
    FileService(db).delete_document(file_id)
    return {"status": "deleted"}

