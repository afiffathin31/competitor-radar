import React, { useState } from 'react';
import { 
  Plus, Download, Settings, 
  Layers, Smartphone, Users, ChevronDown, 
  FileSpreadsheet, FileText, Printer, Compass
} from 'lucide-react';
import type { Project, AnalysisReport } from '../types';
import { api } from '../api';

interface NavbarProps {
  projects: Project[];
  activeProject: Project | null;
  onSelectProject: (p: Project) => void;
  activeTab: 'analysis' | 'internal' | 'competitors' | 'settings';
  setActiveTab: (tab: 'analysis' | 'internal' | 'competitors' | 'settings') => void;
  onOpenNewProject: () => void;
  onRunAnalysis: () => void;
  isAnalyzing: boolean;
  latestReport: AnalysisReport | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  projects,
  activeProject,
  onSelectProject,
  activeTab,
  setActiveTab,
  onOpenNewProject,
  onRunAnalysis,
  isAnalyzing,
  latestReport
}) => {
  const [showExportMenu, setShowExportMenu] = useState(false);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-3">
          
          {/* Brand Logo & Project Switcher */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Original Exact Logo Image */}
            <div className="flex items-center gap-2.5">
              <img 
                src="/logo.png" 
                alt="Logo" 
                className="w-8 h-8 rounded-lg object-contain shrink-0" 
              />
              <span className="text-sm font-bold tracking-tight text-slate-900 whitespace-nowrap">
                CompetitorRadar
              </span>
            </div>

            {/* Subtle Divider */}
            <div className="h-5 w-px bg-slate-200 shrink-0 hidden sm:block" />

            {/* Project Switcher */}
            <div className="flex items-center gap-1.5">
              <div className="relative">
                <select
                  value={activeProject?.id || ''}
                  onChange={(e) => {
                    const p = projects.find(item => item.id === e.target.value);
                    if (p) onSelectProject(p);
                  }}
                  title={activeProject?.title}
                  className="bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-semibold rounded-lg pl-2.5 pr-7 py-1.5 border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-600 transition w-36 sm:w-44 md:w-52 lg:w-56 truncate cursor-pointer appearance-none h-8"
                  style={{
                    backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2364748b' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                    backgroundPosition: `right 0.35rem center`,
                    backgroundRepeat: `no-repeat`,
                    backgroundSize: `1.2em 1.2em`
                  }}
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={onOpenNewProject}
                className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg border border-slate-200 transition shrink-0 h-8 w-8 flex items-center justify-center"
                title="Buat Proyek Baru"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Minimalist Navigation Tabs (Fit Segmented Control, No Wrapping) */}
          <nav className="hidden md:flex items-center bg-slate-100/90 p-1 rounded-xl border border-slate-200/80 space-x-1 shrink-0">
            <button
              onClick={() => setActiveTab('analysis')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all h-7 ${
                activeTab === 'analysis'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <Layers className="w-3.5 h-3.5 shrink-0" />
              <span>Matriks & Laporan</span>
            </button>

            <button
              onClick={() => setActiveTab('internal')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all h-7 ${
                activeTab === 'internal'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <Smartphone className="w-3.5 h-3.5 shrink-0" />
              <span>Aplikasi Internal</span>
            </button>

            <button
              onClick={() => setActiveTab('competitors')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all h-7 ${
                activeTab === 'competitors'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <Users className="w-3.5 h-3.5 shrink-0" />
              <span>Kompetitor</span>
              <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                activeTab === 'competitors' 
                  ? 'bg-slate-800 text-slate-200' 
                  : 'bg-slate-200/90 text-slate-700'
              }`}>
                {activeProject?.competitors_count || 0}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('settings')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all h-7 ${
                activeTab === 'settings'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <Settings className="w-3.5 h-3.5 shrink-0" />
              <span>API Provider</span>
            </button>
          </nav>

          {/* Action Buttons: Export & Run Research */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Export Dropdown */}
            {latestReport && (
              <div className="relative">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  className="flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 shadow-xs transition whitespace-nowrap h-8"
                >
                  <Download className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>Ekspor</span>
                  <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
                </button>

                {showExportMenu && (
                  <div className="absolute right-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-50 text-xs">
                    <a
                      href={api.getExportPdfUrl(latestReport.id)}
                      download
                      onClick={() => setShowExportMenu(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2.5 text-rose-700 hover:bg-rose-50/60 font-semibold transition"
                    >
                      <Download className="w-4 h-4 text-rose-600 shrink-0" />
                      <span>Unduh Dokumen PDF (.pdf)</span>
                    </a>
                    <a
                      href={api.getPrintHtmlUrl(latestReport.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => setShowExportMenu(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-slate-800 hover:bg-slate-50 font-medium transition"
                    >
                      <Printer className="w-4 h-4 text-slate-600 shrink-0" />
                      <span>Cetak / Pratinjau PDF</span>
                    </a>
                    <div className="my-1 border-t border-slate-100" />
                    <a
                      href={api.getExportExcelUrl(latestReport.id)}
                      download
                      onClick={() => setShowExportMenu(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-slate-700 hover:bg-slate-50 transition"
                    >
                      <FileSpreadsheet className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>Excel Spreadsheet (.xlsx)</span>
                    </a>
                    <a
                      href={api.getExportCsvUrl(latestReport.id)}
                      download
                      onClick={() => setShowExportMenu(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-slate-700 hover:bg-slate-50 transition"
                    >
                      <FileSpreadsheet className="w-4 h-4 text-teal-600 shrink-0" />
                      <span>Data CSV (.csv)</span>
                    </a>
                    <a
                      href={api.getExportMarkdownUrl(latestReport.id)}
                      download
                      onClick={() => setShowExportMenu(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-slate-700 hover:bg-slate-50 transition"
                    >
                      <FileText className="w-4 h-4 text-orange-600 shrink-0" />
                      <span>Markdown (.md)</span>
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* Run Analysis Button (Solid Teal Elegant Accent) */}
            <button
              onClick={onRunAnalysis}
              disabled={isAnalyzing || !activeProject}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all shadow-xs h-8 ${
                isAnalyzing
                  ? 'bg-slate-200 text-slate-500 cursor-not-allowed'
                  : 'bg-[#0D9488] hover:bg-[#0F766E] text-white'
              }`}
            >
              {isAnalyzing ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin shrink-0" />
                  <span>Menganalisis...</span>
                </>
              ) : (
                <>
                  <Compass className="w-3.5 h-3.5 shrink-0" />
                  <span>Jalankan Riset</span>
                </>
              )}
            </button>
          </div>

        </div>
      </div>
    </header>
  );
};
