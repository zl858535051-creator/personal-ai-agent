from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.api.deps import DbSession
from app.schemas.report import ReportCreate, ReportRead
from app.services.report_service import ReportService

router = APIRouter()


@router.post("", response_model=ReportRead)
def create_report(request: ReportCreate, db: DbSession) -> ReportRead:
    return ReportService(db).create_report(request)


@router.get("", response_model=list[ReportRead])
def list_reports(db: DbSession) -> list[ReportRead]:
    return ReportService(db).list_reports()


@router.get("/{report_id}/download")
def download_report(report_id: int, db: DbSession) -> FileResponse:
    report = ReportService(db).get_report(report_id)
    return FileResponse(path=report.file_path, filename=report.filename)

