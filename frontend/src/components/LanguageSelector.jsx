import React from 'react';
import { Languages, ChevronDown } from 'lucide-react';

export default function LanguageSelector({
  languages,
  selectedLanguage,
  onSelectLanguage,
}) {
  return (
    <div className="relative inline-flex items-center">
      <div className="flex items-center gap-2 bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700 rounded-lg px-3 py-1.5 transition-all shadow-sm">
        <Languages className="w-4 h-4 text-amber-400" />
        <select
          value={selectedLanguage}
          onChange={(e) => onSelectLanguage(e.target.value)}
          className="bg-transparent text-sm text-slate-100 font-medium focus:outline-none cursor-pointer pr-2"
        >
          <option value="auto" className="bg-slate-800 text-slate-100">
            🌐 Auto-Detect Language (స్వయంచాలక)
          </option>
          {languages.map((lang) => (
            <option
              key={lang.code}
              value={lang.code}
              className="bg-slate-800 text-slate-100"
            >
              {lang.native} ({lang.name})
            </option>
          ))}
        </select>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 pointer-events-none" />
      </div>
    </div>
  );
}
