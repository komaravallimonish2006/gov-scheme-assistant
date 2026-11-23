from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.schemas import VoiceQueryResponse, TTSRequest, TTSResponse
from app.core.speech import speech_service
from app.core.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/api/voice", tags=["Voice"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...)
):
    """
    Transcribes audio into text supporting regional Indian languages.
    """
    try:
        content = await file.read()
        transcript, lang = speech_service.speech_to_text(content, filename=file.filename or "audio.wav")
        return {"transcript": transcript, "language": lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/query", response_model=VoiceQueryResponse)
async def voice_query(
    file: UploadFile = File(...),
    preferred_language: Optional[str] = Form("auto")
):
    """
    End-to-end voice query endpoint:
    Audio Input -> Multilingual STT -> RAG Pipeline -> Localized TTS Audio Output.
    """
    try:
        content = await file.read()
        transcript, detected_lang = speech_service.speech_to_text(
            content,
            filename=file.filename or "audio.wav"
        )

        if not transcript or not transcript.strip():
            raise HTTPException(status_code=400, detail="Could not capture clear speech from audio.")

        target_lang = detected_lang if preferred_language == "auto" else (preferred_language or detected_lang)

        # Execute RAG query
        chat_resp = rag_pipeline.run(
            query=transcript,
            preferred_language=target_lang
        )

        # Generate audio response using regional TTS
        audio_b64 = speech_service.text_to_speech(chat_resp.answer, language_code=chat_resp.language)

        return VoiceQueryResponse(
            transcript=transcript,
            language=chat_resp.language,
            chat_response=chat_resp,
            audio_base64=audio_b64
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice query processing failed: {str(e)}")


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech_endpoint(request: TTSRequest):
    """
    Converts policy explanation text into spoken regional audio (MP3 Base64).
    """
    try:
        b64_audio = speech_service.text_to_speech(request.text, language_code=request.language)
        if not b64_audio:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech audio.")
        return TTSResponse(audio_base64=b64_audio, format="audio/mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")
