import React, { useState, useEffect } from 'react';
import { 
  Plus, Trash2, ExternalLink, Globe, 
  CheckCircle2, AlertCircle, Search, RefreshCw, Star,
  Sparkles
} from 'lucide-react';
import type { Competitor, DiscoveredApp } from '../types';
import { api } from '../api';

interface CompetitorsManagerProps {
  projectId: string;
  onCompetitorChange?: () => void;
}

export const CompetitorsManager: React.FC<CompetitorsManagerProps> = ({ projectId, onCompetitorChange }) => {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  
  // Auto-discovery States
  const [discoveredList, setDiscoveredList] = useState<DiscoveredApp[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const [customSearchQuery, setCustomSearchQuery] = useState('');

  // New Competitor Form State
  const [name, setName] = useState('');
  const [playstorePackage, setPlaystorePackage] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [extraUrls, setExtraUrls] = useState<string[]>(['']);
  const [adding, setAdding] = useState(false);

  // Live Preview States
  const [previewingPlaystore, setPreviewingPlaystore] = useState(false);
  const [playstorePreviewData, setPlaystorePreviewData] = useState<any>(null);
  const [previewingWeb, setPreviewingWeb] = useState(false);
  const [webPreviewData, setWebPreviewData] = useState<any>(null);

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadCompetitors();
  }, [projectId]);

  const loadCompetitors = async () => {
    try {
      const data = await api.getCompetitors(projectId);
      setCompetitors(data);
    } catch (err: any) {
      showToast(err.message || 'Gagal memuat kompetitor', 'error');
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleDiscoverPreview = async () => {
    try {
      setDiscovering(true);
      const results = await api.discoverCompetitorsPreview(projectId, customSearchQuery);
      setDiscoveredList(results);
      if (results.length === 0) {
        showToast('Tidak ada aplikasi kompetitor baru yang ditemukan di Play Store', 'error');
      } else {
        showToast(`Ditemukan ${results.length} kandidat aplikasi kompetitor di Play Store.`, 'success');
      }
    } catch (err: any) {
      showToast(err.message || 'Gagal mencari kompetitor', 'error');
    } finally {
      setDiscovering(false);
    }
  };

  const handleAddDiscoveredApp = async (app: DiscoveredApp) => {
    try {
      setAdding(true);
      const details = await api.previewPlayStore(app.package_name).catch(() => ({}));
      const website = details?.website || '';

      await api.addCompetitor({
        project_id: projectId,
        name: app.title,
        playstore_package: app.package_name,
        website_url: website,
        extra_urls: []
      });

      setDiscoveredList(prev => prev.filter(a => a.package_name !== app.package_name));
      showToast(`Kompetitor "${app.title}" berhasil ditambahkan ke riset.`, 'success');
      await loadCompetitors();
      if (onCompetitorChange) onCompetitorChange();
    } catch (err: any) {
      showToast(err.message || 'Gagal menambahkan kompetitor', 'error');
    } finally {
      setAdding(false);
    }
  };

  const handleAddAllDiscovered = async () => {
    try {
      setDiscovering(true);
      const updated = await api.autoDiscoverCompetitors(projectId, customSearchQuery, 3);
      setCompetitors(updated);
      setDiscoveredList([]);
      showToast('Seluruh kompetitor otomatis berhasil didaftarkan.', 'success');
      if (onCompetitorChange) onCompetitorChange();
    } catch (err: any) {
      showToast(err.message || 'Gagal menambahkan kompetitor otomatis', 'error');
    } finally {
      setDiscovering(false);
    }
  };

  const handleTestPlaystore = async () => {
    if (!playstorePackage.trim()) {
      showToast('Masukkan Package Name Play Store terlebih dahulu', 'error');
      return;
    }
    try {
      setPreviewingPlaystore(true);
      setPlaystorePreviewData(null);
      const data = await api.previewPlayStore(playstorePackage.trim());
      setPlaystorePreviewData(data);
      if (data.title && !name) {
        setName(data.title);
      }
      showToast('Berhasil terhubung ke Play Store.', 'success');
    } catch (err: any) {
      showToast('Aplikasi tidak ditemukan di Google Play Store', 'error');
    } finally {
      setPreviewingPlaystore(false);
    }
  };

  const handleTestWeb = async () => {
    if (!websiteUrl.trim()) {
      showToast('Masukkan URL Website terlebih dahulu', 'error');
      return;
    }
    try {
      setPreviewingWeb(true);
      setWebPreviewData(null);
      const data = await api.previewWebsite(websiteUrl.trim());
      setWebPreviewData(data);
      showToast('Berhasil mengambil data website.', 'success');
    } catch (err: any) {
      showToast('Gagal mengakses website kompetitor', 'error');
    } finally {
      setPreviewingWeb(false);
    }
  };

  const handleAddCompetitor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      showToast('Nama kompetitor wajib diisi', 'error');
      return;
    }

    try {
      setAdding(true);
      const filteredExtras = extraUrls.map(u => u.trim()).filter(Boolean);
      await api.addCompetitor({
        project_id: projectId,
        name: name.trim(),
        playstore_package: playstorePackage.trim(),
        website_url: websiteUrl.trim(),
        extra_urls: filteredExtras,
      });

      showToast(`Kompetitor "${name}" berhasil ditambahkan.`, 'success');
      setName('');
      setPlaystorePackage('');
      setWebsiteUrl('');
      setExtraUrls(['']);
      setPlaystorePreviewData(null);
      setWebPreviewData(null);
      await loadCompetitors();
      if (onCompetitorChange) onCompetitorChange();
    } catch (err: any) {
      showToast(err.message || 'Gagal menambahkan kompetitor', 'error');
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteCompetitor = async (id: string, compName: string) => {
    if (!confirm(`Hapus kompetitor "${compName}" dari riset?`)) return;
    try {
      await api.deleteCompetitor(id);
      showToast(`Kompetitor "${compName}" dihapus.`, 'success');
      await loadCompetitors();
      if (onCompetitorChange) onCompetitorChange();
    } catch (err: any) {
      showToast(err.message || 'Gagal menghapus kompetitor', 'error');
    }
  };

  const handleClearAllCompetitors = async () => {
    if (!confirm('Hapus seluruh daftar kompetitor di proyek ini?')) return;
    try {
      await api.clearCompetitors(projectId);
      showToast('Seluruh kompetitor berhasil dihapus.', 'success');
      await loadCompetitors();
      if (onCompetitorChange) onCompetitorChange();
    } catch (err: any) {
      showToast(err.message || 'Gagal menghapus seluruh kompetitor', 'error');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-7 pb-16">
      
      {/* Toast Notification */}
      {toast && (
        <div className={`p-3.5 rounded-xl flex items-center gap-3 text-xs font-semibold shadow-xs ${
          toast.type === 'success' ? 'bg-[#EBFBF8] text-[#0F766E] border border-[#1ACAB6]/30' : 'bg-[#FDF3F2] text-[#B91C1C] border border-[#E33723]/30'
        }`}>
          {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-[#0D9488]" /> : <AlertCircle className="w-4 h-4 text-[#E33723]" />}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Globe className="w-4 h-4 text-[#0D9488]" />
          Kelola Daftar Aplikasi Kompetitor
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Daftarkan kompetitor pasar yang ingin Anda amati. Sistem akan otomatis membedah ulasan Play Store, changelog rilis, dan konten resmi website.
        </p>
      </div>

      {/* Auto-Discovery Quick Card */}
      <div className="bg-gradient-to-br from-[#EBFBF8]/60 to-white p-6 rounded-2xl border border-[#1ACAB6]/30 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1 rounded bg-[#0D9488]/10 text-[#0D9488]">
                <Sparkles className="w-3.5 h-3.5" />
              </span>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Pencarian Otomatis Kompetitor Play Store
              </h3>
              <span className="px-1.5 py-0.2 bg-[#0D9488] text-white text-[9px] font-bold rounded uppercase tracking-wider">
                Cepat & Akurat
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Sistem akan memindai Google Play Store dan menemukan aplikasi sejenis yang paling relevan dengan profil aplikasi internal Anda.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleDiscoverPreview}
              disabled={discovering}
              className="px-3.5 py-1.5 bg-[#0D9488] hover:bg-[#0F766E] text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition disabled:opacity-50"
            >
              {discovering ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
                  <span>Mencari...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>Cari Rekomendasi Play Store</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Optional Custom Keyword Input */}
        <div className="flex items-center gap-2 pt-1">
          <input
            type="text"
            value={customSearchQuery}
            onChange={(e) => setCustomSearchQuery(e.target.value)}
            placeholder="Kata kunci pencarian khusus (opsional, default memakai kategori profil internal)..."
            className="flex-1 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-600"
          />
        </div>

        {/* Discovered Apps Results */}
        {discoveredList.length > 0 && (
          <div className="pt-3 border-t border-slate-200/60 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800">
                Aplikasi Sejenis Terdeteksi ({discoveredList.length})
              </span>
              <button
                type="button"
                onClick={handleAddAllDiscovered}
                disabled={discovering}
                className="text-xs text-teal-700 hover:text-teal-900 font-semibold flex items-center gap-1"
              >
                <Plus className="w-3 h-3" />
                Tambahkan Semua ke Riset
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {discoveredList.map((app) => (
                <div
                  key={app.package_name}
                  className="bg-white border border-slate-200 rounded-xl p-3.5 flex items-start gap-3 shadow-xs hover:border-[#1ACAB6] transition"
                >
                  {app.icon ? (
                    <img src={app.icon} alt={app.title} className="w-11 h-11 rounded-xl border border-slate-100 object-cover shrink-0" />
                  ) : (
                    <div className="w-11 h-11 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0">
                      <Globe className="w-5 h-5 text-slate-400" />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-1">
                      <h4 className="font-bold text-slate-900 text-xs truncate" title={app.title}>
                        {app.title}
                      </h4>
                      <span className="flex items-center gap-0.5 text-amber-700 font-semibold bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200 text-[10px] shrink-0">
                        <Star className="w-2.5 h-2.5 fill-amber-500 text-amber-500" />
                        {app.score}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-500 truncate">{app.developer}</p>
                    <p className="text-[10px] text-slate-400 font-mono truncate">{app.package_name} • {app.installs} unduhan</p>

                    <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-slate-100">
                      <a
                        href={app.playstore_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[11px] text-slate-500 hover:text-teal-700 flex items-center gap-0.5"
                      >
                        Play Store <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                      <button
                        type="button"
                        onClick={() => handleAddDiscoveredApp(app)}
                        disabled={adding}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-[#0D9488] text-slate-700 hover:text-white rounded-lg text-[11px] font-semibold flex items-center gap-1 transition"
                      >
                        <Plus className="w-3 h-3" />
                        Tambah ke Riset
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Add Competitor Form */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-1.5">
          <Plus className="w-4 h-4 text-[#0D9488]" />
          Tambah Kompetitor Baru
        </h3>

        <form onSubmit={handleAddCompetitor} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Competitor Name */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">Nama Kompetitor *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Contoh: Astro, Alfagift, Shopee"
                className="w-full px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-600 text-xs font-medium"
              />
            </div>

            {/* Play Store Package Name with Test Button */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                ID Google Play Store (Package Name)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={playstorePackage}
                  onChange={(e) => setPlaystorePackage(e.target.value)}
                  placeholder="Contoh: com.astronauts.app"
                  className="flex-1 px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-600 text-xs font-mono"
                />
                <button
                  type="button"
                  onClick={handleTestPlaystore}
                  disabled={previewingPlaystore}
                  className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 flex items-center gap-1 transition"
                  title="Uji koneksi ke Play Store"
                >
                  <Search className="w-3.5 h-3.5 text-slate-500" />
                  {previewingPlaystore ? 'Mengecek...' : 'Cek App'}
                </button>
              </div>
            </div>

          </div>

          {/* Play Store Live Preview Card */}
          {playstorePreviewData && (
            <div className="bg-slate-50/70 border border-slate-200 rounded-xl p-3.5 flex items-start gap-3 text-xs">
              {playstorePreviewData.icon && (
                <img src={playstorePreviewData.icon} alt="icon" className="w-10 h-10 rounded-lg border border-slate-200 shrink-0" />
              )}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900">{playstorePreviewData.title}</span>
                  <span className="flex items-center gap-0.5 text-amber-700 font-semibold bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200 text-[11px]">
                    <Star className="w-3 h-3 fill-amber-500 text-amber-500" /> {playstorePreviewData.score}
                  </span>
                  <span className="text-slate-500 text-[11px]">({playstorePreviewData.ratings} ratings)</span>
                </div>
                <p className="text-slate-600 line-clamp-1 mt-0.5 text-[11px]">{playstorePreviewData.summary}</p>
                {playstorePreviewData.recent_changes && (
                  <p className="text-teal-700 line-clamp-1 mt-0.5 text-[11px]">
                    <strong>Changelog:</strong> {playstorePreviewData.recent_changes}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Website URL with Test Button */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
              Website Resmi Perusahaan
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="Contoh: https://astronauts.id"
                className="flex-1 px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-600 text-xs"
              />
              <button
                type="button"
                onClick={handleTestWeb}
                disabled={previewingWeb}
                className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 flex items-center gap-1 transition"
                title="Uji akses ke website"
              >
                <Search className="w-3.5 h-3.5 text-slate-500" />
                {previewingWeb ? 'Mengecek...' : 'Cek Web'}
              </button>
            </div>
          </div>

          {/* Web Preview Card */}
          {webPreviewData && (
            <div className="bg-slate-50/70 border border-slate-200 rounded-xl p-3 text-xs space-y-1">
              <div className="font-bold text-slate-800 text-[11px]">{webPreviewData.title || webPreviewData.url}</div>
              <p className="text-slate-600 text-[11px]">{webPreviewData.meta_description || 'Konten berhasil diambil'}</p>
            </div>
          )}

          {/* Extra URLs */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
              Tautan Tambahan (Press Release, Artikel Fitur Baru, atau Changelog Tambahan)
            </label>
            {extraUrls.map((url, idx) => (
              <div key={idx} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={url}
                  onChange={(e) => {
                    const updated = [...extraUrls];
                    updated[idx] = e.target.value;
                    setExtraUrls(updated);
                  }}
                  placeholder="https://artikel-berita.com/fitur-baru"
                  className="flex-1 px-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:ring-1 focus:ring-teal-600"
                />
                {extraUrls.length > 1 && (
                  <button
                    type="button"
                    onClick={() => {
                      const updated = extraUrls.filter((_, i) => i !== idx);
                      setExtraUrls(updated);
                    }}
                    className="p-1.5 text-slate-400 hover:text-rose-600"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => setExtraUrls([...extraUrls, ''])}
              className="text-[11px] text-teal-700 hover:text-teal-900 font-semibold flex items-center gap-1"
            >
              <Plus className="w-3 h-3" />
              Tambah Link Eksternal
            </button>
          </div>

          <div className="pt-2 border-t border-slate-100 flex justify-end">
            <button
              type="submit"
              disabled={adding}
              className="px-4 py-1.5 bg-[#0D9488] hover:bg-[#0F766E] text-white rounded-lg text-xs font-semibold shadow-xs transition disabled:opacity-50"
            >
              {adding ? 'Menyimpan...' : 'Simpan Kompetitor'}
            </button>
          </div>
        </form>
      </div>

      {/* Competitors List */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Kompetitor Terdaftar ({competitors.length})
          </h3>
          <div className="flex items-center gap-3">
            {competitors.length > 0 && (
              <button
                onClick={handleClearAllCompetitors}
                className="text-rose-600 hover:text-rose-800 text-xs font-semibold flex items-center gap-1 transition"
                title="Hapus semua kompetitor terdaftar"
              >
                <Trash2 className="w-3 h-3" /> Hapus Semua
              </button>
            )}
            <button
              onClick={loadCompetitors}
              className="text-slate-500 hover:text-teal-700 text-xs font-medium flex items-center gap-1 transition"
            >
              <RefreshCw className="w-3 h-3" /> Refresh
            </button>
          </div>
        </div>

        {competitors.length === 0 ? (
          <div className="py-10 text-center text-slate-400 text-xs">
            Belum ada kompetitor yang didaftarkan.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {competitors.map((comp) => (
              <div
                key={comp.id}
                className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 flex flex-col justify-between hover:border-slate-300 transition"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <h4 className="font-bold text-slate-900 text-xs">{comp.name}</h4>
                    <button
                      onClick={() => handleDeleteCompetitor(comp.id, comp.name)}
                      className="text-slate-400 hover:text-rose-600 p-1"
                      title="Hapus Kompetitor"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="mt-2.5 space-y-1 text-xs">
                    {comp.playstore_package && (
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <span className="text-[11px] text-slate-400 w-16">Play Store:</span>
                        <a
                          href={`https://play.google.com/store/apps/details?id=${comp.playstore_package}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-teal-700 hover:underline flex items-center gap-0.5 truncate text-[11px] font-medium"
                        >
                          {comp.playstore_package}
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    )}

                    {comp.website_url && (
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <span className="text-[11px] text-slate-400 w-16">Website:</span>
                        <a
                          href={comp.website_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-teal-700 hover:underline flex items-center gap-0.5 truncate text-[11px] font-medium"
                        >
                          {comp.website_url}
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};
