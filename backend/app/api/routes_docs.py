import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.config import settings, RAW_PDFS_DIR
from app.models.schemas import DocumentUploadResponse, DocumentListResponse, DocumentItem
from app.core.pdf_processor import pdf_processor
from app.core.vector_store import vector_store

router = APIRouter(prefix="/api/docs", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    scheme_name: Optional[str] = Form(None)
):
    """
    Admin endpoint to upload and index official Government Scheme PDF documents.
    Extracts text, preserves page numbers, chunks text, and stores vectors into ChromaDB.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    dest_path = RAW_PDFS_DIR / file.filename
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process and chunk PDF
        chunks = pdf_processor.chunk_document(dest_path, scheme_name=scheme_name)
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from this PDF (it may be empty or an image scan).")

        # Ingest into vector store
        added_count = vector_store.add_chunks(chunks)

        total_pages = max([c["page_number"] for c in chunks], default=1)

        return DocumentUploadResponse(
            filename=file.filename,
            total_pages=total_pages,
            total_chunks=added_count,
            message=f"Successfully indexed '{file.filename}' ({added_count} chunks across {total_pages} pages)."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process and index document: {str(e)}")


@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """
    Lists all indexed policy documents, chunks, and schemes.
    """
    try:
        raw_list = vector_store.list_documents()
        items = [
            DocumentItem(
                filename=doc["filename"],
                chunks_count=doc["chunks_count"],
                pages_count=doc["pages_count"],
                schemes=doc["schemes"]
            )
            for doc in raw_list
        ]
        total_chunks = sum(i.chunks_count for i in items)
        return DocumentListResponse(
            total_documents=len(items),
            total_chunks=total_chunks,
            documents=items
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")


@router.delete("/{doc_name}")
async def delete_document(doc_name: str):
    """
    Deletes an indexed document from ChromaDB and the raw PDFs directory.
    """
    try:
        deleted_count = vector_store.delete_document(doc_name)
        file_path = RAW_PDFS_DIR / doc_name
        if file_path.exists():
            file_path.unlink()
        return {"message": f"Deleted {deleted_count} chunks for document '{doc_name}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
