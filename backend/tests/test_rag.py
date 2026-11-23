import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import sys

# Ensure backend root is in python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.core.rag_pipeline import rag_pipeline
from app.core.pdf_processor import pdf_processor
from app.core.vector_store import vector_store

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gemini_configured" in data


def test_supported_languages():
    response = client.get("/api/languages")
    assert response.status_code == 200
    langs = response.json()
    codes = [l["code"] for l in langs]
    # Check key Indian languages are present
    assert "te" in codes  # Telugu
    assert "hi" in codes  # Hindi
    assert "ta" in codes  # Tamil
    assert "en" in codes  # English


def test_language_detection():
    # Telugu query
    assert rag_pipeline.detect_language("రైతు భరోసా పథకం వివరాలు ఏమిటి?") == "te"
    # Hindi query
    assert rag_pipeline.detect_language("प्रधानमंत्री किसान सम्मान निधि योजना") == "hi"
    # Tamil query
    assert rag_pipeline.detect_language("பிரதமர் கிசான் திட்டம் தகுதி என்ன?") == "ta"
    # English query
    assert rag_pipeline.detect_language("What is the eligibility for PM KISAN?") == "en"


def test_pdf_chunking_and_vector_store(tmp_path):
    # Create sample policy document in vector store
    sample_chunks = [
        {
            "chunk_id": "test_pmkisan_p1_c1",
            "document_name": "Test_PM_KISAN.pdf",
            "page_number": 1,
            "scheme_name": "PM-KISAN",
            "text": "Under PM-KISAN, financial assistance of Rs 6000 per year is given to eligible farmer families in three installments."
        },
        {
            "chunk_id": "test_pmkisan_p2_c2",
            "document_name": "Test_PM_KISAN.pdf",
            "page_number": 2,
            "scheme_name": "PM-KISAN",
            "text": "Eligibility: All landholding farmer families with cultivable land. Mandatory document: Aadhaar card and bank account."
        }
    ]
    added = vector_store.add_chunks(sample_chunks)
    assert added == 2

    # Query vector store
    results = vector_store.query("farmer financial assistance Rs 6000", n_results=1)
    assert len(results) > 0
    assert results[0]["document_name"] == "Test_PM_KISAN.pdf"
    assert results[0]["page_number"] in [1, 2]


def test_chat_endpoint_response_structure():
    payload = {
        "query": "What is the benefit under PM-KISAN?",
        "language": "en"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "language" in data
    assert "citations" in data
    assert "suggested_followups" in data
