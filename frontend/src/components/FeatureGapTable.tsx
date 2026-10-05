import React, { useState } from 'react';
import { 
  ExternalLink, Search, MessageSquareQuote, Globe, Layers
} from 'lucide-react';
import type { FeatureGap } from '../types';
import { api } from '../api';

interface FeatureGapTableProps {
  gaps: FeatureGap[];
  onGapUpdated?: () => void;
}

export const FeatureGapTable: React.FC<FeatureGapTableProps> = ({ gaps, onGapUpdated }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const categories = Array.from(new Set(gaps.map((g) => g.category)));

  const filteredGaps = gaps.filter((item) => {
    const matchesSearch = 
      item.feature_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.innovation_highlight.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.competitor_name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || item.internal_status === statusFilter;
    const matchesCategory = categoryFilter === 'all' || item.category === categoryFilter;

    return matchesSearch && matchesStatus && matchesCategory;
  });

  const handleStatusChange = async (gapId: string, newStatus: any) => {
    try {
      await api.updateGapStatus(gapId, { internal_status: newStatus });
      if (onGapUpdated) onGapUpdated();
    } catch (err) {
      console.error('Gagal memperbarui status:', err);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Belum Diadaptasi':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#FDF3F2] text-[#B91C1C] border border-[#E33723]/25">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E33723]" />
            Belum Diadaptasi
          </span>
        );
      case 'Sebagian Diadaptasi':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#FFF6EF] text-[#C25510] border border-[#F77925]/25">
            <span className="w-1.5 h-1.5 rounded-full bg-[#F77925]" />
            Sebagian Diadaptasi
          </span>
        );
      case 'Sudah Setara':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#EBFBF8] text-[#0F766E] border border-[#1ACAB6]/30">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1ACAB6]" />
            Sudah Setara
          </span>
        );
      case 'Aplikasi Kita Unggul':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-800 border border-slate-300">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-700" />
            Kita Lebih Unggul
          </span>
        );
      default:
        return <span className="text-xs text-slate-600">{status}</span>;
    }
  };

  const getPriorityLabel = (impact: number, effort: number) => {
    if (impact >= 8 && effort <= 6) {
      return (
        <span className="inline-block px-2 py-0.5 rounded text-[11px] font-semibold bg-[#EBFBF8] text-[#0F766E] border border-[#1ACAB6]/30">
          Prioritas 1 · Quick Win
        </span>
      );
    } else if (impact >= 7 && effort >= 7) {
      return (
        <span className="inline-block px-2 py-0.5 rounded text-[11px] font-semibold bg-[#FFF6EF] text-[#C25510] border border-[#F77925]/30">
          Prioritas 2 · Strategis
        </span>
      );
    }
    return (
      <span className="text-slate-500 text-[11px]">
        Sekunder (Impact {impact} · Effort {effort})
      </span>
    );
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden">
      
      {/* Header & Filter Bar */}
      <div className="p-6 border-b border-slate-100 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#0D9488]" />
              Matriks Gap Inovasi Fitur Kompetitor
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Pemetaan fitur baru kompetitor yang belum diadopsi, lengkap dengan bukti sumber resmi dan tingkat prioritas.
            </p>
          </div>

          {/* Minimalist Search */}
          <div className="relative w-full md:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Cari fitur, modul, kompetitor..."
              className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-slate-300 text-xs focus:ring-1 focus:ring-teal-600 focus:outline-none transition"
            />
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
          <span className="text-slate-400 font-semibold text-[11px] uppercase tracking-wider mr-1">
            Status:
          </span>
          {['all', 'Belum Diadaptasi', 'Sebagian Diadaptasi', 'Sudah Setara', 'Aplikasi Kita Unggul'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                statusFilter === st
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {st === 'all' ? 'Semua' : st}
            </button>
          ))}

          {categories.length > 1 && (
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="ml-auto bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-700"
            >
              <option value="all">Semua Modul</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50/60 border-b border-slate-200/80 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4 font-semibold">Kompetitor</th>
              <th className="py-3 px-4 font-semibold">Fitur Inovatif</th>
              <th className="py-3 px-4 font-semibold">Status Internal</th>
              <th className="py-3 px-4 w-1/3 font-semibold">Highlight Inovasi</th>
              <th className="py-3 px-4 font-semibold">Prioritas</th>
              <th className="py-3 px-4 font-semibold">Bukti & Sitasi Resmi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredGaps.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400">
                  Tidak ada fitur yang sesuai dengan kriteria filter.
                </td>
              </tr>
            ) : (
              filteredGaps.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/50 transition">
                  {/* Competitor Name */}
                  <td className="py-3.5 px-4 font-bold text-slate-900 whitespace-nowrap">
                    {item.competitor_name}
                  </td>

                  {/* Feature & Category */}
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-900 text-xs">{item.feature_name}</div>
                    <span className="inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600">
                      {item.category}
                    </span>
                  </td>

                  {/* Status Dropdown */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <select
                      value={item.internal_status}
                      onChange={(e) => handleStatusChange(item.id, e.target.value)}
                      className="bg-transparent border-0 font-medium cursor-pointer focus:ring-0 text-xs p-0 text-slate-700"
                    >
                      <option value="Belum Diadaptasi">Belum Diadaptasi</option>
                      <option value="Sebagian Diadaptasi">Sebagian Diadaptasi</option>
                      <option value="Sudah Setara">Sudah Setara</option>
                      <option value="Aplikasi Kita Unggul">Kita Lebih Unggul</option>
                    </select>
                    <div className="mt-1">{getStatusBadge(item.internal_status)}</div>
                  </td>

                  {/* Highlight */}
                  <td className="py-3.5 px-4 text-slate-700 leading-relaxed text-xs">
                    {item.innovation_highlight}
                  </td>

                  {/* Priority / Impact */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <div>{getPriorityLabel(item.impact_score, item.effort_score)}</div>
                    <div className="text-[10px] text-slate-400 mt-1">
                      Dampak: {item.impact_score}/10 · Upaya: {item.effort_score}/10
                    </div>
                  </td>

                  {/* Official Sources */}
                  <td className="py-3.5 px-4 space-y-1.5 min-w-[200px]">
                    {item.official_sources?.map((s, sIdx) => (
                      <div key={sIdx} className="bg-slate-50/80 border border-slate-200/80 rounded p-1.5 text-[11px]">
                        <div className="flex items-center gap-1 font-medium text-slate-700">
                          {s.type === 'playstore_review' ? (
                            <MessageSquareQuote className="w-3 h-3 text-teal-600 shrink-0" />
                          ) : (
                            <Globe className="w-3 h-3 text-orange-600 shrink-0" />
                          )}
                          <a
                            href={s.url}
                            target="_blank"
                            rel="noreferrer"
                            className="hover:underline text-teal-700 font-semibold flex items-center gap-0.5 truncate"
                          >
                            {s.title}
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        </div>
                        {s.quote && (
                          <p className="text-slate-500 italic mt-0.5 line-clamp-2">
                            "{s.quote}"
                          </p>
                        )}
                      </div>
                    ))}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
};
