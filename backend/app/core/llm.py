import os
import json
import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.schemas import Citation, ChatResponse


SYSTEM_PROMPT_TEMPLATE = """You are the official Multilingual Government Scheme & Policy Assistant of India.
Your mission is to provide accurate, easy-to-understand, and empathetic guidance to citizens regarding government welfare schemes, policies, eligibility, subsidies, and application steps.

### STRICT RULES:
1. Grounding & Anti-Hallucination: Answer using ONLY the verified excerpts provided in the [CONTEXT] section below.
2. If the excerpts do not contain the answer, explicitly state that the provided official documents do not mention this detail, and advise the citizen to consult the nearest Common Service Centre (CSC / MeeSeva) or the official scheme portal. DO NOT invent eligibility criteria, dates, or monetary amounts.
3. Language & Tone: Respond directly in the requested language: {target_language_name} ({target_language_native}). Use respectful, clear, and citizen-friendly language.
4. Structure your response with clean Markdown:
   - **Scheme Summary**
   - **Eligibility Criteria** (Who qualifies)
   - **Benefits / Assistance Provided** (Financial subsidy, rations, insurance, etc.)
   - **Required Documents** (Aadhaar, income certificate, land records, etc.)
   - **Application Process** (Online portal, offline office, nodal department)
5. Output Format:
Always provide your answer, followed by recommended follow-up questions formatted as:
---FOLLOWUPS---
- [Follow-up question 1 in {target_language_name}]
- [Follow-up question 2 in {target_language_name}]
- [Follow-up question 3 in {target_language_name}]
"""


class GeminiLLMClient:
    """
    Client interface for Google Gemini with support for the modern `google-genai` SDK
    and fallback handling.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._client = None
        self._sdk_type = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            return

        # Attempt modern google-genai SDK
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._sdk_type = "google-genai"
            return
        except Exception as e:
            pass

        # Attempt google-generativeai SDK
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            self._client = legacy_genai.GenerativeModel(self.model_name)
            self._sdk_type = "google-generativeai"
            return
        except Exception as e:
            pass

        # Attempt direct REST API via requests
        try:
            import requests
            self._client = requests
            self._sdk_type = "rest"
            return
        except Exception as e:
            self._client = None
            self._sdk_type = None

    def update_api_key(self, api_key: str):
        self.api_key = api_key
        self._init_client()

    def is_configured(self) -> bool:
        return bool(self.api_key and self._client)

    def generate_rag_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        target_language_code: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatResponse:
        """
        Generates grounded, cited response in citizen's selected language.
        """
        lang_meta = settings.SUPPORTED_LANGUAGES.get(
            target_language_code,
            {"name": "English", "native": "English"}
        )
        target_name = lang_meta["name"]
        target_native = lang_meta["native"]

        # Build citations list from context chunks
        citations: List[Citation] = []
        context_text_blocks = []
        for idx, chunk in enumerate(context_chunks):
            doc = chunk.get("document_name", "Official Policy PDF")
            page = chunk.get("page_number", 1)
            text = chunk.get("text", "")
            scheme = chunk.get("scheme_name", "")
            score = chunk.get("score", 0.8)

            snippet = text[:200] + "..." if len(text) > 200 else text
            citations.append(Citation(
                document_name=doc,
                page_number=page,
                snippet=snippet,
                confidence_score=score,
                scheme_name=scheme
            ))

            context_text_blocks.append(
                f"[Source {idx+1}: {doc} (Page {page}) - Scheme: {scheme}]\n{text}"
            )

        context_str = "\n\n".join(context_text_blocks) if context_text_blocks else "No matching scheme documents found in the database."

        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(
            target_language_name=target_name,
            target_language_native=target_native
        )

        user_prompt = f"""[CONTEXT FROM OFFICIAL POLICY DOCUMENTS]
{context_str}

[CONVERSATION HISTORY]
{self._format_history(conversation_history or [])}

