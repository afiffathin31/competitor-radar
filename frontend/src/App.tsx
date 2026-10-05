import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { FeatureGapTable } from './components/FeatureGapTable';
import { UserFlowComparison } from './components/UserFlowComparison';
import { ChartsSection } from './components/ChartsSection';
import { InternalAppForm } from './components/InternalAppForm';
import { CompetitorsManager } from './components/CompetitorsManager';
import { SettingsTab } from './components/SettingsTab';
import { NewProjectModal } from './components/NewProjectModal';
import { EditProjectModal } from './components/EditProjectModal';
import { RunAnalysisModal } from './components/RunAnalysisModal';
import type { Project, AnalysisReport, InternalAppProfile } from './types';
import { api } from './api';
import { 
  Play, CheckCircle2, AlertCircle, 
  Smartphone, Users, Compass, Edit3, RotateCcw
} from 'lucide-react';

export function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'internal' | 'competitors' | 'settings'>('analysis');
  
  const [internalAppProfile, setInternalAppProfile] = useState<InternalAppProfile | null>(null);
  const [latestReport, setLatestReport] = useState<AnalysisReport | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [isEditProjectModalOpen, setIsEditProjectModalOpen] = useState(false);
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (activeProject) {
      loadReport(activeProject.id);
      loadInternalApp(activeProject.id);
    }
  }, [activeProject]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects();
      setProjects(data);
      if (data.length > 0) {
        setActiveProject(prev => {
          if (!prev) return data[0];
          const updated = data.find(p => p.id === prev.id);
          return updated || data[0];
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadInternalApp = async (projectId: string) => {
    try {
      const app = await api.getInternalApp(projectId);
      setInternalAppProfile(app);
    } catch (err) {
      console.error(err);
    }
  };

  const loadReport = async (projectId: string) => {
    try {
      const rep = await api.getLatestAnalysis(projectId);
      setLatestReport(rep);
    } catch (err) {
      console.error(err);
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleOpenRunModal = () => {
    setIsRunModalOpen(true);
  };

  const handleExecuteAnalysis = async (options: {
    autoDiscover: boolean;
    discoverLimit: number;
    customKeywords: string;
    provider: string;
  }) => {
    if (!activeProject) return;

    try {
      setIsAnalyzing(true);
      showToast('Memulai crawling Play Store & Web kompetitor serta analisis...', 'success');
      
      const report = await api.runAnalysis(
        activeProject.id,
        options.provider,
        options.autoDiscover,
        options.discoverLimit,
        options.customKeywords
      );
      setLatestReport(report);
      setIsRunModalOpen(false);
      setActiveTab('analysis');
      await loadProjects();
      showToast('Analisis riset kompetitor berhasil diselesaikan.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Gagal menjalankan analisis', 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleResetAnalysis = async () => {
    if (!activeProject) return;
    if (!confirm(`Hapus seluruh laporan hasil riset sebelumnya untuk proyek "${activeProject.title}"? Anda dapat menjalankan riset ulang kapan saja.`)) return;

    try {
      await api.deleteAnalysisReport(activeProject.id);
      setLatestReport(null);
      await loadProjects();
      showToast('Laporan riset sebelumnya berhasil dihapus. Dashboard siap untuk riset ulang.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Gagal menghapus laporan riset', 'error');
    }
  };

  const handleProjectUpdated = (updated: Project) => {
    setActiveProject(updated);
    setProjects(prev => prev.map(p => p.id === updated.id ? updated : p));
    showToast(`Informasi sesi riset "${updated.title}" berhasil diperbarui.`, 'success');
  };

  const handleDeleteProject = async (id: string) => {
    try {
      await api.deleteProject(id);
      const remaining = projects.filter(p => p.id !== id);
      setProjects(remaining);
      setActiveProject(remaining.length > 0 ? remaining[0] : null);
      setLatestReport(null);
      showToast('Proyek berhasil dihapus.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Gagal menghapus proyek', 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col items-center justify-center">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mb-3" />
        <h2 className="text-sm font-semibold tracking-tight text-slate-800">Memuat Platform Riset...</h2>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col font-sans">
      
      {/* Top Navbar */}
      <Navbar
        projects={projects}
        activeProject={activeProject}
        onSelectProject={(p) => setActiveProject(p)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenNewProject={() => setIsNewProjectModalOpen(true)}
        onRunAnalysis={handleOpenRunModal}
        isAnalyzing={isAnalyzing}
        latestReport={latestReport}
      />

      {/* Clean Toast Notification */}
      {toast && (
        <div className="fixed top-20 right-6 z-50 max-w-sm">
          <div className={`px-4 py-3 rounded-xl flex items-center gap-3 text-xs font-semibold shadow-md border ${
            toast.type === 'success' 
              ? 'bg-white text-emerald-900 border-emerald-200' 
              : 'bg-white text-rose-900 border-rose-200'
          }`}>
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{toast.message}</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-7">
        
        {/* Minimalist Executive Project Header */}
        {activeProject && (
          <div className="mb-7 bg-white rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden">
            {/* Top Color Accent Bar (Teal & Orange Harmony) */}
            <div className="h-1.5 w-full flex">
              <div className="w-2/3 bg-[#1ACAB6]" />
              <div className="w-1/3 bg-[#F77925]" />
            </div>

            <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-5">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-[#EBFBF8] text-[#0F766E] border border-[#1ACAB6]/30">
                    {activeProject.category}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    Sesi: {activeProject.id.slice(0, 8)}
                  </span>
                </div>
                
                <div className="flex items-center gap-2.5">
                  <h1 className="text-xl font-bold tracking-tight text-slate-900">
                    {activeProject.title}
                  </h1>
                  <button
                    onClick={() => setIsEditProjectModalOpen(true)}
                    className="p-1 text-slate-400 hover:text-teal-700 hover:bg-slate-100 rounded-md transition"
                    title="Edit judul, kategori, dan deskripsi proyek"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                </div>

                {activeProject.description && (
                  <p className="text-xs text-slate-500 max-w-3xl leading-relaxed pt-0.5">
                    {activeProject.description}
                  </p>
                )}
              </div>

              {/* Status / Quick Action Pills */}
              <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                <button
                  onClick={() => setIsEditProjectModalOpen(true)}
                  className="px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition"
                  title="Edit judul, kategori, dan deskripsi proyek"
                >
                  <Edit3 className="w-3.5 h-3.5 text-slate-500" />
                  Edit Sesi
                </button>
                <button
                  onClick={() => setActiveTab('internal')}
                  className="px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition"
                >
                  <Smartphone className="w-3.5 h-3.5 text-slate-500" />
                  Profil Internal
                </button>
                <button
                  onClick={() => setActiveTab('competitors')}
                  className="px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition"
                >
                  <Users className="w-3.5 h-3.5 text-slate-500" />
                  Kompetitor ({activeProject.competitors_count})
                </button>
                {latestReport && (
                  <button
                    onClick={handleResetAnalysis}
                    className="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 border border-rose-200 text-xs font-semibold text-rose-700 flex items-center gap-1.5 transition"
                    title="Hapus riwayat riset sebelumnya agar bersih dan siap dianalisis ulang"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-rose-600" />
                    Reset Riset
                  </button>
                )}
              </div>
            </div>

            {/* Quick Metrics Bar if report exists */}
            {latestReport && (
              <div className="border-t border-slate-100 bg-slate-50/50 px-6 py-2.5 flex flex-wrap items-center gap-6 text-xs text-slate-600">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#E33723]" />
                  <span>Fitur Belum Diadaptasi: <strong>{latestReport.feature_gaps.filter(g => g.internal_status === 'Belum Diadaptasi').length}</strong></span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#F77925]" />
                  <span>Sebagian Diadaptasi: <strong>{latestReport.feature_gaps.filter(g => g.internal_status === 'Sebagian Diadaptasi').length}</strong></span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#1ACAB6]" />
                  <span>Sudah Setara / Unggul: <strong>{latestReport.feature_gaps.filter(g => g.internal_status === 'Sudah Setara' || g.internal_status === 'Aplikasi Kita Unggul').length}</strong></span>
                </div>
                <div className="flex items-center gap-1.5 ml-auto text-slate-400 text-[11px]">
                  Dianalisis: {latestReport.created_at}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 1: ANALYSIS & MATRIX */}
        {activeTab === 'analysis' && (
          <div className="space-y-7">
            {latestReport ? (
              <>
                {/* Executive Summary Card */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                      <Compass className="w-4 h-4 text-[#0D9488]" />
                      Ringkasan Eksekutif & Lanskap Persaingan Pasar
                    </h3>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line pt-1">
                    {latestReport.summary}
                  </p>
                </div>

                {/* Visual Charts: Radar & Quadrant */}
                <ChartsSection
                  featureGaps={latestReport.feature_gaps}
                  competitorOverviews={latestReport.competitor_overviews}
                  internalAppProfile={internalAppProfile}
                  projectCategory={activeProject?.category}
                />

                {/* Core Feature Gap Matrix */}
                <FeatureGapTable
                  gaps={latestReport.feature_gaps}
                  onGapUpdated={() => activeProject && loadReport(activeProject.id)}
                />

                {/* User Flow Friction & Simplification */}
                <UserFlowComparison
                  flowComparisons={latestReport.flow_comparisons}
                />
              </>
            ) : (
              /* Minimalist Empty State */
              <div className="bg-white p-12 rounded-2xl border border-slate-200 shadow-sm text-center max-w-lg mx-auto space-y-3.5 my-8">
                <div className="w-12 h-12 bg-[#EBFBF8] text-[#0D9488] rounded-xl flex items-center justify-center mx-auto border border-[#1ACAB6]/30">
                  <Compass className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Belum Ada Laporan Analisis</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
                  Lengkapi profil aplikasi internal dan pastikan data kompetitor sudah terdaftar, lalu jalankan riset untuk melihat perbandingan gap inovasi.
                </p>
                <div className="pt-2">
                  <button
                    onClick={handleOpenRunModal}
                    disabled={isAnalyzing}
                    className="px-5 py-2 rounded-lg bg-[#0D9488] hover:bg-[#0F766E] text-white text-xs font-semibold inline-flex items-center gap-2 transition shadow-xs"
                  >
                    {isAnalyzing ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Sedang Menganalisis...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current" />
                        Jalankan Riset Sekarang
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: INTERNAL APP PROFILE */}
        {activeTab === 'internal' && activeProject && (
          <InternalAppForm 
            projectId={activeProject.id} 
            onStartResearch={handleOpenRunModal}
          />
        )}

        {/* TAB 3: COMPETITORS MANAGEMENT */}
        {activeTab === 'competitors' && activeProject && (
          <CompetitorsManager
            projectId={activeProject.id}
            onCompetitorChange={() => loadProjects()}
          />
        )}

        {/* TAB 4: SETTINGS */}
        {activeTab === 'settings' && <SettingsTab />}

      </main>

      {/* New Project Modal */}
      <NewProjectModal
        isOpen={isNewProjectModalOpen}
        onClose={() => setIsNewProjectModalOpen(false)}
        onProjectCreated={(p) => {
          setProjects([p, ...projects]);
          setActiveProject(p);
          setActiveTab('internal');
          showToast(`Proyek "${p.title}" dibuat. Silakan atur profil aplikasi Anda.`, 'success');
        }}
      />

      {/* Edit Project Modal */}
      {activeProject && (
        <EditProjectModal
          isOpen={isEditProjectModalOpen}
          onClose={() => setIsEditProjectModalOpen(false)}
          project={activeProject}
          onProjectUpdated={handleProjectUpdated}
          onDeleteProject={handleDeleteProject}
        />
      )}

      {/* Run Analysis & Auto-Discovery Modal */}
      {activeProject && (
        <RunAnalysisModal
          isOpen={isRunModalOpen}
          onClose={() => setIsRunModalOpen(false)}
          project={activeProject}
          internalApp={internalAppProfile}
          competitorsCount={activeProject.competitors_count || 0}
          onRun={handleExecuteAnalysis}
          isAnalyzing={isAnalyzing}
        />
      )}

    </div>
  );
}
export default App;
