import React, { useState, useEffect } from 'react';
import { 
  Save, Download, Upload, Plus, Trash2, Smartphone, 
  Layers, GitFork, AlertCircle, CheckCircle2, Compass, Sparkles
} from 'lucide-react';
import type { InternalAppProfile } from '../types';
import { api } from '../api';

interface InternalAppFormProps {
  projectId: string;
  onStartResearch?: () => void;
}

export const InternalAppForm: React.FC<InternalAppFormProps> = ({ projectId, onStartResearch }) => {
  const [profile, setProfile] = useState<InternalAppProfile>({
    project_id: projectId,
    app_name: '',
    category: '',
    description: '',
    target_audience: '',
    modules_features: [],
    user_flows: [],
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadProfile();
  }, [projectId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await api.getInternalApp(projectId);
      if (data) {
        setProfile(data);
      } else {
        setProfile({
          project_id: projectId,
          app_name: '',
          category: '',
          description: '',
          target_audience: '',
          modules_features: [
            {
              module_name: 'Modul Utama',
              features: [{ name: '', description: '' }]
            }
          ],
          user_flows: [
            {
              flow_name: 'Alur Inti Aplikasi',
              steps: ['Buka aplikasi', 'Pilih menu utama', 'Selesaikan transaksi'],
              notes: ''
            }
          ],
        });
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile.app_name.trim()) {
      showToast('Nama aplikasi wajib diisi', 'error');
      return;
    }

    try {
      setSaving(true);
      await api.saveInternalApp({ ...profile, project_id: projectId });
      showToast('Profil aplikasi internal berhasil disimpan.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Gagal menyimpan profil', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndStartResearch = async () => {
    if (!profile.app_name.trim()) {
      showToast('Nama aplikasi wajib diisi', 'error');
      return;
    }

    try {
      setSaving(true);
      await api.saveInternalApp({ ...profile, project_id: projectId });
      showToast('Profil tersimpan. Membuka konfigurasi riset...', 'success');
      if (onStartResearch) {
        onStartResearch();
      }
    } catch (err: any) {
      showToast(err.message || 'Gagal menyimpan profil', 'error');
    } finally {
      setSaving(false);
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(profile, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `${profile.app_name || 'internal_app'}_profile.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleImportJson = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        setProfile({
          ...profile,
          app_name: json.app_name || profile.app_name,
          category: json.category || profile.category,
          description: json.description || profile.description,
          target_audience: json.target_audience || profile.target_audience,
          modules_features: json.modules_features || profile.modules_features,
          user_flows: json.user_flows || profile.user_flows,
        });
        showToast('File JSON profil berhasil diimpor.', 'success');
      } catch (err) {
        showToast('Format file JSON tidak valid', 'error');
      }
    };
    reader.readAsText(file);
  };

  // Module & Feature Handlers
  const addModule = () => {
    setProfile({
      ...profile,
      modules_features: [
        ...profile.modules_features,
        { module_name: `Modul Baru ${profile.modules_features.length + 1}`, features: [{ name: '', description: '' }] }
      ]
    });
  };

  const removeModule = (modIdx: number) => {
    const updated = [...profile.modules_features];
    updated.splice(modIdx, 1);
    setProfile({ ...profile, modules_features: updated });
  };

  const addFeature = (modIdx: number) => {
    const updated = [...profile.modules_features];
    updated[modIdx].features.push({ name: '', description: '' });
    setProfile({ ...profile, modules_features: updated });
  };

  const removeFeature = (modIdx: number, featIdx: number) => {
    const updated = [...profile.modules_features];
    updated[modIdx].features.splice(featIdx, 1);
    setProfile({ ...profile, modules_features: updated });
  };

  // Flow Handlers
  const addFlow = () => {
    setProfile({
      ...profile,
      user_flows: [
        ...profile.user_flows,
        { flow_name: `Alur ${profile.user_flows.length + 1}`, steps: ['Langkah 1'], notes: '' }
      ]
    });
  };

  const removeFlow = (flowIdx: number) => {
    const updated = [...profile.user_flows];
    updated.splice(flowIdx, 1);
    setProfile({ ...profile, user_flows: updated });
  };

  const addStep = (flowIdx: number) => {
    const updated = [...profile.user_flows];
    updated[flowIdx].steps.push(`Langkah ${updated[flowIdx].steps.length + 1}`);
    setProfile({ ...profile, user_flows: updated });
  };

  const removeStep = (flowIdx: number, stepIdx: number) => {
    const updated = [...profile.user_flows];
    updated[flowIdx].steps.splice(stepIdx, 1);
    setProfile({ ...profile, user_flows: updated });
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500">
        <div className="w-6 h-6 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        Memuat profil aplikasi internal...
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-7 pb-16">
      
      {/* Toast Notification */}
      {toast && (
        <div className={`p-3.5 rounded-xl flex items-center gap-3 text-xs font-semibold shadow-xs transition-all ${
          toast.type === 'success' ? 'bg-[#EBFBF8] text-[#0F766E] border border-[#1ACAB6]/30' : 'bg-[#FDF3F2] text-[#B91C1C] border border-[#E33723]/30'
        }`}>
          {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-[#0D9488]" /> : <AlertCircle className="w-4 h-4 text-[#E33723]" />}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header with Actions */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-[#0D9488]" />
            Profil Aplikasi Internal (Tolok Ukur Riset)
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Daftar fitur dan alur internal yang Anda daftarkan di sini menjadi acuan perbandingan otomatis bagi sistem.
          </p>
        </div>

        <div className="flex items-center gap-2 self-end md:self-auto">
          {/* Export JSON */}
          <button
            onClick={handleExportJson}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition"
            title="Download profil JSON"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            Export JSON
          </button>

          {/* Import JSON */}
          <label className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 cursor-pointer transition">
            <Upload className="w-3.5 h-3.5 text-slate-500" />
            Import JSON
            <input type="file" accept=".json" onChange={handleImportJson} className="hidden" />
          </label>

          {/* Save Profile Button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            {saving ? 'Menyimpan...' : 'Simpan Profil'}
          </button>

          {/* Save & Run Research CTA */}
          <button
            onClick={handleSaveAndStartResearch}
            disabled={saving}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[#0D9488] hover:bg-[#0F766E] text-white rounded-lg text-xs font-semibold shadow-xs transition disabled:opacity-50"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Simpan & Mulai Riset</span>
          </button>
        </div>
      </div>

      {/* Section 1: General Info */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-4">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-3">
          1. Informasi Umum Produk
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">Nama Aplikasi Internal *</label>
            <input
              type="text"
              value={profile.app_name}
              onChange={(e) => setProfile({ ...profile, app_name: e.target.value })}
              placeholder="Contoh: TokoKita Mobile"
              className="w-full px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-600 text-xs font-medium"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">Kategori Sektor</label>
            <input
              type="text"
              value={profile.category}
              onChange={(e) => setProfile({ ...profile, category: e.target.value })}
              placeholder="Contoh: E-Commerce, Fintech, Logistik"
              className="w-full px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-600 text-xs"
            />
          </div>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">Deskripsi Proposisi Nilai</label>
          <textarea
            rows={2}
            value={profile.description || ''}
            onChange={(e) => setProfile({ ...profile, description: e.target.value })}
            placeholder="Jelaskan proposisi nilai utama dan fungsi aplikasi internal saat ini..."
            className="w-full px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-600 text-xs leading-relaxed"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">Target Segmen Pengguna</label>
          <input
            type="text"
            value={profile.target_audience || ''}
            onChange={(e) => setProfile({ ...profile, target_audience: e.target.value })}
            placeholder="Contoh: Pelanggan retail perkotaan, UMKM"
            className="w-full px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-600 text-xs"
          />
        </div>
      </div>

      {/* Section 2: Modules & Features */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-[#0D9488]" />
              2. Daftar Modul & Fitur yang Sudah Dimiliki
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Fitur yang terdaftar di sini tidak akan diklasifikasikan sebagai gap baru oleh sistem riset.
            </p>
          </div>
          <button
            onClick={addModule}
            className="flex items-center gap-1 px-3 py-1 bg-[#EBFBF8] hover:bg-teal-50 text-[#0F766E] border border-[#1ACAB6]/30 rounded-lg text-xs font-semibold transition"
          >
            <Plus className="w-3.5 h-3.5" />
            Tambah Modul
          </button>
        </div>

        <div className="space-y-5">
          {profile.modules_features.map((mod, modIdx) => (
            <div key={modIdx} className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <input
                  type="text"
                  value={mod.module_name}
                  onChange={(e) => {
                    const updated = [...profile.modules_features];
                    updated[modIdx].module_name = e.target.value;
                    setProfile({ ...profile, modules_features: updated });
                  }}
                  placeholder="Nama Modul (misal: Pembayaran, Autentikasi)"
                  className="font-bold text-xs text-slate-900 bg-white px-3 py-1.5 rounded-lg border border-slate-300 focus:ring-1 focus:ring-teal-600 w-full max-w-sm"
                />
                <button
                  onClick={() => removeModule(modIdx)}
                  className="text-slate-400 hover:text-rose-600 p-1"
                  title="Hapus Modul"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Feature items */}
              <div className="space-y-2 pt-1">
                {mod.features.map((feat, featIdx) => (
                  <div key={featIdx} className="flex items-center gap-2 bg-white p-2 rounded-lg border border-slate-200">
                    <input
                      type="text"
                      value={feat.name}
                      onChange={(e) => {
                        const updated = [...profile.modules_features];
                        updated[modIdx].features[featIdx].name = e.target.value;
                        setProfile({ ...profile, modules_features: updated });
                      }}
                      placeholder="Nama Fitur (misal: Virtual Account)"
                      className="text-xs font-medium text-slate-900 w-1/3 px-2 py-1 rounded border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-600"
                    />
                    <input
                      type="text"
                      value={feat.description}
                      onChange={(e) => {
                        const updated = [...profile.modules_features];
                        updated[modIdx].features[featIdx].description = e.target.value;
                        setProfile({ ...profile, modules_features: updated });
                      }}
                      placeholder="Deskripsi singkat cara kerja..."
                      className="text-xs text-slate-600 flex-1 px-2 py-1 rounded border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-600"
                    />
                    <button
                      onClick={() => removeFeature(modIdx, featIdx)}
                      className="text-slate-400 hover:text-rose-500 p-1"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}

                <button
                  onClick={() => addFeature(modIdx)}
                  className="text-[11px] text-teal-700 hover:text-teal-900 font-semibold flex items-center gap-1 mt-1"
                >
                  <Plus className="w-3 h-3" />
                  Tambah Fitur di Modul Ini
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 3: User Flows */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <GitFork className="w-4 h-4 text-[#0D9488]" />
              3. Alur Pengguna (User Flow) Aplikasi
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Rincian tahapan langkah operasional yang ingin diaudit friksinya terhadap kompetitor.
            </p>
          </div>
          <button
            onClick={addFlow}
            className="flex items-center gap-1 px-3 py-1 bg-[#EBFBF8] hover:bg-teal-50 text-[#0F766E] border border-[#1ACAB6]/30 rounded-lg text-xs font-semibold transition"
          >
            <Plus className="w-3.5 h-3.5" />
            Tambah Alur
          </button>
        </div>

        <div className="space-y-5">
          {profile.user_flows.map((flow, flowIdx) => (
            <div key={flowIdx} className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <input
                  type="text"
                  value={flow.flow_name}
                  onChange={(e) => {
                    const updated = [...profile.user_flows];
                    updated[flowIdx].flow_name = e.target.value;
                    setProfile({ ...profile, user_flows: updated });
                  }}
                  placeholder="Nama Alur (misal: Alur Checkout)"
                  className="font-bold text-xs text-slate-900 bg-white px-3 py-1.5 rounded-lg border border-slate-300 focus:ring-1 focus:ring-teal-600 w-full max-w-sm"
                />
                <button
                  onClick={() => removeFlow(flowIdx)}
                  className="text-slate-400 hover:text-rose-600 p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Steps */}
              <div className="space-y-2 pt-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Tahapan Langkah:</label>
                {flow.steps.map((step, stepIdx) => (
                  <div key={stepIdx} className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-slate-400 w-5 text-right">{stepIdx + 1}.</span>
                    <input
                      type="text"
                      value={step}
                      onChange={(e) => {
                        const updated = [...profile.user_flows];
                        updated[flowIdx].steps[stepIdx] = e.target.value;
                        setProfile({ ...profile, user_flows: updated });
                      }}
                      placeholder={`Langkah ${stepIdx + 1}`}
                      className="text-xs text-slate-800 flex-1 px-3 py-1.5 rounded-lg bg-white border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-600"
                    />
                    <button
                      onClick={() => removeStep(flowIdx, stepIdx)}
                      className="text-slate-400 hover:text-rose-500 p-1"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}

                <button
                  onClick={() => addStep(flowIdx)}
                  className="text-[11px] text-teal-700 hover:text-teal-900 font-semibold flex items-center gap-1 mt-1"
                >
                  <Plus className="w-3 h-3" />
                  Tambah Langkah
                </button>
              </div>

              {/* Notes */}
              <div className="pt-1">
                <input
                  type="text"
                  value={flow.notes || ''}
                  onChange={(e) => {
                    const updated = [...profile.user_flows];
                    updated[flowIdx].notes = e.target.value;
                    setProfile({ ...profile, user_flows: updated });
                  }}
                  placeholder="Catatan kendala atau keluhan pada alur ini (opsional)..."
                  className="text-xs text-slate-600 bg-white w-full px-3 py-1.5 rounded-lg border border-slate-200"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Sticky Action Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Sparkles className="w-4 h-4 text-[#0D9488]" />
          <span>Profil ini akan dijadikan tolok ukur gap analisis inovasi terhadap kompetitor.</span>
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold border border-slate-200 transition disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            {saving ? 'Menyimpan...' : 'Simpan Profil'}
          </button>

          <button
            onClick={handleSaveAndStartResearch}
            disabled={saving}
            className="flex items-center gap-1.5 px-5 py-2 bg-[#0D9488] hover:bg-[#0F766E] text-white rounded-xl text-xs font-semibold shadow-xs transition disabled:opacity-50"
          >
            <Compass className="w-4 h-4" />
            <span>Simpan & Mulai Riset Otomatis</span>
          </button>
        </div>
      </div>

    </div>
  );
};
