from fastapi import APIRouter, HTTPException
from typing import List
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse, LanguageInfo
from app.core.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Multilingual chat endpoint for querying Indian Government Schemes.
    Accepts queries in Telugu, Hindi, Tamil, English, and other regional languages.
    Returns grounded answers with citations (document name + page number).
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        response = rag_pipeline.run(
            query=request.query,
            preferred_language=request.language,
            conversation_history=request.conversation_history,
            filter_scheme=request.filter_scheme
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.get("/languages", response_model=List[LanguageInfo])
async def get_languages():
    """
    Returns the list of supported Indian regional languages and ISO codes.
    """
    langs = []
    for code, info in settings.SUPPORTED_LANGUAGES.items():
        langs.append(LanguageInfo(
            code=code,
            name=info["name"],
            native=info["native"]
        ))
    return langs
