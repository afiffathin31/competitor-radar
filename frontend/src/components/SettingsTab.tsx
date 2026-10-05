import React, { useState, useEffect } from 'react';
import { Settings, Key, CheckCircle2, ShieldAlert, Cpu, Globe, Layers } from 'lucide-react';
import type { AppSettings } from '../types';
import { api } from '../api';

export const SettingsTab: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [claudeKey, setClaudeKey] = useState('');
  const [qwenKey, setQwenKey] = useState('');
  const [qwenBaseUrl, setQwenBaseUrl] = useState('');
  const [qwenModel, setQwenModel] = useState('');
  const [defaultProvider, setDefaultProvider] = useState('gemini');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      setDefaultProvider(data.default_provider || 'gemini');
      if (data.qwen_base_url) setQwenBaseUrl(data.qwen_base_url);
      if (data.qwen_model) setQwenModel(data.qwen_model);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await api.updateSettings({
        gemini_api_key: geminiKey.trim(),
        openai_api_key: openaiKey.trim(),
        anthropic_api_key: claudeKey.trim(),
        qwen_api_key: qwenKey.trim(),
        qwen_base_url: qwenBaseUrl.trim(),
        qwen_model: qwenModel.trim(),
        default_provider: defaultProvider,
      });
      setToast({ message: 'Pengaturan API Key dan provider berhasil disimpan.', type: 'success' });
      setGeminiKey('');
      setOpenaiKey('');
      setClaudeKey('');
      setQwenKey('');
      await loadSettings();
    } catch (err: any) {
      setToast({ message: err.message || 'Gagal menyimpan pengaturan', type: 'error' });
    } finally {
      setSaving(false);
      setTimeout(() => setToast(null), 4000);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-16">
      
      {toast && (
        <div className={`p-3.5 rounded-xl flex items-center gap-3 text-xs font-semibold shadow-xs ${
          toast.type === 'success' ? 'bg-[#EBFBF8] text-[#0F766E] border border-[#1ACAB6]/30' : 'bg-[#FDF3F2] text-[#B91C1C] border border-[#E33723]/30'
        }`}>
          {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-[#0D9488]" /> : <ShieldAlert className="w-4 h-4 text-[#E33723]" />}
          <span>{toast.message}</span>
        </div>
      )}

      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Settings className="w-4 h-4 text-[#0D9488]" />
          Konfigurasi Model AI (Multi-Provider)
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Pilih provider analisis dan masukkan API Key Anda. Didukung Google Gemini, Qwen (Alibaba DashScope), OpenAI GPT-4o, dan Anthropic Claude.
        </p>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
        <form onSubmit={handleSave} className="space-y-6">
          
          {/* Provider Selection */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-2">
              Default AI Provider
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { id: 'gemini', name: 'Google Gemini', desc: 'Gemini 2.5 Flash / Pro' },
                { id: 'qwen', name: 'Qwen (Alibaba)', desc: 'Qwen 2.5 / Plus / Max' },
                { id: 'openai', name: 'OpenAI', desc: 'GPT-4o / GPT-4o-mini' },
                { id: 'claude', name: 'Anthropic Claude', desc: 'Claude 3.5 Sonnet' },
              ].map((p) => (
                <div
                  key={p.id}
                  onClick={() => setDefaultProvider(p.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    defaultProvider === p.id
                      ? 'border-[#0D9488] bg-[#EBFBF8] ring-1 ring-[#0D9488]'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">{p.name}</span>
                    <Cpu className={`w-3.5 h-3.5 ${defaultProvider === p.id ? 'text-[#0D9488]' : 'text-slate-400'}`} />
                  </div>
                  <p className="text-[11px] text-slate-500">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4 pt-4 border-t border-slate-100">
            {/* Qwen (Alibaba DashScope) */}
            <div className="bg-slate-50/60 p-4 rounded-xl border border-slate-200/80 space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-[#F77925]" />
                  Qwen API Configuration (DashScope)
                </label>
                {settings?.has_qwen && (
                  <span className="text-[10px] text-[#C25510] font-semibold bg-[#FFF6EF] px-2 py-0.5 rounded border border-[#F77925]/30">
                    Aktif ({settings.qwen_api_key_masked})
                  </span>
                )}
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  Qwen API Key (DashScope API Key)
                </label>
                <input
                  type="password"
                  value={qwenKey}
                  onChange={(e) => setQwenKey(e.target.value)}
                  placeholder={settings?.has_qwen ? 'Biarkan kosong jika tidak ingin mengubah' : 'sk-...'}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono focus:ring-1 focus:ring-teal-600 focus:outline-none bg-white"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <Globe className="w-3 h-3 text-slate-400" />
                    Base URL (Endpoint)
                  </label>
                  <input
                    type="text"
                    value={qwenBaseUrl}
                    onChange={(e) => setQwenBaseUrl(e.target.value)}
                    placeholder="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono focus:ring-1 focus:ring-teal-600 focus:outline-none bg-white"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Gunakan <code>dashscope-intl.aliyuncs.com</code> atau <code>dashscope.aliyuncs.com</code>
                  </span>
                </div>

                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <Layers className="w-3 h-3 text-slate-400" />
                    Model Name
                  </label>
                  <input
                    type="text"
                    value={qwenModel}
                    onChange={(e) => setQwenModel(e.target.value)}
                    placeholder="qwen-plus"
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono focus:ring-1 focus:ring-teal-600 focus:outline-none bg-white"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Contoh: <code>qwen-plus</code>, <code>qwen-max</code>, <code>qwen-turbo</code>
                  </span>
                </div>
              </div>
            </div>

            {/* Google Gemini */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                  <Key className="w-3 h-3 text-[#0D9488]" />
                  Google Gemini API Key
                </label>
                {settings?.has_gemini && (
                  <span className="text-[10px] text-[#0F766E] font-semibold bg-[#EBFBF8] px-2 py-0.5 rounded border border-[#1ACAB6]/30">
                    Aktif ({settings.gemini_api_key_masked})
                  </span>
                )}
              </div>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder={settings?.has_gemini ? 'Biarkan kosong jika tidak ingin mengubah' : 'AIzaSy...'}
                className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono focus:ring-1 focus:ring-teal-600 focus:outline-none"
              />
            </div>

            {/* OpenAI */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                  <Key className="w-3 h-3 text-emerald-600" />
                  OpenAI API Key
                </label>
                {settings?.has_openai && (
                  <span className="text-[10px] text-emerald-800 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Aktif ({settings.openai_api_key_masked})
                  </span>
                )}
              </div>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder={settings?.has_openai ? 'Biarkan kosong jika tidak ingin mengubah' : 'sk-...'}
                className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono focus:ring-1 focus:ring-teal-600 focus:outline-none"
              />
            </div>

            {/* Anthropic Claude */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                  <Key className="w-3 h-3 text-amber-600" />
                  Anthropic Claude API Key
                </label>
                {settings?.has_claude && (
                  <span className="text-[10px] text-amber-800 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Aktif ({settings.anthropic_api_key_masked})
                  </span>
                )}
              </div>
              <input
                type="password"
                value={claudeKey}
                onChange={(e) => setClaudeKey(e.target.value)}
                placeholder={settings?.has_claude ? 'Biarkan kosong jika tidak ingin mengubah' : 'sk-ant-...'}
                className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono focus:ring-1 focus:ring-teal-600 focus:outline-none"
              />
            </div>
          </div>

          <div className="bg-slate-50/70 p-3.5 rounded-xl text-xs text-slate-500 leading-relaxed border border-slate-200">
            <strong>Catatan Operasional:</strong> Jika API Key belum disetel atau perangkat sedang offline, sistem memiliki mesin analisis heuristik terintegrasi yang tetap menyintesis ulasan Play Store & web secara otomatis.
          </div>

          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-1.5 bg-[#0D9488] hover:bg-[#0F766E] text-white rounded-lg text-xs font-semibold shadow-xs transition disabled:opacity-50"
            >
              {saving ? 'Menyimpan...' : 'Simpan Konfigurasi'}
            </button>
          </div>

        </form>
      </div>

    </div>
  );
};
