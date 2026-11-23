from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_name: str = Field(..., description="Source policy PDF file name")
    page_number: int = Field(..., description="Document page number of the citation")
    snippet: str = Field(..., description="Extracted relevant text excerpt")
    confidence_score: Optional[float] = Field(None, description="Similarity or relevance score")
    scheme_name: Optional[str] = Field(None, description="Name of the government scheme")


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    query: str = Field(..., description="Citizen's question in any supported Indian language or English")
    language: str = Field("auto", description="Preferred output language ISO code (e.g. te, hi, ta, en, auto)")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation context")
    filter_scheme: Optional[str] = Field(None, description="Optional scheme name filter")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Assistant's answer translated and formatted into the target language")
    language: str = Field(..., description="Language of the answer")
    detected_language: Optional[str] = Field(None, description="Detected language of citizen query")
    citations: List[Citation] = Field(default=[], description="Source document references and page numbers")
    confidence: Optional[float] = Field(None, description="Confidence estimate")
    suggested_followups: List[str] = Field(default=[], description="Recommended related questions for the citizen")


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")
    language: str = Field("en", description="Language code (e.g. te, hi, ta, en)")


class TTSResponse(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded MP3 audio")
    format: str = Field("audio/mp3", description="Audio MIME type")


class VoiceQueryResponse(BaseModel):
    transcript: str = Field(..., description="Transcribed query text")
    language: str = Field(..., description="Detected language")
    chat_response: ChatResponse = Field(..., description="RAG answer and citations")
    audio_base64: Optional[str] = Field(None, description="Synthesized voice audio in target language")


class DocumentUploadResponse(BaseModel):
    filename: str
    total_pages: int
    total_chunks: int
    message: str


class DocumentItem(BaseModel):
    filename: str
    chunks_count: int
    pages_count: Optional[int] = None
    schemes: List[str] = []


class DocumentListResponse(BaseModel):
    total_documents: int
    total_chunks: int
    documents: List[DocumentItem] = []


class LanguageInfo(BaseModel):
    code: str
    name: str
    native: str
