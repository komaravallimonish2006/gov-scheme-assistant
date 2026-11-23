import re
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pypdf
except ImportError:
    pypdf = None


class PDFProcessor:
    """
    Extracts text from official Government Scheme & Policy PDF documents,
    retaining page numbers and generating chunk metadata for citations.
    """

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_by_pages(self, file_path: str | Path) -> List[Dict[str, Any]]:
        """
        Reads a PDF file and extracts text page by page.
        Returns a list of dicts with:
            {'page_number': int, 'text': str}
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        pages_data = []
        if pypdf is not None:
            with open(path, "rb") as f:
                reader = pypdf.PdfReader(f)
                total_pages = len(reader.pages)
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    cleaned_text = self._clean_text(page_text)
                    if cleaned_text.strip():
                        pages_data.append({
                            "page_number": page_idx + 1,
                            "text": cleaned_text,
                            "total_pages": total_pages
                        })
        else:
            # Fallback direct text stream extractor when pypdf is not installed
            with open(path, "rb") as f:
                content = f.read().decode("latin-1", "ignore")
                matches = re.findall(r'\((.*?)\)\s*Tj', content)
                if matches:
                    extracted = "\n".join([m.replace("\\(", "(").replace("\\)", ")") for m in matches])
                    cleaned = self._clean_text(extracted)
                    pages_data.append({"page_number": 1, "text": cleaned, "total_pages": 1})
                else:
                    pages_data.append({"page_number": 1, "text": f"Document {path.name}", "total_pages": 1})

        return pages_data

    def chunk_document(self, file_path: str | Path, scheme_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Splits extracted pages into overlapping chunks with precise citations.
        """
        path = Path(file_path)
        document_name = path.name
        pages_data = self.extract_text_by_pages(path)
        
        # If scheme_name is not provided, deduce from file name or first page
        if not scheme_name and pages_data:
            scheme_name = self._infer_scheme_name(document_name, pages_data[0]["text"])
        elif not scheme_name:
            scheme_name = path.stem.replace("_", " ").title()

        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]

            # Paragraph and sentence-aware chunking
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            
            current_chunk = ""
            for p in paragraphs:
                if len(current_chunk) + len(p) <= self.chunk_size:
                    current_chunk += ("\n\n" if current_chunk else "") + p
                else:
                    if current_chunk:
                        chunk_idx += 1
                        chunks.append({
                            "chunk_id": f"{document_name}_p{page_num}_c{chunk_idx}",
                            "document_name": document_name,
                            "page_number": page_num,
                            "scheme_name": scheme_name,
                            "text": current_chunk.strip()
                        })
                    
                    # If paragraph alone is longer than chunk_size, split by sentences
                    if len(p) > self.chunk_size:
                        sentences = re.split(r'(?<=[.!?]) +', p)
                        sub_chunk = ""
                        for s in sentences:
                            if len(sub_chunk) + len(s) <= self.chunk_size:
                                sub_chunk += (" " if sub_chunk else "") + s
                            else:
                                if sub_chunk:
                                    chunk_idx += 1
                                    chunks.append({
                                        "chunk_id": f"{document_name}_p{page_num}_c{chunk_idx}",
                                        "document_name": document_name,
                                        "page_number": page_num,
                                        "scheme_name": scheme_name,
                                        "text": sub_chunk.strip()
                                    })
                                sub_chunk = s
                        current_chunk = sub_chunk
                    else:
                        current_chunk = p

            if current_chunk.strip():
                chunk_idx += 1
                chunks.append({
                    "chunk_id": f"{document_name}_p{page_num}_c{chunk_idx}",
                    "document_name": document_name,
                    "page_number": page_num,
                    "scheme_name": scheme_name,
                    "text": current_chunk.strip()
                })

        return chunks

    def _clean_text(self, text: str) -> str:
        # Replace non-breaking spaces and normalize line breaks
        text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
        # Remove repeated hyphens or underscores
        text = re.sub(r'[-_]{4,}', '', text)
        # Collapse multiple empty lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _infer_scheme_name(self, filename: str, first_page_text: str) -> str:
        # Clean filename
        clean_name = Path(filename).stem.replace("_", " ").replace("-", " ")
        # Look for typical scheme headers in first page
        match = re.search(r'(?:Scheme|Yojana|Mission|Guidelines|Policy|Pradhan Mantri [A-Za-z ]+)\b', first_page_text, re.IGNORECASE)
        if match:
            # Grab line
            lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]
            for line in lines[:5]:
                if any(k in line.lower() for k in ["scheme", "yojana", "mission", "guidelines", "pradhan mantri"]):
                    return line[:80]
        return clean_name.title()


# Global processor instance
pdf_processor = PDFProcessor()
