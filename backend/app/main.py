import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import settings, RAW_PDFS_DIR, CHROMA_PERSIST_DIR
from app.api.routes_chat import router as chat_router
from app.api.routes_voice import router as voice_router
from app.api.routes_docs import router as docs_router
from app.core.vector_store import vector_store
from app.core.llm import llm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("=" * 60)
    print(f"🚀 Initializing {settings.PROJECT_NAME} (v{settings.VERSION})")
    print(f"📁 PDF Storage: {RAW_PDFS_DIR}")
    print(f"🗄️  ChromaDB Path: {CHROMA_PERSIST_DIR}")
    
    # Check Gemini API Key
    if settings.GEMINI_API_KEY:
        print(f"✨ Gemini API Key configured. Model: {settings.GEMINI_MODEL}")
        llm_client.update_api_key(settings.GEMINI_API_KEY)
        vector_store.reload_embeddings(settings.GEMINI_API_KEY)
    else:
        print("⚠️  Warning: GEMINI_API_KEY is not set in backend/.env. Using development fallback modes.")
    
    # Report vector store status
    stats = vector_store.get_stats()
    print(f"📚 Vector Index Status: {stats['total_chunks']} chunks from {len(stats['documents'])} policy documents.")
    print("=" * 60)

    yield

    # Shutdown actions
    print(f"🛑 Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Cross-lingual RAG and voice assistant for Indian Welfare Schemes & Policies",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(docs_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "gemini_configured": llm_client.is_configured(),
        "total_chunks_indexed": vector_store.collection.count(),
        "version": settings.VERSION
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
        "health_check": "/health",
        "supported_languages": list(settings.SUPPORTED_LANGUAGES.keys())
    }


# If frontend static build directory exists, mount it
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
