export interface Project {
  id: string;
  title: string;
  category: string;
  description?: string;
  created_at: string;
  updated_at: string;
  competitors_count: number;
  has_internal_app: boolean;
  has_report: boolean;
}

export interface FeatureItem {
  name: string;
  description: string;
}

export interface ModuleItem {
  module_name: string;
  features: FeatureItem[];
}

export interface UserFlowItem {
  flow_name: string;
  steps: string[];
  notes?: string;
}

export interface InternalAppProfile {
  id?: string;
  project_id: string;
  app_name: string;
  category: string;
  description?: string;
  target_audience?: string;
  modules_features: ModuleItem[];
  user_flows: UserFlowItem[];
  updated_at?: string;
}

export interface Competitor {
  id: string;
  project_id: string;
  name: string;
  playstore_package: string;
  website_url: string;
  extra_urls: string[];
}

export interface DiscoveredApp {
  package_name: string;
  title: string;
  developer: string;
  score: number;
  installs: string;
  icon: string;
  description: string;
  genre?: string;
  playstore_url: string;
}

export interface OfficialSource {
  title: string;
  type: 'website' | 'playstore_review' | 'changelog' | 'external';
  quote?: string;
  url: string;
}

export interface FeatureGap {
  id: string;
  competitor_name: string;
  feature_name: string;
  category: string;
  internal_status: 'Belum Diadaptasi' | 'Sebagian Diadaptasi' | 'Sudah Setara' | 'Aplikasi Kita Unggul';
  innovation_highlight: string;
  impact_score: number;
  effort_score: number;
  official_sources: OfficialSource[];
}

export interface FlowComparison {
  id: string;
  flow_name: string;
  internal_steps: string;
  competitor_detected_flow: string;
  friction_points: string;
  simplification_recommendation: string;
}

export interface CompetitorOverview {
  id: string;
  competitor_name: string;
  playstore_score: number;
  ratings_count: number;
  key_strengths: string[];
  key_weaknesses: string[];
  playstore_url: string;
  website_url: string;
}

export interface AnalysisReport {
  id: string;
  project_id: string;
  project_title: string;
  summary: string;
  created_at: string;
  feature_gaps: FeatureGap[];
  flow_comparisons: FlowComparison[];
  competitor_overviews: CompetitorOverview[];
}

export interface AppSettings {
  gemini_api_key_masked: string;
  has_gemini: boolean;
  openai_api_key_masked: string;
  has_openai: boolean;
  anthropic_api_key_masked: string;
  has_claude: boolean;
  qwen_api_key_masked?: string;
  has_qwen?: boolean;
  qwen_base_url?: string;
  qwen_model?: string;
  default_provider: string;
}
