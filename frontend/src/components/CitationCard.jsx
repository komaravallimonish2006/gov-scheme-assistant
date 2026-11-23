import React, { useState } from 'react';
import { FileText, ChevronRight, ChevronDown, CheckCircle2 } from 'lucide-react';

export default function CitationCard({ citation, index }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-lg p-2.5 transition-all text-xs">
      <div 
        className="flex items-center justify-between cursor-pointer select-none gap-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="w-5 h-5 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
            <FileText className="w-3.5 h-3.5" />
          </div>
          <div className="truncate">
            <span className="font-semibold text-slate-200 truncate block">
              {citation.document_name}
            </span>
            {citation.scheme_name && (
              <span className="text-[10px] text-amber-400/90 block truncate">
                {citation.scheme_name}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded text-[10px] font-mono font-medium">
            Page {citation.page_number}
          </span>
          {citation.confidence_score && (
            <span className="text-emerald-400 text-[10px] hidden sm:inline-flex items-center gap-0.5">
              <CheckCircle2 className="w-3 h-3" />
              {Math.round(citation.confidence_score * 100)}% match
            </span>
          )}
          {isExpanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-2 pt-2 border-t border-slate-700/60 text-slate-300 text-[11px] leading-relaxed bg-slate-900/50 p-2 rounded">
          <p className="italic">"{citation.snippet}"</p>
          <div className="mt-1.5 flex justify-between items-center text-[10px] text-slate-400">
            <span>Verified Official Government Excerpt</span>
            <span className="text-blue-400 font-mono">Page {citation.page_number}</span>
          </div>
        </div>
      )}
    </div>
  );
}
