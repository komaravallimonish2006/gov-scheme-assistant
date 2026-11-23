# Multilingual Government Scheme & Policy Assistant
### బహుభాషా సంక్షేమ పథకాల సహాయకుడు | बहुभाषी सरकारी योजना एवं नीति सहायक

An AI-powered public welfare assistant designed to help Indian citizens discover, understand, and verify eligibility for central and state government schemes (e.g., **PM-KISAN**, **Ayushman Bharat PM-JAY**, **PMAY**, **Rythu Bharosa**, etc.) in their native regional languages using **Strictly Grounded Cross-Lingual RAG**, **Google Gemini**, and **Voice Speech-to-Text & Text-to-Speech**.

---

## 🌟 Key Features

1. **Cross-Lingual Retrieval-Augmented Generation (RAG)**
   - Official policy guidelines are often in English or Hindi.
   - Citizens can ask questions in **Telugu, Hindi, Tamil, Bengali, Marathi, Kannada, Malayalam, English**, or conversational scripts (e.g., Hinglish, Telugish).
   - Queries are automatically expanded across languages to retrieve the most relevant sections from official policy PDFs stored in **ChromaDB**.

2. **Strict Grounding & Hallucination Prevention**
   - Answers are synthesized strictly from verified government document excerpts.
   - If an official scheme document does not mention an eligibility condition, monetary figure, or deadline, the assistant explicitly states that the document does not mention it and directs the citizen to their nearest Common Service Centre (CSC / MeeSeva) or the official ministry portal.

3. **Verifiable Document Citations**
   - Every answer includes exact source citations displaying the **Official PDF File Name**, **Page Number**, and quoted excerpt.

4. **Speech-to-Text (STT) & Text-to-Speech (TTS) Voice Support**
   - Citizens who prefer voice can click the microphone to speak their query in their regional tongue.
   - Answers can be read aloud in regional Indian voices using native Text-to-Speech.

5. **Admin PDF Ingestion Pipeline**
   - Upload official scheme guidelines and circulars through the web dashboard or CLI script.
   - Automatically splits documents page-by-page and indexes chunks into the vector store.

---

## 🏗️ Architecture & Project Structure

```
gov-scheme-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI entry point & CORS setup
│   │   ├── config.py                # Environment variables & language settings
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_chat.py       # Multilingual text chat endpoints
│   │   │   ├── routes_voice.py      # Voice query (STT / TTS) endpoints
│   │   │   └── routes_docs.py       # Admin PDF upload & indexing endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── llm.py               # Gemini API client & grounding prompts
│   │   │   ├── rag_pipeline.py      # Cross-lingual retrieval & citation logic
│   │   │   ├── vector_store.py      # ChromaDB persistent vector storage
│   │   │   ├── pdf_processor.py     # PDF text extraction & page-aware chunking
│   │   │   └── speech.py            # Speech-to-Text & Text-to-Speech engine
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py           # Pydantic request & response schemas
│   ├── data/
│   │   ├── raw_pdfs/                # Verified government policy PDFs
│   │   └── chroma_db/               # Local persistent Chroma vector database
│   ├── scripts/
│   │   └── ingest_policies.py       # Batch script to index PDFs into Vector DB
│   ├── tests/
│   │   └── test_rag.py              # Test suite for chunking, detection & RAG
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment configuration template
│   └── .env                         # Local environment variables
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx       # Chat interface with cited answers & TTS
│   │   │   ├── LanguageSelector.jsx # Regional language picker (Telugu, Hindi, etc.)
│   │   │   ├── VoiceRecorder.jsx    # Audio recording component for voice queries
│   │   │   └── CitationCard.jsx     # Source document & page number viewer
│   │   ├── services/
│   │   │   └── api.js               # API service connecting to backend
│   │   ├── App.jsx                  # Main dashboard with Chat & PDF management tabs
│   │   ├── main.jsx                 # Vite React root
│   │   └── index.css                # Tailwind CSS styling
│   ├── index.html                   # HTML entry point
│   ├── vite.config.js               # Vite bundler configuration
│   └── package.json                 # Node dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: v18+ & npm

---

### 2. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API Key**:
   Open `backend/.env` and insert your Google Gemini API Key:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

5. **Ingest Initial Policy Documents**:
   Run the batch ingestion script to prepare sample verified guidelines (PM-KISAN, Ayushman Bharat PM-JAY):
   ```bash
   python scripts/ingest_policies.py
   ```

6. **Start the FastAPI server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Interactive Swagger API Docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

---

### 3. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```
   Open your browser at `http://localhost:5173`.

---

## 🇮🇳 Supported Languages

| Code | Language | Native Script | Voice TTS Supported |
|---|---|---|---|
| `te` | Telugu | తెలుగు | ✅ |
| `hi` | Hindi | हिन्दी | ✅ |
| `ta` | Tamil | தமிழ் | ✅ |
| `bn` | Bengali | বাংলা | ✅ |
| `mr` | Marathi | मराठी | ✅ |
| `kn` | Kannada | ಕನ್ನಡ | ✅ |
| `ml` | Malayalam | മലയാളം | ✅ |
| `gu` | Gujarati | ગુજરાતી | ✅ |
| `pa` | Punjabi | ਪੰਜਾਬੀ | ✅ |
| `en` | English | English | ✅ |

---

## 📡 API Reference

### 1. Multilingual Chat
- **POST** `/api/chat`
- **Request Body**:
  ```json
  {
    "query": "రైతు భరోసా పథకం అర్హతలు ఏమిటి?",
    "language": "te",
    "conversation_history": []
  }
  ```
- **Response**:
  ```json
  {
    "answer": "పీఎం కిసాన్ పథకం కింద అర్హులైన రైతు కుటుంబాలకు సంవత్సరానికి ₹6,000 ఆర్థిక సాయం మూడు విడతలలో అందించబడుతుంది...",
    "language": "te",
    "detected_language": "te",
    "citations": [
      {
        "document_name": "PM_KISAN_Guidelines.pdf",
        "page_number": 1,
        "snippet": "Under the Scheme, an income support of Rs. 6,000/- per year is provided...",
        "confidence_score": 0.92,
        "scheme_name": "PM-KISAN"
      }
    ],
    "suggested_followups": [
      "ఈ పథకానికి ఏయే డాక్యుమెంట్లు కావాలి?",
      "దరఖాస్తు విధానం ఏమిటి?"
    ]
  }
  ```

### 2. Voice Query
- **POST** `/api/voice/query`
- **Multipart Form Data**:
  - `file`: Audio file (WebM / WAV / MP3)
  - `preferred_language`: `te` / `hi` / `auto`
- **Returns**: Audio transcript, grounded answer, citations, and base64 MP3 TTS audio.

### 3. Document Ingestion
- **POST** `/api/docs/upload`
- **Multipart Form Data**:
  - `file`: Official policy PDF
  - `scheme_name`: Optional title tag

---

## 🧪 Running Tests

To verify that the RAG pipeline, chunking, and language detection work as expected:
```bash
cd backend
pytest tests/test_rag.py
```
