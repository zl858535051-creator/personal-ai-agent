from datetime import datetime
from pathlib import Path
from re import sub

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.task import Report
from app.schemas.report import ReportCreate


class ReportService:
    """Creates Markdown and PDF report artifacts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_report(self, request: ReportCreate) -> Report:
        fmt = request.format.lower()
        if fmt not in {"markdown", "md", "pdf"}:
            raise AppError("Report format must be markdown or pdf.")

        slug = sub(r"[^a-zA-Z0-9_-]+", "-", request.title).strip("-").lower() or "report"
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        if fmt == "pdf":
            path = settings.absolute_report_dir / f"{slug}-{timestamp}.pdf"
            self._write_pdf(path, request.title, request.content)
            report_format = "pdf"
        else:
            path = settings.absolute_report_dir / f"{slug}-{timestamp}.md"
            path.write_text(f"# {request.title}\n\n{request.content}\n", encoding="utf-8")
            report_format = "markdown"

        report = Report(title=request.title, filename=path.name, file_path=str(path), format=report_format)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def list_reports(self) -> list[Report]:
        return self.db.query(Report).order_by(Report.created_at.desc()).all()

    def get_report(self, report_id: int) -> Report:
        report = self.db.get(Report, report_id)
        if report is None or not Path(report.file_path).exists():
            raise AppError("Report not found", 404)
        return report

    def _write_pdf(self, path: Path, title: str, content: str) -> None:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise AppError("reportlab is required to generate PDF reports.") from exc

        pdf = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4
        font_name = "Helvetica"
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            font_name = "STSong-Light"
        except Exception:
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
                font_name = "DejaVuSans"
            except Exception:
                pass

        y = height - 50
        pdf.setFont(font_name, 16)
        pdf.drawString(50, y, title[:80])
        y -= 32
        pdf.setFont(font_name, 10)
        for line in content.splitlines():
            for part in _wrap(line, 95):
                if y < 50:
                    pdf.showPage()
                    pdf.setFont(font_name, 10)
                    y = height - 50
                pdf.drawString(50, y, part)
                y -= 16
        pdf.save()


def _wrap(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + width] for index in range(0, len(text), width)]
