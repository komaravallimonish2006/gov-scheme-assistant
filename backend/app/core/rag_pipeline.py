import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.schemas import ChatResponse, ChatMessage
from app.core.vector_store import vector_store
from app.core.llm import llm_client


class CrossLingualRAGPipeline:
    """
    RAG Pipeline supporting cross-lingual queries across Indian Government Scheme PDFs.
    Matches regional language queries (Telugu, Hindi, Tamil, etc.) against English/Hindi
    official policy PDFs and generates localized cited answers.
    """

    def __init__(self):
        self.vector_store = vector_store
        self.llm = llm_client

    def detect_language(self, text: str) -> str:
        """
        Detects primary script / language of citizen query.
        """
        # Unicode range checks for major Indian scripts
        for char in text:
            code = ord(char)
            if 0x0C00 <= code <= 0x0C7F:
                return "te"  # Telugu
            elif 0x0900 <= code <= 0x097F:
                return "hi"  # Hindi / Devanagari (Marathi)
            elif 0x0B80 <= code <= 0x0BFF:
                return "ta"  # Tamil
            elif 0x0980 <= code <= 0x09FF:
                return "bn"  # Bengali
            elif 0x0C80 <= code <= 0x0CFF:
                return "kn"  # Kannada
            elif 0x0D00 <= code <= 0x0D7F:
                return "ml"  # Malayalam
            elif 0x0A80 <= code <= 0x0AFF:
                return "gu"  # Gujarati
            elif 0x0A00 <= code <= 0x0A7F:
                return "pa"  # Punjabi

        # Default to English
        return "en"

    def expand_cross_lingual_query(self, query: str, detected_lang: str) -> List[str]:
        """
        Fast instantaneous cross-lingual query expansion (0ms).
        Maps regional language terms and Romanized Indian schemes into English keywords
        to retrieve policy chunks immediately without blocking on extra LLM roundtrips.
        """
        queries = [query]
        query_lower = query.lower()

        # Scheme & domain keyword mapping (Telugu, Hindi, Tamil, Kannada, Marathi, English)
        if any(w in query for w in ["రైతు", "किसान", "உழவர்", "రైతులు", "సేద్యం", "వ్యవసాయం"]) or "kisan" in query_lower or "farmer" in query_lower:
            queries.append("farmer agriculture subsidy eligibility PM-KISAN landholding")
        
        if any(w in query for w in ["ఆరోగ్య", "आरोग्य", "மருத்துவம்", "ఆయుష్మాన్", "ఆసుపత్రి"]) or "ayushman" in query_lower or "pmjay" in query_lower or "health" in query_lower:
            queries.append("health insurance Ayushman Bharat PM-JAY hospital cashless coverage 5 lakhs")
        
        if any(w in query for w in ["ఆవాస్", "ఇల్లు", "आवास", "வீடு", "గృహ"]) or "pmay" in query_lower or "housing" in query_lower or "awas" in query_lower:
            queries.append("housing scheme PMAY Pradhan Mantri Awas Yojana subsidy shelter")
        
        if any(w in query for w in ["మహిళ", "महिला", "பெண்", "స్త్రీ"]) or "women" in query_lower:
            queries.append("women empowerment financial assistance livelihood self help groups")

        if any(w in query for w in ["పెన్షన్", "పింఛను", "पेंशन", "ஓய்வூதியம்"]) or "pension" in query_lower:
            queries.append("social security pension elderly widow disability scheme")

        if any(w in query for w in ["అర్హత", "పాఠక", "पात्रता", "தகுதி"]) or "eligibility" in query_lower or "qualification" in query_lower:
            queries.append("eligibility criteria income limit requirements rules")

        if any(w in query for w in ["డాక్యుమెంట్", "పత్రాలు", "దస్తావేజులు", "दस्तावेज", "ஆவணங்கள்"]) or "documents" in query_lower:
            queries.append("required documents Aadhaar card proof certificate")

        # Extract Roman words (e.g. "PM-KISAN", "PMAY", "KYC")
        roman_words = re.findall(r'[A-Za-z0-9\-]+', query)
        if roman_words:
            queries.append(" ".join(roman_words))

        return list(dict.fromkeys(queries))

    def run(
        self,
        query: str,
        preferred_language: str = "auto",
        conversation_history: Optional[List[ChatMessage]] = None,
        filter_scheme: Optional[str] = None,
        top_k: int = 4
    ) -> ChatResponse:
        """
        Executes end-to-end RAG:
        1. Language detection
        2. Cross-lingual query expansion
        3. Vector retrieval with citation tracking
        4. Gemini generation with citations
        """
        detected_lang = self.detect_language(query)
        target_lang = detected_lang if preferred_language == "auto" else preferred_language

        # Step 1: Expand queries for cross-lingual vector retrieval
        search_queries = self.expand_cross_lingual_query(query, detected_lang)

        # Step 2: Retrieve candidate chunks from ChromaDB
        candidate_chunks: Dict[str, Dict[str, Any]] = {}
        where_filter = {"scheme_name": filter_scheme} if filter_scheme else None

        for sq in search_queries:
            results = self.vector_store.query(sq, n_results=top_k, where=where_filter)
            for res in results:
                cid = res["chunk_id"]
                if cid not in candidate_chunks or res["score"] > candidate_chunks[cid]["score"]:
                    candidate_chunks[cid] = res

        # Sort by similarity score and take top_k
        ranked_chunks = sorted(
            candidate_chunks.values(),
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:top_k]

        # Step 3: Format conversation history
        hist_dicts = []
        if conversation_history:
            for item in conversation_history:
                hist_dicts.append({"role": item.role, "content": item.content})

        # Step 4: Generate cited response
        response = self.llm.generate_rag_response(
            query=query,
            context_chunks=ranked_chunks,
            target_language_code=target_lang,
            conversation_history=hist_dicts
        )
        response.detected_language = detected_lang
        return response


# Global pipeline instance
rag_pipeline = CrossLingualRAGPipeline()
