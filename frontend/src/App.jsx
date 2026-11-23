import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  FileText,
  Upload,
  Trash2,
  RefreshCw,
  Landmark,
  ShieldAlert,
  CheckCircle,
  HelpCircle,
  Info
} from 'lucide-react';
import ChatWindow from './components/ChatWindow';
import LanguageSelector from './components/LanguageSelector';
import {
  sendChatMessage,
  sendVoiceQuery,
  fetchSupportedLanguages,
  fetchIndexedDocuments,
  uploadPolicyDocument,
  deletePolicyDocument
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'docs'
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [languages, setLanguages] = useState([]);
  
  // Documents state
  const [documents, setDocuments] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState({ text: '', type: '' });
  const [customSchemeName, setCustomSchemeName] = useState('');

  // Initial load: languages & documents
  useEffect(() => {
    loadLanguages();
    loadDocuments();
  }, []);

  const loadLanguages = async () => {
    try {
      const data = await fetchSupportedLanguages();
      setLanguages(data);
    } catch (err) {
      console.error('Could not load languages list:', err);
      // Fallback languages list
      setLanguages([
        { code: 'te', name: 'Telugu', native: 'తెలుగు' },
        { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
        { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
        { code: 'bn', name: 'Bengali', native: 'বাংলা' },
        { code: 'mr', name: 'Marathi', native: 'मराठी' },
        { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
        { code: 'en', name: 'English', native: 'English' },
      ]);
    }
  };

  const loadDocuments = async () => {
    try {
      const data = await fetchIndexedDocuments();
      setDocuments(data.documents || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (err) {
      console.error('Could not load indexed documents:', err);
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Prepare recent conversation history
      const history = messages.slice(-4).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await sendChatMessage(text, selectedLanguage, history);

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations || [],
        language: response.language,
        suggested_followups: response.suggested_followups || [],
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = {
        role: 'assistant',
        content: `⚠️ Error retrieving information: ${err.message}. Please check your backend connection or configure your GEMINI_API_KEY.`,
        citations: [],
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceRecorded = async (audioBlob) => {
    setIsLoading(true);
    setUploadMessage({ text: 'Processing voice query with regional speech recognition...', type: 'info' });

    try {
      const response = await sendVoiceQuery(audioBlob, selectedLanguage);

      // Add user transcribed message
      const userMessage = {
        role: 'user',
        content: `🎙️ ${response.transcript}`,
        timestamp: new Date().toISOString(),
      };

      // Add assistant answer
      const assistantMessage = {
        role: 'assistant',
        content: response.chat_response.answer,
        citations: response.chat_response.citations || [],
        language: response.language,
        suggested_followups: response.chat_response.suggested_followups || [],
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
    } catch (err) {
      console.error('Voice query error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Voice query failed: ${err.message}. Try speaking clearly or use text input.`,
          citations: [],
        },
      ]);
    } finally {
      setIsLoading(false);
      setUploadMessage({ text: '', type: '' });
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadMessage({ text: 'Please select a valid PDF file.', type: 'error' });
      return;
    }

    setIsUploading(true);
    setUploadMessage({ text: `Indexing '${file.name}' into vector database...`, type: 'info' });

    try {
      const result = await uploadPolicyDocument(file, customSchemeName);
      setUploadMessage({ text: result.message, type: 'success' });
      setCustomSchemeName('');
      await loadDocuments();
    } catch (err) {
      setUploadMessage({ text: `Upload failed: ${err.message}`, type: 'error' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (filename) => {
    if (!window.confirm(`Delete document '${filename}' from vector database?`)) return;

    try {
      await deletePolicyDocument(filename);
      await loadDocuments();
      setUploadMessage({ text: `Deleted '${filename}' successfully.`, type: 'success' });
    } catch (err) {
      setUploadMessage({ text: `Delete failed: ${err.message}`, type: 'error' });
    }
  };

  const handleResetChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Header with subtle Indian Tricolor Ribbon */}
      <header className="relative border-b border-slate-800 bg-slate-900/90 backdrop-blur z-10 shrink-0">
        <div className="h-1 w-full bg-gradient-to-r from-amber-500 via-white to-emerald-500 opacity-80"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-amber-500/20">
              <Landmark className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm sm:text-base font-bold text-white tracking-tight">
                  Government Scheme & Policy Assistant
                </h1>
                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded font-mono font-medium">
                  Official Portal
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                బహుభాషా సంక్షేమ పథకాల సహాయకుడు • बहुभाषी सरकारी योजना सहायक • Multilingual Citizen RAG
              </p>
            </div>
          </div>

          {/* Controls: Language Selector & Tabs */}
          <div className="flex items-center gap-3">
            <LanguageSelector
              languages={languages}
              selectedLanguage={selectedLanguage}
              onSelectLanguage={setSelectedLanguage}
            />

            {/* Navigation Tabs */}
            <div className="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700">
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === 'chat'
                    ? 'bg-amber-500 text-slate-950 shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Citizen Chat</span>
              </button>

              <button
                onClick={() => setActiveTab('docs')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === 'docs'
                    ? 'bg-amber-500 text-slate-950 shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Policy PDFs ({documents.length})</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-4 md:p-6 overflow-hidden flex flex-col">
        {activeTab === 'chat' ? (
          <div className="flex-1 h-full overflow-hidden">
            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              onSendMessage={handleSendMessage}
              onVoiceRecorded={handleVoiceRecorded}
              selectedLanguage={selectedLanguage}
              onSelectLanguage={setSelectedLanguage}
              languages={languages}
              onResetChat={handleResetChat}
            />
          </div>
        ) : (
          /* Policy Documents Management Tab */
          <div className="flex-1 overflow-y-auto space-y-6 max-w-4xl mx-auto w-full">
            {/* Header info */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-amber-400" />
                    Verified Government Policy Documents
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Upload official Central and State government policy PDFs. Text is extracted, chunked page-by-page, and stored with citations in ChromaDB.
                  </p>
                </div>
                <button
                  onClick={loadDocuments}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all"
                  title="Refresh list"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              {/* Upload Box */}
              <div className="border-2 border-dashed border-slate-700 rounded-xl p-6 text-center bg-slate-950/40">
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-xs font-medium text-slate-300">
                  Select official government scheme guideline PDF to upload
                </p>
                <p className="text-[11px] text-slate-500 mb-4">
                  e.g., PM-KISAN, Ayushman Bharat, PMAY, Rythu Bharosa guidelines
                </p>

                <div className="max-w-md mx-auto flex flex-col sm:flex-row gap-2">
                  <input
                    type="text"
                    value={customSchemeName}
                    onChange={(e) => setCustomSchemeName(e.target.value)}
                    placeholder="Optional scheme title (e.g. PM-KISAN)"
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                  />

                  <label className="cursor-pointer bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold px-4 py-1.5 rounded-lg text-xs transition-all flex items-center justify-center gap-1.5 shrink-0 shadow-md">
                    <span>{isUploading ? 'Indexing...' : 'Choose PDF'}</span>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileUpload}
                      disabled={isUploading}
                      className="hidden"
                    />
                  </label>
                </div>

                {uploadMessage.text && (
                  <div
                    className={`mt-4 text-xs p-2.5 rounded-lg flex items-center justify-center gap-2 ${
                      uploadMessage.type === 'error'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : uploadMessage.type === 'success'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    }`}
                  >
                    {uploadMessage.type === 'error' ? (
                      <ShieldAlert className="w-4 h-4" />
                    ) : (
                      <CheckCircle className="w-4 h-4" />
                    )}
                    <span>{uploadMessage.text}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Document List */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-200">
                  Currently Indexed Documents ({documents.length})
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  Total Vector Chunks: {totalChunks}
                </span>
              </div>

              {documents.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No documents indexed yet. Run <code className="bg-slate-800 px-1 py-0.5 rounded text-amber-400">python scripts/ingest_policies.py</code> or upload a PDF above.
                </div>
              ) : (
                <div className="divide-y divide-slate-800">
                  {documents.map((doc, idx) => (
                    <div
                      key={idx}
                      className="py-3 flex items-center justify-between gap-4"
                    >
                      <div className="flex items-center gap-3 overflow-hidden">
                        <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="truncate">
                          <p className="text-xs font-semibold text-slate-200 truncate">
                            {doc.filename}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-400">
                            <span>{doc.chunks_count} vector chunks</span>
                            <span>•</span>
                            <span>{doc.pages_count || 1} pages</span>
                            {doc.schemes && doc.schemes.length > 0 && (
                              <>
                                <span>•</span>
                                <span className="text-amber-400 truncate">
                                  {doc.schemes.join(', ')}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteDocument(doc.filename)}
                        className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all shrink-0"
                        title="Delete document from vector DB"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
