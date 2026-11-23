import io
import os
import base64
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from gtts import gTTS
from app.config import settings
from app.core.llm import llm_client


class SpeechService:
    """
    Handles Speech-to-Text (STT) and Text-to-Speech (TTS) for Indian regional languages.
    """

    def __init__(self):
        self.supported_tts_langs = {
            "en": "en",
            "hi": "hi",
            "te": "te",
            "ta": "ta",
            "bn": "bn",
            "mr": "mr",
            "gu": "gu",
            "kn": "kn",
            "ml": "ml",
            "pa": "pa",
        }

    def text_to_speech(self, text: str, language_code: str = "en") -> str:
        """
        Converts text in regional language into base64-encoded MP3 audio.
        """
        # Clean text for TTS (remove markdown asterisks, hashes, etc.)
        cleaned = text.replace("*", "").replace("#", "").replace(">", "").strip()
        # Truncate if too long for quick playback
        if len(cleaned) > 500:
            cleaned = cleaned[:500] + "..."

        lang = self.supported_tts_langs.get(language_code, "en")

        try:
            tts = gTTS(text=cleaned, lang=lang, slow=False)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_b64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
            return audio_b64
        except Exception as e:
            print(f"[SpeechService] gTTS failed for lang '{lang}': {e}. Falling back to English.")
            try:
                tts = gTTS(text=cleaned, lang="en", slow=False)
                mp3_fp = io.BytesIO()
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)
                return base64.b64encode(mp3_fp.read()).decode("utf-8")
            except Exception as e2:
                print(f"[SpeechService] TTS fallback error: {e2}")
                return ""

    def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> Tuple[str, str]:
        """
        Transcribes speech audio into text using Gemini multimodal audio or SpeechRecognition.
        Returns (transcribed_text, detected_language_code).
        """
        # Try Gemini multimodal audio transcription if client is configured
        if llm_client.is_configured():
            try:
                transcript, lang = self._transcribe_with_gemini(audio_bytes, filename)
                if transcript.strip():
                    return transcript, lang
            except Exception as e:
                print(f"[SpeechService] Gemini audio transcription error: {e}")

        # Fallback to local SpeechRecognition library
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                with sr.AudioFile(tmp_path) as source:
                    audio_data = r.record(source)
                    # Recognize with Google Web Speech API (supports multilingual Indian languages)
                    text = r.recognize_google(audio_data)
                    return text, "auto"
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            print(f"[SpeechService] Local speech recognition error: {e}")

        return "Could not transcribe audio. Please type your query.", "en"

    def _transcribe_with_gemini(self, audio_bytes: bytes, filename: str) -> Tuple[str, str]:
        """
        Uses Gemini's native audio understanding to transcribe Indian language audio.
        """
        mime_type = "audio/wav"
        if filename.endswith(".mp3"):
            mime_type = "audio/mp3"
        elif filename.endswith(".ogg") or filename.endswith(".webm"):
            mime_type = "audio/webm"

        prompt = (
            "Listen to this audio query regarding an Indian government scheme. "
            "1. Accurately transcribe what the speaker said in their original language. "
            "2. Identify the language code (e.g. te for Telugu, hi for Hindi, ta for Tamil, en for English). "
            "Respond in JSON format: {\"transcript\": \"...\", \"language\": \"te\"}"
        )

        if llm_client._sdk_type == "google-genai":
            from google.genai import types
            part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            res = llm_client._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[part, prompt]
            )
            raw = res.text
        elif llm_client._sdk_type == "google-generativeai":
            import google.generativeai as legacy_genai
            res = llm_client._client.generate_content([
                {"mime_type": mime_type, "data": audio_bytes},
                prompt
            ])
            raw = res.text
        else:
            return "", "en"

        # Parse JSON
        import json
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("transcript", ""), data.get("language", "en")
        return raw.strip(), "en"


# Global speech service instance
speech_service = SpeechService()
