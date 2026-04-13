from __future__ import annotations

import mimetypes
from pathlib import Path

import fitz
from fastapi import UploadFile
from sqlalchemy.orm import Session

from docustruct_ai.models import Document, Job, Page
from docustruct_ai.storage.base import ArtifactStorage


class IngestionService:
    def __init__(self, storage: ArtifactStorage) -> None:
        self.storage = storage

    def create_document(
        self,
        db: Session,
        file: UploadFile,
        document_type: str,
        external_id: str | None = None,
    ) -> tuple[Document, Job]:
        content = file.file.read()
        mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
        doc = Document(
            external_id=external_id,
            document_type=document_type,
            filename=file.filename or "uploaded.bin",
            mime_type=mime_type,
            source_path="",
            status="uploaded",
            routing_state="needs_review",
            metadata_json={"size_bytes": len(content)},
        )
        db.add(doc)
        db.flush()

        original_path = self.storage.save_bytes(f"{doc.id}/original/{doc.filename}", content)
        doc.source_path = original_path

        pages = self._materialize_pages(doc.id, original_path, mime_type)
        for page in pages:
            db.add(page)

        job = Job(document_id=doc.id, job_type="document_pipeline", status="queued")
        db.add(job)
        db.commit()
        db.refresh(doc)
        db.refresh(job)
        return doc, job

    def _materialize_pages(self, document_id: str, source_path: str, mime_type: str) -> list[Page]:
        pages: list[Page] = []
        source = Path(source_path)
        if mime_type == "application/pdf" or source.suffix.lower() == ".pdf":
            pdf = fitz.open(source_path)
            try:
                for idx, page in enumerate(pdf):
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    image_path = self.storage.save_bytes(
                        f"{document_id}/pages/page_{idx + 1}.png",
                        pix.tobytes("png"),
                    )
                    pages.append(
                        Page(
                            document_id=document_id,
                            page_number=idx + 1,
                            width=float(page.rect.width),
                            height=float(page.rect.height),
                            rotation=int(page.rotation),
                            image_path=image_path,
                            metadata_json={"rendered_from": "pdf"},
                        )
                    )
            finally:
                pdf.close()
            return pages

        image_doc = fitz.open(source_path)
        try:
            page = image_doc[0]
            pages.append(
                Page(
                    document_id=document_id,
                    page_number=1,
                    width=float(page.rect.width),
                    height=float(page.rect.height),
                    rotation=0,
                    image_path=source_path,
                    metadata_json={"rendered_from": "image"},
                )
            )
        finally:
            image_doc.close()
        return pages
