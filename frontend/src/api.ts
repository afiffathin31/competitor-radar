import type { 
  Project, InternalAppProfile, Competitor, DiscoveredApp,
  AnalysisReport, AppSettings 
} from './types';

const API_BASE = '/api';

export const api = {
  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Gagal memuat daftar proyek');
    return res.json();
  },

  async createProject(data: { title: string; category: string; description?: string }): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Gagal membuat proyek baru');
    return res.json();
  },

  async deleteProject(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Gagal menghapus proyek');
  },

  async updateProject(id: string, data: { title?: string; category?: string; description?: string }): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Gagal memperbarui proyek');
    return res.json();
  },

  // Internal App
  async getInternalApp(projectId: string): Promise<InternalAppProfile | null> {
    const res = await fetch(`${API_BASE}/internal-app/${projectId}`);
    if (!res.ok) throw new Error('Gagal memuat profil aplikasi internal');
    return res.json();
  },

  async saveInternalApp(data: InternalAppProfile): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/internal-app`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Gagal menyimpan profil aplikasi internal');
    return res.json();
  },

  async exportInternalAppJson(projectId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/internal-app/export-json/${projectId}`);
    if (!res.ok) throw new Error('Gagal mengekspor profil JSON');
    return res.json();
  },

  // Competitors
  async getCompetitors(projectId: string): Promise<Competitor[]> {
    const res = await fetch(`${API_BASE}/competitors/project/${projectId}`);
    if (!res.ok) throw new Error('Gagal memuat daftar kompetitor');
    return res.json();
  },

  async addCompetitor(data: {
    project_id: string;
    name: string;
    playstore_package: string;
    website_url: string;
    extra_urls: string[];
  }): Promise<Competitor> {
    const res = await fetch(`${API_BASE}/competitors`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Gagal menambahkan kompetitor');
    return res.json();
  },

  async deleteCompetitor(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/competitors/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Gagal menghapus kompetitor');
  },

  async clearCompetitors(projectId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/competitors/project/${projectId}/all`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Gagal menghapus seluruh kompetitor');
  },

  async previewPlayStore(packageName: string): Promise<any> {
    const res = await fetch(`${API_BASE}/competitors/preview/playstore?package_name=${encodeURIComponent(packageName)}`);
    if (!res.ok) throw new Error('Gagal mengambil preview Play Store');
    return res.json();
  },

  async previewWebsite(url: string): Promise<any> {
    const res = await fetch(`${API_BASE}/competitors/preview/website?url=${encodeURIComponent(url)}`);
    if (!res.ok) throw new Error('Gagal mengambil preview Website');
    return res.json();
  },

  async discoverCompetitorsPreview(projectId: string, query?: string, limit: number = 4): Promise<DiscoveredApp[]> {
    const params = new URLSearchParams({ project_id: projectId, limit: String(limit) });
    if (query) params.append('query', query);
    const res = await fetch(`${API_BASE}/competitors/discover-preview?${params.toString()}`);
    if (!res.ok) throw new Error('Gagal mencari rekomendasi kompetitor');
    return res.json();
  },

  async autoDiscoverCompetitors(projectId: string, query?: string, limit: number = 3): Promise<Competitor[]> {
    const res = await fetch(`${API_BASE}/competitors/auto-discover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, query, limit }),
    });
    if (!res.ok) throw new Error('Gagal menambahkan kompetitor otomatis');
    return res.json();
  },

  // Analysis
  async runAnalysis(
    projectId: string, 
    provider: string, 
    autoDiscover: boolean = true, 
    discoverLimit: number = 3, 
    customKeywords?: string
  ): Promise<AnalysisReport> {
    const res = await fetch(`${API_BASE}/analysis/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        project_id: projectId, 
        provider,
        auto_discover: autoDiscover,
        discover_limit: discoverLimit,
        custom_keywords: customKeywords
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Gagal menjalankan analisis' }));
      throw new Error(err.detail || 'Gagal menjalankan analisis');
    }
    return res.json();
  },

  async getLatestAnalysis(projectId: string): Promise<AnalysisReport | null> {
    const res = await fetch(`${API_BASE}/analysis/project/${projectId}/latest`);
    if (!res.ok) throw new Error('Gagal memuat hasil analisis');
    return res.json();
  },

  async deleteAnalysisReport(projectId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/analysis/project/${projectId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Gagal mereset laporan riset');
  },

  async updateGapStatus(gapId: string, data: { internal_status?: string; impact_score?: number; effort_score?: number }): Promise<void> {
    const res = await fetch(`${API_BASE}/analysis/feature-gap/${gapId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Gagal memperbarui status gap');
  },

  // Settings
  async getSettings(): Promise<AppSettings> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Gagal memuat pengaturan');
    return res.json();
  },

  async updateSettings(data: {
    gemini_api_key?: string;
    openai_api_key?: string;
    anthropic_api_key?: string;
    qwen_api_key?: string;
    qwen_base_url?: string;
    qwen_model?: string;
    default_provider?: string;
  }): Promise<void> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Gagal menyimpan pengaturan');
  },

  // Exports URLs
  getExportPdfUrl(reportId: string): string {
    return `${API_BASE}/exports/${reportId}/pdf`;
  },
  getExportExcelUrl(reportId: string): string {
    return `${API_BASE}/exports/${reportId}/excel`;
  },
  getExportCsvUrl(reportId: string): string {
    return `${API_BASE}/exports/${reportId}/csv`;
  },
  getExportMarkdownUrl(reportId: string): string {
    return `${API_BASE}/exports/${reportId}/markdown`;
  },
  getExportHtmlUrl(reportId: string): string {
    return `${API_BASE}/exports/${reportId}/html`;
  },
  getPrintHtmlUrl(reportId: string): string {
    return `${API_BASE}/exports/${reportId}/print`;
  },
};
