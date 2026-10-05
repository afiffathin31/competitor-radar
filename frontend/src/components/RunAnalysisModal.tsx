import React, { useState, useEffect } from 'react';
import { 
  X, Compass, Smartphone, CheckCircle2, Bot
} from 'lucide-react';
import type { Project, InternalAppProfile, AppSettings } from '../types';
import { api } from '../api';

interface RunAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  project: Project;
  internalApp: InternalAppProfile | null;
  competitorsCount: number;
  onRun: (options: {
    autoDiscover: boolean;
    discoverLimit: number;
    customKeywords: string;
    provider: string;
  }) => Promise<void>;
  isAnalyzing: boolean;
}

export const RunAnalysisModal: React.FC<RunAnalysisModalProps> = ({
  isOpen,
  onClose,
  project,
  internalApp,
  competitorsCount,
  onRun,
  isAnalyzing
}) => {
  const [autoDiscover, setAutoDiscover] = useState(true);
  const [discoverLimit, setDiscoverLimit] = useState(3);
  const [customKeywords, setCustomKeywords] = useState('');
  const [provider, setProvider] = useState('gemini');
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [progressStep, setProgressStep] = useState(1);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
      setProgressStep(1);
    }
  }, [isOpen]);

  useEffect(() => {
    let interval: any;
    if (isAnalyzing) {
      interval = setInterval(() => {
        setProgressStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 5000);
    } else {
      setProgressStep(1);
    }
    return () => clearInterval(interval);
  }, [isAnalyzing]);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      if (data.default_provider) {
        setProvider(data.default_provider);
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!isOpen) return null;

  const handleStart = async () => {
    await onRun({
      autoDiscover,
      discoverLimit,
      customKeywords: customKeywords.trim(),
      provider
    });
  };

  const stepsList = [
    { num: 1, title: 'Analisis Profil Internal', desc: 'Mengekstrak spesifikasi, modul & alur aplikasi' },
    { num: 2, title: 'Pencarian Play Store', desc: 'Menemukan 2-4 kompetitor sejenis terpopuler' },
    { num: 3, title: 'Pengambilan Ulasan & Web', desc: 'Mengunduh pujian, keluhan pengguna & situs resmi' },
    { num: 4, title: 'Sintesis AI & Matriks Gap', desc: 'Memetakan inovasi, skor prioritas & user flow' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden transition-all">
        
        {/* Top Header Bar */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-[#EBFBF8] text-[#0D9488]">
              <Compass className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Jalankan Riset & Analisis Kompetitor</h3>
              <p className="text-[11px] text-slate-500">Konfigurasi sumber data dan mesin intelijen kompetitor</p>
            </div>
          </div>
          {!isAnalyzing && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 text-xs text-slate-700 max-h-[75vh] overflow-y-auto">
          
          {/* Internal App Reference Card */}
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1">
                <Smartphone className="w-3 h-3 text-[#0D9488]" /> Baseline Aplikasi Internal
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#EBFBF8] text-[#0F766E] border border-[#1ACAB6]/30">
                {internalApp?.category || project.category || 'General'}
              </span>
            </div>
            <div className="text-xs font-bold text-slate-900">
              {internalApp?.app_name || 'Aplikasi Belum Diberi Nama'}
            </div>
            <p className="text-[11px] text-slate-500 line-clamp-2">
              {internalApp?.description || 'Silakan lengkapi profil aplikasi di tab Aplikasi Internal untuk perbandingan akurat.'}
            </p>
          </div>

          {/* Mode Selection */}
          <div className="space-y-3">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600">
              Sumber Penemuan Kompetitor
            </label>

            {/* Option A: Auto-Discovery (Recommended) */}
            <label
              className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition ${
                autoDiscover
                  ? 'bg-[#EBFBF8]/50 border-[#1ACAB6] shadow-xs'
                  : 'bg-white border-slate-200 hover:border-slate-300'
              }`}
            >
              <input
                type="radio"
                name="competitor_source"
                checked={autoDiscover}
                onChange={() => setAutoDiscover(true)}
                disabled={isAnalyzing}
                className="mt-0.5 text-[#0D9488] focus:ring-[#0D9488]"
              />
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 text-xs">Otomatis Temukan di Google Play Store</span>
                  <span className="px-1.5 py-0.5 bg-[#0D9488] text-white text-[9px] font-bold rounded uppercase tracking-wider">
                    Rekomendasi
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Sistem otomatis mencari 2-4 aplikasi sejenis teratas di Play Store berdasarkan kategori dan modul aplikasi Anda, lalu mengekstrak ulasan & situs resminya.
                </p>

                {/* Sub-options when autoDiscover is true */}
                {autoDiscover && (
                  <div className="pt-2 mt-2 border-t border-slate-200/60 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <span className="text-[10px] font-semibold text-slate-600 uppercase">Jumlah Kompetitor</span>
                      <select
                        value={discoverLimit}
                        onChange={(e) => setDiscoverLimit(Number(e.target.value))}
                        disabled={isAnalyzing}
                        className="mt-1 w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-semibold text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      >
                        <option value={2}>2 Kompetitor Teratas</option>
                        <option value={3}>3 Kompetitor Teratas (Ideal)</option>
                        <option value={4}>4 Kompetitor Teratas</option>
                      </select>
                    </div>

                    <div>
                      <span className="text-[10px] font-semibold text-slate-600 uppercase">Kata Kunci Khusus (Opsional)</span>
                      <input
                        type="text"
                        value={customKeywords}
                        onChange={(e) => setCustomKeywords(e.target.value)}
                        disabled={isAnalyzing}
                        placeholder="Contoh: haji umrah panduan"
                        className="mt-1 w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-600"
                      />
                    </div>
                  </div>
                )}
              </div>
            </label>

            {/* Option B: Manual Registered Competitors */}
            <label
              className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition ${
                !autoDiscover
                  ? 'bg-[#EBFBF8]/50 border-[#1ACAB6] shadow-xs'
                  : 'bg-white border-slate-200 hover:border-slate-300'
              }`}
            >
              <input
                type="radio"
                name="competitor_source"
                checked={!autoDiscover}
                onChange={() => setAutoDiscover(false)}
                disabled={isAnalyzing}
                className="mt-0.5 text-[#0D9488] focus:ring-[#0D9488]"
              />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-xs">Hanya Gunakan Kompetitor Terdaftar Manual</span>
                  <span className="text-[11px] font-semibold text-slate-500">
                    {competitorsCount} terdaftar
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Riset hanya akan memproses kompetitor spesifik yang sudah Anda input pada tab Kompetitor.
                </p>
              </div>
            </label>
          </div>

          {/* AI Provider Selector */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-slate-500" />
              Model AI Engine
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              disabled={isAnalyzing}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-600"
            >
              <option value="qwen">Qwen (Alibaba DashScope / OpenAI Compatible) {settings?.has_qwen ? '✓ Aktif' : ''}</option>
              <option value="gemini">Google Gemini 2.5 Flash {settings?.has_gemini ? '✓ Aktif' : ''}</option>
              <option value="openai">OpenAI GPT-4o {settings?.has_openai ? '✓ Aktif' : ''}</option>
              <option value="claude">Anthropic Claude 3.5 Sonnet {settings?.has_claude ? '✓ Aktif' : ''}</option>
            </select>
          </div>

          {/* Real-time Multi-step Progress indicator when isAnalyzing */}
          {isAnalyzing && (
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 flex items-center gap-2">
                  <div className="w-3.5 h-3.5 border-2 border-teal-600 border-t-transparent rounded-full animate-spin" />
                  Riset Sedang Berlangsung...
                </span>
                <span className="text-[11px] font-mono text-teal-700 font-semibold">
                  Tahap {progressStep}/4
                </span>
              </div>

              <div className="space-y-2 pt-1">
                {stepsList.map((s) => {
                  const isDone = progressStep > s.num;
                  const isCurrent = progressStep === s.num;
                  return (
                    <div key={s.num} className="flex items-start gap-2.5 text-[11px]">
                      <div className="mt-0.5">
                        {isDone ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                        ) : isCurrent ? (
                          <div className="w-3.5 h-3.5 rounded-full border-2 border-teal-600 border-t-transparent animate-spin" />
                        ) : (
                          <div className="w-3.5 h-3.5 rounded-full border border-slate-300 bg-white" />
                        )}
                      </div>
                      <div className="flex-1">
                        <span className={`font-semibold ${isCurrent ? 'text-teal-900 font-bold' : isDone ? 'text-slate-700' : 'text-slate-400'}`}>
                          {s.title}
                        </span>
                        <p className={`text-[10px] ${isCurrent ? 'text-teal-700' : 'text-slate-400'}`}>
                          {s.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>

        {/* Footer Action Buttons */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2.5">
          {!isAnalyzing && (
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-100 transition"
            >
              Batal
            </button>
          )}

          <button
            onClick={handleStart}
            disabled={isAnalyzing}
            className={`px-5 py-1.5 rounded-lg text-xs font-semibold text-white shadow-xs flex items-center gap-1.5 transition ${
              isAnalyzing
                ? 'bg-slate-300 cursor-not-allowed text-slate-500'
                : 'bg-[#0D9488] hover:bg-[#0F766E]'
            }`}
          >
            {isAnalyzing ? (
              <>
                <div className="w-3 h-3 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
                <span>Memproses Riset...</span>
              </>
            ) : (
              <>
                <Compass className="w-3.5 h-3.5" />
                <span>Mulai Riset Otomatis</span>
              </>
            )}
          </button>
        </div>

      </div>
    </div>
  );
};
