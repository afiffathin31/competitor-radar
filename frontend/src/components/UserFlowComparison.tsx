import React from 'react';
import { GitFork, AlertCircle, CheckCircle2, Smartphone, ShieldCheck } from 'lucide-react';
import type { FlowComparison } from '../types';

interface UserFlowComparisonProps {
  flowComparisons: FlowComparison[];
}

export const UserFlowComparison: React.FC<UserFlowComparisonProps> = ({ flowComparisons }) => {
  if (!flowComparisons || flowComparisons.length === 0) {
    return (
      <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-slate-400 text-xs">
        Belum ada data komparasi alur pengguna.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <GitFork className="w-4 h-4 text-[#0D9488]" />
          Komparasi Alur Pengguna (User Flow & Audit Friksi)
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Perbandingan langkah alur aplikasi internal terhadap pendekatan efisiensi kompetitor untuk mendeteksi redundansi dan potensi simplifikasi.
        </p>
      </div>

      <div className="space-y-5">
        {flowComparisons.map((fc) => (
          <div key={fc.id} className="bg-white rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] p-6 space-y-4">
            
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#0D9488]" />
                Modul Alur: {fc.flow_name}
              </h4>
            </div>

            {/* Side-by-side Flow Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Internal Flow */}
              <div className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4">
                <div className="flex items-center gap-2 text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  <Smartphone className="w-3.5 h-3.5 text-slate-400" />
                  Alur Aplikasi Internal Saat Ini
                </div>
                <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-line bg-white p-3 rounded-lg border border-slate-200/70">
                  {fc.internal_steps}
                </div>
              </div>

              {/* Competitor Streamlined Flow */}
              <div className="bg-[#FFF6EF]/60 border border-[#F77925]/25 rounded-xl p-4">
                <div className="flex items-center gap-2 text-[11px] font-bold text-[#C25510] uppercase tracking-wider mb-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#F77925]" />
                  Pendekatan Alur Cepat Kompetitor
                </div>
                <div className="text-xs text-slate-800 leading-relaxed whitespace-pre-line bg-white p-3 rounded-lg border border-[#F77925]/20 shadow-2xs">
                  {fc.competitor_detected_flow}
                </div>
              </div>

            </div>

            {/* Friction Points Callout (Coral Accent) */}
            <div className="bg-[#FDF3F2] border border-[#E33723]/25 rounded-xl p-3.5 flex items-start gap-3">
              <AlertCircle className="w-4 h-4 text-[#E33723] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[11px] font-bold text-[#B91C1C] uppercase tracking-wider block">
                  Titik Hambatan (UX Friction Points):
                </strong>
                <p className="text-xs text-[#991B1B] mt-1 leading-relaxed">
                  {fc.friction_points}
                </p>
              </div>
            </div>

            {/* Simplification Recommendation (Teal Accent) */}
            <div className="bg-[#EBFBF8] border border-[#1ACAB6]/30 rounded-xl p-3.5 flex items-start gap-3">
              <CheckCircle2 className="w-4 h-4 text-[#0D9488] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[11px] font-bold text-[#0F766E] uppercase tracking-wider block">
                  Rekomendasi Simplifikasi Alur:
                </strong>
                <p className="text-xs text-[#115E59] mt-1 leading-relaxed">
                  {fc.simplification_recommendation}
                </p>
              </div>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
};