[CITIZEN'S QUESTION]
{query}

Please answer the citizen's question based strictly on the official context above in {target_name} ({target_native})."""

        # If Gemini is configured, invoke it
        if self.is_configured():
            try:
                raw_text = self._call_gemini(system_instruction, user_prompt)
                return self._parse_llm_output(raw_text, citations, target_language_code)
            except Exception as e:
                print(f"[GeminiLLM] API call failed: {e}")

        # Graceful fallback generator for development / offline use
        return self._fallback_rag_response(query, context_chunks, target_language_code, citations)

    def _call_gemini(self, system_instruction: str, user_prompt: str) -> str:
        if self._sdk_type == "google-genai":
            from google.genai import types
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=2048,
                )
            )
            return response.text
        elif self._sdk_type == "google-generativeai":
            # Pass combined prompt to legacy model
            full_prompt = f"{system_instruction}\n\n{user_prompt}"
            response = self._client.generate_content(
                full_prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 2048}
            )
            return response.text
        elif self._sdk_type == "rest":
            import requests
            candidate_models = list(dict.fromkeys([
                self.model_name,
                "gemini-3.1-flash-lite",
                "gemini-3-flash-preview",
                "gemini-3.5-flash"
            ]))
            
            payload = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
                },
                "contents": [
                    {"role": "user", "parts": [{"text": user_prompt}]}
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 2048
                }
            }

            last_error = None
            for model in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                try:
                    resp = requests.post(url, json=payload, timeout=12)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    else:
                        last_error = f"Model {model} returned status {resp.status_code}: {resp.text[:120]}"
                except Exception as e:
                    last_error = f"Model {model} failed: {e}"
                    continue

            raise RuntimeError(last_error or "All candidate Gemini models failed to respond in time.")
        else:
            raise RuntimeError("Gemini client is not initialized.")

    def _parse_llm_output(self, raw_text: str, citations: List[Citation], language_code: str) -> ChatResponse:
        followups = []
        answer = raw_text

        if "---FOLLOWUPS---" in raw_text:
            parts = raw_text.split("---FOLLOWUPS---")
            answer = parts[0].strip()
            followup_lines = parts[1].strip().splitlines()
            for line in followup_lines:
                clean_line = re.sub(r'^[-*0-9.]+\s*', '', line).strip()
                if clean_line:
                    followups.append(clean_line)

        # Default followups if LLM didn't produce 3
        if not followups:
            followups = self._default_followups(language_code)

        return ChatResponse(
            answer=answer,
            language=language_code,
            citations=citations,
            confidence=0.92,
            suggested_followups=followups[:3]
        )

    def _fallback_rag_response(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        language_code: str,
        citations: List[Citation]
    ) -> ChatResponse:
        """Fallback response when Gemini API key is waiting to be configured."""
        lang_meta = settings.SUPPORTED_LANGUAGES.get(language_code, {"name": "English", "native": "English"})
        
        if not chunks:
            if language_code == "te":
                msg = "క్షమించండి, మీ ప్రశ్నకు సంబంధించిన అధికారిక పథక పత్రాలు డేటాబేస్‌లో లభించలేదు. దయచేసి పథకం పేరు సరిచూసుకోండి లేదా సమీప మీసేవ కేంద్రాన్ని సంప్రదించండి."
            elif language_code == "hi":
                msg = "क्षमा करें, आपके प्रश्न से संबंधित आधिकारिक योजना दस्तावेज़ डेटाबेस में नहीं मिले। कृपया योजना का नाम जांचें या निकटतम सीएससी केंद्र से संपर्क करें।"
            elif language_code == "ta":
                msg = "மன்னிக்கவும், உங்கள் கேள்வி தொடர்பான அதிகாரப்பூர்வ திட்ட ஆவணங்கள் தரவுத்தளத்தில் கிடைக்கவில்லை. அருகிலுள்ள இ-சேவை மையத்தைத் தொடர்பு கொள்ளவும்."
            else:
                msg = "No verified policy documents matching your query were found in the database. Please ensure official scheme PDFs are uploaded or consult your nearest Common Service Centre (CSC)."
            
            return ChatResponse(
                answer=msg,
                language=language_code,
                citations=[],
                confidence=0.5,
                suggested_followups=self._default_followups(language_code)
            )

        top_chunk = chunks[0]
        scheme_title = top_chunk.get("scheme_name", "Government Scheme")
        doc_name = top_chunk.get("document_name", "Policy Document")
        page_num = top_chunk.get("page_number", 1)

        # Build informative response summarizing the retrieved excerpt
        summary = (
            f"### {scheme_title} (Source: {doc_name}, Page {page_num})\n\n"
            f"Based on the official government documentation on record:\n\n"
            f"> {top_chunk.get('text', '')[:450]}...\n\n"
            f"**Key Highlights:**\n"
            f"- **Official Document:** {doc_name} (Page {page_num})\n"
            f"- **Status:** Verified policy guidelines retrieved.\n\n"
            f"*Tip: Configure your `GEMINI_API_KEY` in `.env` for full AI multi-turn cross-lingual reasoning and synthesis.*"
        )

        return ChatResponse(
            answer=summary,
            language=language_code,
            citations=citations,
            confidence=0.88,
            suggested_followups=self._default_followups(language_code)
        )

    def _default_followups(self, language_code: str) -> List[str]:
        followup_dict = {
            "te": [
                "ఈ పథకానికి దరఖాస్తు చేసుకోవడానికి ఏ డాక్యుమెంట్లు కావాలి?",
                "పథకానికి అర్హత ప్రమాణాలు ఏమిటి?",
                "సహాయం లేదా సబ్సిడీ మొత్తం ఎంత వస్తుంది?"
            ],
            "hi": [
                "इस योजना के लिए कौन से दस्तावेज आवश्यक हैं?",
                "इस योजना की पात्रता मानदंड क्या हैं?",
                "ऑनलाइन आवेदन कैसे करें?"
            ],
            "ta": [
                "இந்த திட்டத்திற்கு என்ன ஆவணங்கள் தேவை?",
                "திட்டத்திற்கான தகுதி வரம்புகள் என்ன?",
                "விண்ணப்பிக்கும் முறை என்ன?"
            ],
            "en": [
                "What documents are required to apply for this scheme?",
                "What is the eligibility criteria and income limit?",
                "What is the step-by-step application procedure?"
            ]
        }
        return followup_dict.get(language_code, followup_dict["en"])

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "None"
        formatted = []
        for msg in history[-4:]:
            role = "Citizen" if msg.get("role") == "user" else "Assistant"
            formatted.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(formatted)


# Global LLM instance
llm_client = GeminiLLMClient()
