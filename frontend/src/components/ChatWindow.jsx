import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Volume2,
  VolumeX,
  Loader2,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  RotateCcw,
  BookOpen
} from 'lucide-react';
import CitationCard from './CitationCard';
import VoiceRecorder from './VoiceRecorder';
import { requestTTS } from '../services/api';

export default function ChatWindow({
  messages,
  isLoading,
  onSendMessage,
  onVoiceRecorded,
  selectedLanguage,
  onSelectLanguage,
  languages,
  onResetChat,
}) {
  const [inputText, setInputText] = useState('');
  const [playingAudioIndex, setPlayingAudioIndex] = useState(null);
  const [loadingAudioIndex, setLoadingAudioIndex] = useState(null);
  
  const messagesEndRef = useRef(null);
  const currentAudioRef = useRef(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePlayTTS = async (text, language, index) => {
    // If this message is already playing, stop it
    if (playingAudioIndex === index && currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingAudioIndex(null);
      return;
    }

    // Stop any existing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingAudioIndex(null);
    }

    setLoadingAudioIndex(index);
    try {
      const data = await requestTTS(text, language || 'en');
      if (data?.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
        currentAudioRef.current = audio;
        setPlayingAudioIndex(index);

        audio.onended = () => {
          setPlayingAudioIndex(null);
          currentAudioRef.current = null;
        };

        audio.onerror = () => {
          setPlayingAudioIndex(null);
          currentAudioRef.current = null;
        };

        await audio.play();
      }
    } catch (err) {
      console.error('Error playing TTS:', err);
    } finally {
      setLoadingAudioIndex(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden">
      {/* Chat Sub-header */}
      <div className="px-5 py-3 bg-slate-800/60 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-xs font-medium text-slate-300">
            Verified Scheme RAG Assistant
          </span>
          <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-medium">
            Strict Grounding
          </span>
        </div>

        <button
          onClick={onResetChat}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 px-2.5 py-1 rounded-lg hover:bg-slate-700/60 transition-all"
          title="Reset conversation"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4 shadow-lg shadow-amber-500/5">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-slate-200 mb-1">
              Ask about Indian Government Schemes & Policies
            </h3>
            <p className="text-xs max-w-md text-slate-400 leading-relaxed mb-6">
              Ask your questions in <span className="text-amber-400 font-medium">తెలుగు, हिन्दी, தமிழ், English</span>, or any Indian regional language. All answers are grounded in verified policy documents with page citations.
            </p>

            {/* Quick Starter Prompts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-w-xl w-full text-left">
              {[
                {
                  label: "PM-KISAN అర్హతలు ఏమిటి?",
                  sub: "రైతు భరోసా & ఆర్థిక సహాయం వివరాలు (Telugu)",
                },
                {
                  label: "आयुष्मान भारत योजना के तहत कितना कवर मिलता है?",
                  sub: "₹5 लाख का स्वास्थ्य बीमा एवं पात्रता (Hindi)",
                },
                {
                  label: "What are the documents needed for PM-KISAN?",
                  sub: "Mandatory Aadhaar, land records & bank details",
                },
                {
                  label: "பிரதமர் கிசான் திட்டத்திற்கு எவ்வாறு விண்ணப்பிப்பது?",
                  sub: "விண்ணப்ப செயல்முறை மற்றும் இ-கேஒய்சி (Tamil)",
                },
              ].map((starter, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(starter.label)}
                  className="p-3 rounded-xl bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 hover:border-amber-500/40 transition-all text-left group"
                >
                  <p className="text-xs font-medium text-slate-200 group-hover:text-amber-300">
                    {starter.label}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {starter.sub}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 max-w-3xl ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}
              >
                {msg.role === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>

              {/* Message Body */}
              <div
                className={`flex-1 rounded-2xl p-4 shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-none'
                    : 'bg-slate-800/90 border border-slate-700/80 text-slate-100 rounded-tl-none'
                }`}
              >
                {/* Assistant Answer or User Text */}
                <div className="prose prose-invert prose-sm max-w-none text-xs md:text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                </div>

                {/* Assistant Controls: Audio TTS & Citations */}
                {msg.role === 'assistant' && (
                  <div className="mt-4 pt-3 border-t border-slate-700/60 flex flex-col gap-3">
                    {/* Read Aloud Button */}
                    <div className="flex items-center justify-between">
                      <button
                        onClick={() => handlePlayTTS(msg.content, msg.language, index)}
                        disabled={loadingAudioIndex === index}
                        className="flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 bg-amber-400/10 hover:bg-amber-400/20 px-2.5 py-1 rounded-lg border border-amber-400/20 transition-all font-medium"
                      >
                        {loadingAudioIndex === index ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Synthesizing voice...</span>
                          </>
                        ) : playingAudioIndex === index ? (
                          <>
                            <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                            <span className="text-rose-400">Stop Reading</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3.5 h-3.5" />
                            <span>Read Aloud (వినండి / सुनें)</span>
                          </>
                        )}
                      </button>

                      {msg.language && (
                        <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
                          Lang: {msg.language}
                        </span>
                      )}
                    </div>

                    {/* Verified Citations List */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-300">
                          <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                          <span>Official Sources & Citations:</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {msg.citations.map((citation, citIdx) => (
                            <CitationCard
                              key={citIdx}
                              citation={citation}
                              index={citIdx}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Suggested Follow-ups */}
                    {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                      <div className="mt-1 space-y-1.5">
                        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                          Suggested Questions:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.suggested_followups.map((followup, fIdx) => (
                            <button
                              key={fIdx}
                              onClick={() => onSendMessage(followup)}
                              className="text-xs text-left bg-slate-900/90 hover:bg-slate-700/80 text-amber-200/90 hover:text-white border border-slate-700 px-2.5 py-1 rounded-full transition-all"
                            >
                              + {followup}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator Bubble */}
        {isLoading && (
          <div className="flex gap-3 mr-auto max-w-xl">
            <div className="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 animate-bounce" />
            </div>
            <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl rounded-tl-none p-4 flex items-center gap-3">
              <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
              <div className="text-xs text-slate-300">
                <span>Searching verified policy documents & synthesizing answer...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-3 md:p-4 bg-slate-800/70 border-t border-slate-800">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          {/* Voice input mic component */}
          <VoiceRecorder
            onVoiceRecorded={onVoiceRecorded}
            disabled={isLoading}
          />

          {/* Text Input */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask a question in any regional language (e.g. రైతు భరోసా అర్హతలు? or पीएम किसान)..."
            className="flex-1 bg-slate-900 text-slate-100 placeholder-slate-500 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs md:text-sm focus:outline-none focus:border-amber-500/80 transition-all"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="p-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 active:scale-95 text-slate-950 font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-amber-500/20"
            title="Send query"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
