import json
import logging
from typing import List, Dict, Any
from sqlmodel import Session, select
from app.models.models import (
    Project, InternalApp, Competitor, AnalysisReport, 
    FeatureGapItem, FlowComparisonItem, CompetitorOverviewItem
)
from app.services.scraper_playstore import PlayStoreScraper
from app.services.scraper_web import WebScraper
from app.services.llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
Anda adalah Chief Product Officer (CPO) dan Senior Mobile UX Specialist kelas dunia yang ahli dalam 'Competitor Intelligence' dan 'Feature Gap Analysis' untuk aplikasi Android.
Tugas Anda adalah membedah secara objektif aplikasi kompetitor berdasarkan data nyata dari ulasan Google Play Store dan konten Website Resmi, lalu membandingkannya dengan aplikasi internal kami.

Fokus Analisis:
1. INOVASI YANG BELUM KAMI ADAPTASI: Identifikasi fitur-fitur baru, unik, atau unggul milik kompetitor yang belum dimiliki oleh aplikasi internal kita.
2. SITASI SUMBER RESMI (PROVENANCE): Setiap klaim fitur kompetitor wajib menyertakan bukti sumber resmi (URL Website, link Play Store, atau kutipan ulasan nyata).
3. ANALISIS FRIKSI USER FLOW: Bandingkan langkah alur aplikasi internal dengan pengalaman kompetitor, temukan langkah berbelit-belit (friction) dan berikan saran simplifikasi konkret.
4. MATRIKS PRIORITAS: Berikan skor Impact (1-10) dan Effort (1-10) untuk tiap inovasi agar tim produk tahu mana yang 'Quick Win' vs 'Strategic Project'.

KEMBALIKAN HANYA FORMAT JSON DENGAN STRUKTUR BERIKUT:
{
  "summary": "Ringkasan eksekutif 2-3 paragraf mengenai lanskap persaingan, posisi aplikasi internal, dan area inovasi terpenting.",
  "feature_gaps": [
    {
      "competitor_name": "Nama Kompetitor",
      "feature_name": "Nama Fitur Inovatif",
      "category": "Kategori Modul (misal: Checkout, Loyalty, AI Assistant, dll.)",
      "internal_status": "Belum Diadaptasi | Sebagian Diadaptasi | Sudah Setara | Aplikasi Kita Unggul",
      "innovation_highlight": "Penjelasan mengapa fitur ini inovatif dan apa nilai tambahnya bagi pengguna.",
      "impact_score": 8,
      "effort_score": 5,
      "official_sources": [
        {
          "title": "Website Resmi / Ulasan Play Store",
          "type": "website | playstore_review | changelog | external",
          "quote": "Kutipan atau deskripsi bukti",
          "url": "https://..."
        }
      ]
    }
  ],
  "flow_comparisons": [
    {
      "flow_name": "Nama Alur (misal: Registrasi & Onboarding / Checkout)",
      "internal_steps": "Langkah-langkah di aplikasi kita",
      "competitor_detected_flow": "Langkah atau pendekatan yang dipakai kompetitor",
      "friction_points": "Di mana letak hambatan / inefisiensi pada flow internal",
      "simplification_recommendation": "Rekomendasi konkret cara memangkas langkah"
    }
  ],
  "competitor_overviews": [
    {
      "competitor_name": "Nama Kompetitor",
      "playstore_score": 4.5,
      "ratings_count": 50000,
      "key_strengths": ["Kekuatan 1", "Kekuatan 2"],
      "key_weaknesses": ["Kelemahan 1 berdasarkan komplain ulasan", "Kelemahan 2"],
      "playstore_url": "https://play.google.com/store/apps/details?id=...",
      "website_url": "https://..."
    }
  ]
}
"""

class AnalysisEngine:
    @classmethod
    def determine_search_queries(cls, internal_app: Any, custom_keywords: str = None) -> List[str]:
        """
        Menentukan kata kunci pencarian yang presisi dari profil aplikasi internal.
        """
        queries = []
        if custom_keywords and custom_keywords.strip():
            queries.append(custom_keywords.strip())

        if internal_app:
            category = (internal_app.category or "").strip()
            app_name = (internal_app.app_name or "").strip()

            if category and category.lower() not in ["general", "umum", "aplikasi", "lainnya", "lain-lain"]:
                queries.append(category)

            try:
                mods = json.loads(internal_app.modules_features_json) if internal_app.modules_features_json else []
                feature_names = []
                for m in mods:
                    if isinstance(m, dict):
                        m_name = m.get("module_name", "")
                        if m_name and m_name.lower() not in ["modul utama", "general"]:
                            feature_names.append(m_name)
                if feature_names:
                    queries.append(f"{category} {' '.join(feature_names[:2])}".strip())
            except Exception:
                pass

            if app_name and app_name.lower() not in ["app", "aplikasi", "my app", "untitled"]:
                queries.append(app_name)

        if not queries:
            queries = ["mobile app android"]

        deduped = []
        for q in queries:
            if q and q not in deduped:
                deduped.append(q)
        return deduped

    @classmethod
    async def auto_discover_and_register_competitors(
        cls,
        project_id: str,
        internal_app: Any,
        limit: int = 3,
        custom_keywords: str = None,
        session: Session = None
    ) -> List[Competitor]:
        """
        Mencari kompetitor di Google Play Store berdasarkan profil internal app,
        mengambil detailnya, dan otomatis mendaftarkannya ke dalam project.
        """
        existing_comps = session.exec(select(Competitor).where(Competitor.project_id == project_id)).all()
        existing_pkgs = {c.playstore_package.strip().lower() for c in existing_comps if c.playstore_package}
        existing_names = {c.name.strip().lower() for c in existing_comps}

        queries = cls.determine_search_queries(internal_app, custom_keywords)
        logger.info(f"Menjalankan auto-discovery kompetitor dengan kueri: {queries}")

        found_candidates: List[Dict[str, Any]] = []
        seen_pkgs = set(existing_pkgs)

        for query in queries:
            if len(found_candidates) >= limit:
                break
            raw_hits = PlayStoreScraper.search_competitor_apps(query, n_hits=limit + 4)
            for hit in raw_hits:
                pkg = hit["package_name"].lower()
                name = hit["title"].lower()

                if pkg in seen_pkgs or name in existing_names:
                    continue

                if internal_app and (
                    internal_app.app_name.lower() in name or 
                    name in internal_app.app_name.lower()
                ):
                    continue

                seen_pkgs.add(pkg)
                found_candidates.append(hit)
                if len(found_candidates) >= limit:
                    break

        registered: List[Competitor] = []
        for cand in found_candidates:
            pkg = cand["package_name"]
            title = cand["title"]

            details = PlayStoreScraper.scrape_app_details(pkg)
            website_url = details.get("website") or ""

            new_comp = Competitor(
                project_id=project_id,
                name=title,
                playstore_package=pkg,
                website_url=website_url,
                extra_urls_json="[]"
            )
            session.add(new_comp)
            registered.append(new_comp)

        if registered:
            session.commit()
            for r in registered:
                session.refresh(r)
            logger.info(f"Berhasil meregistrasi {len(registered)} kompetitor otomatis untuk proyek {project_id}")

        return registered

    @classmethod
    async def run_project_analysis(
        cls, 
        project_id: str, 
        provider: str, 
        session: Session,
        auto_discover: bool = True,
        discover_limit: int = 3,
        custom_keywords: str = None
    ) -> AnalysisReport:
        """
        Menjalankan seluruh pipeline riset kompetitor:
        1. Ambil profil aplikasi internal
        2. Auto-discovery kompetitor Play Store jika diaktifkan atau belum ada kompetitor
        3. Scrape Play Store dan Web kompetitor
        4. Synthesize dengan AI LLM
        5. Simpan hasil ke database
        """
        project = session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} tidak ditemukan")

        # 1. Ambil data aplikasi internal
        internal_app = session.exec(select(InternalApp).where(InternalApp.project_id == project_id)).first()
        internal_context = "Tidak ada profil aplikasi internal."
        if internal_app:
            internal_context = f"""
NAMA APLIKASI INTERNAL: {internal_app.app_name}
KATEGORI: {internal_app.category}
DESKRIPSI: {internal_app.description}
TARGET AUDIENCE: {internal_app.target_audience}

DAFTAR MODUL & FITUR SAAT INI:
{internal_app.modules_features_json}

USER FLOW SAAT INI:
{internal_app.user_flows_json}
"""

        # 2. Ambil kompetitor / Jalankan Auto-Discovery
        competitors = session.exec(select(Competitor).where(Competitor.project_id == project_id)).all()

        if auto_discover:
            logger.info("Auto-discovery aktif: mencari kompetitor sejenis di Google Play Store...")
            await cls.auto_discover_and_register_competitors(
                project_id=project_id,
                internal_app=internal_app,
                limit=discover_limit,
                custom_keywords=custom_keywords,
                session=session
            )
            # Muat ulang daftar kompetitor proyek yang terbarui
            competitors = session.exec(select(Competitor).where(Competitor.project_id == project_id)).all()

        # Fallback jika belum ada kompetitor sama sekali
        if not competitors:
            logger.info("Daftar kompetitor kosong, menjalankan auto-discovery darurat...")
            await cls.auto_discover_and_register_competitors(
                project_id=project_id,
                internal_app=internal_app,
                limit=discover_limit,
                custom_keywords=custom_keywords,
                session=session
            )
            competitors = session.exec(select(Competitor).where(Competitor.project_id == project_id)).all()

        if not competitors:
            raise ValueError("Tidak ada kompetitor yang ditemukan atau didaftarkan dalam proyek ini.")

        competitor_dossiers = []
        competitor_ids = [c.id for c in competitors]

        # 3. Kumpulkan data kompetitor
        for comp in competitors:
            dossier = {
                "name": comp.name,
                "playstore_pkg": comp.playstore_package,
                "website_url": comp.website_url,
                "playstore_data": {},
                "reviews_data": {},
                "web_data": []
            }

            # Play Store Scraping
            if comp.playstore_package:
                dossier["playstore_data"] = PlayStoreScraper.scrape_app_details(comp.playstore_package)
                dossier["reviews_data"] = PlayStoreScraper.scrape_app_reviews(comp.playstore_package, count=60)

            # Web Scraping
            urls_to_scrape = []
            if comp.website_url:
                urls_to_scrape.append(comp.website_url)
            try:
                extras = json.loads(comp.extra_urls_json) if comp.extra_urls_json else []
                urls_to_scrape.extend(extras)
            except Exception:
                pass

            if urls_to_scrape:
                dossier["web_data"] = await WebScraper.scrape_multiple_urls(urls_to_scrape[:3])

            competitor_dossiers.append(dossier)

        # 4. Susun Context Prompt
        prompt_parts = [
            "### [BASELINE] DATA APLIKASI INTERNAL KITA:",
            internal_context,
            "\n### [DATA EVIDENSI KOMPETITOR]:"
        ]

        for cd in competitor_dossiers:
            prompt_parts.append(f"\n--- KOMPETITOR: {cd['name']} ---")
            ps = cd["playstore_data"]
            if ps:
                prompt_parts.append(f"Play Store URL: {ps.get('playstore_url', '')}")
                prompt_parts.append(f"Rating: {ps.get('score')} ({ps.get('ratings')} rating, {ps.get('installs')} unduhan)")
                prompt_parts.append(f"Ringkasan App: {ps.get('summary')}")
                prompt_parts.append(f"Deskripsi Fitur Play Store:\n{ps.get('description', '')[:2000]}")
                if ps.get('recent_changes'):
                    prompt_parts.append(f"Changelog Terbaru: {ps.get('recent_changes')}")

            rv = cd["reviews_data"]
            if rv:
                praises = rv.get("praises", [])
                complaints = rv.get("complaints", [])
                if praises:
                    prompt_parts.append("Kutipan Ulasan Pengguna Yang Memuji Fitur (Bintang 4-5):")
                    for pr in praises[:8]:
                        prompt_parts.append(f"- \"{pr}\"")
                if complaints:
                    prompt_parts.append("Kutipan Ulasan Pengguna Yang Mengeluhkan Masalah (Bintang 1-3):")
                    for cm in complaints[:8]:
                        prompt_parts.append(f"- \"{cm}\"")

            for wb in cd["web_data"]:
                prompt_parts.append(f"\nWebsite URL: {wb.get('url')}")
                prompt_parts.append(f"Halaman: {wb.get('title')}")
                prompt_parts.append(f"Konten Fitur Website:\n{wb.get('content', '')[:3000]}")

        final_prompt = "\n".join(prompt_parts)

        # 5. Jalankan AI Analysis
        ai_result = await LLMAdapter.generate_structured_analysis(
            prompt=final_prompt,
            system_instruction=SYSTEM_INSTRUCTION,
            provider=provider,
            session=session
        )

        import re

        # Helper normalisasi wrapper jika LLM membungkus di objek data/analysis/report
        target_dict = ai_result
        for wrapper in ["data", "analysis", "report", "result"]:
            if wrapper in target_dict and isinstance(target_dict[wrapper], dict):
                target_dict = target_dict[wrapper]
                break

        summary_text = (
            target_dict.get("summary") or 
            target_dict.get("executive_summary") or 
            target_dict.get("ringkasan") or 
            "Analisis berhasil diselesaikan."
        )

        raw_gaps = (
            target_dict.get("feature_gaps") or 
            target_dict.get("featureGaps") or 
            target_dict.get("features") or 
            target_dict.get("gaps") or 
            target_dict.get("innovations") or 
            []
        )
        if not isinstance(raw_gaps, list):
            raw_gaps = []

        raw_flows = (
            target_dict.get("flow_comparisons") or 
            target_dict.get("flowComparisons") or 
            target_dict.get("flows") or 
            target_dict.get("user_flows") or 
            []
        )
        if not isinstance(raw_flows, list):
            raw_flows = []

        raw_overviews = (
            target_dict.get("competitor_overviews") or 
            target_dict.get("competitorOverviews") or 
            target_dict.get("competitors") or 
            target_dict.get("overviews") or 
            []
        )
        if not isinstance(raw_overviews, list):
            raw_overviews = []

        def safe_int(val, default=5):
            if isinstance(val, (int, float)):
                return min(10, max(1, int(val)))
            if isinstance(val, str):
                digits = re.findall(r'\d+', val)
                if digits:
                    return min(10, max(1, int(digits[0])))
            return default

        def safe_float(val, default=4.5):
            if isinstance(val, (int, float)):
                return round(float(val), 2)
            if isinstance(val, str):
                match = re.search(r'\d+(\.\d+)?', val)
                if match:
                    return round(float(match.group(0)), 2)
            return default

        def safe_int_large(val, default=1000):
            if isinstance(val, (int, float)):
                return int(val)
            if isinstance(val, str):
                clean_str = val.replace('.', '').replace(',', '')
                digits = re.findall(r'\d+', clean_str)
                if digits:
                    return int(digits[0])
            return default

        def safe_str(val, default="-"):
            if val is None:
                return default
            if isinstance(val, list):
                return "\n".join(str(x) for x in val)
            return str(val)

        def safe_list(val):
            if isinstance(val, list):
                return [str(x) for x in val]
            if isinstance(val, str) and val.strip():
                return [val.strip()]
            return []

        # 6. Simpan hasil ke DB
        report = AnalysisReport(
            project_id=project_id,
            competitor_ids_json=json.dumps(competitor_ids),
            summary=summary_text
        )
        session.add(report)
        session.commit()
        session.refresh(report)

        # Simpan Feature Gaps
        for fg in raw_gaps:
            if not isinstance(fg, dict):
                continue
            try:
                comp_name = fg.get("competitor_name") or fg.get("competitorName") or fg.get("competitor") or (competitors[0].name if competitors else "Kompetitor")
                feat_name = fg.get("feature_name") or fg.get("featureName") or fg.get("name") or "Fitur Inovatif"
                cat = fg.get("category") or fg.get("module") or "General"
                status = fg.get("internal_status") or fg.get("internalStatus") or fg.get("status") or "Belum Diadaptasi"
                highlight = fg.get("innovation_highlight") or fg.get("innovationHighlight") or fg.get("description") or ""
                impact = safe_int(fg.get("impact_score") or fg.get("impactScore") or fg.get("impact"), 8)
                effort = safe_int(fg.get("effort_score") or fg.get("effortScore") or fg.get("effort"), 5)

                sources = fg.get("official_sources") or fg.get("officialSources") or fg.get("sources") or []
                if isinstance(sources, str):
                    sources = [{"title": "Sumber Resmi", "url": "", "type": "official", "quote": sources}]
                elif not isinstance(sources, list):
                    sources = []

                item = FeatureGapItem(
                    report_id=report.id,
                    competitor_name=comp_name,
                    feature_name=feat_name,
                    category=cat,
                    internal_status=status,
                    innovation_highlight=highlight,
                    impact_score=impact,
                    effort_score=effort,
                    official_sources_json=json.dumps(sources)
                )
                session.add(item)
            except Exception as e:
                logger.warning(f"Gagal memproses item FeatureGap: {e}")

        # Simpan Flow Comparisons
        for fc in raw_flows:
            if not isinstance(fc, dict):
                continue
            try:
                flow_name = fc.get("flow_name") or fc.get("flowName") or fc.get("name") or "Alur Utama"
                internal_steps = safe_str(fc.get("internal_steps") or fc.get("internalSteps") or fc.get("steps"))
                comp_flow = safe_str(fc.get("competitor_detected_flow") or fc.get("competitorDetectedFlow") or fc.get("competitor_flow"))
                friction = safe_str(fc.get("friction_points") or fc.get("frictionPoints") or fc.get("friction"))
                simplification = safe_str(fc.get("simplification_recommendation") or fc.get("simplificationRecommendation") or fc.get("recommendation"))

                flow_item = FlowComparisonItem(
                    report_id=report.id,
                    flow_name=flow_name,
                    internal_steps=internal_steps,
                    competitor_detected_flow=comp_flow,
                    friction_points=friction,
                    simplification_recommendation=simplification
                )
                session.add(flow_item)
            except Exception as e:
                logger.warning(f"Gagal memproses item FlowComparison: {e}")

        # Simpan Competitor Overviews
        for co in raw_overviews:
            if not isinstance(co, dict):
                continue
            try:
                comp_name = co.get("competitor_name") or co.get("competitorName") or co.get("name") or "Kompetitor"
                score = safe_float(co.get("playstore_score") or co.get("playstoreScore") or co.get("score"), 4.0)
                ratings = safe_int_large(co.get("ratings_count") or co.get("ratingsCount") or co.get("ratings"), 0)
                strengths = safe_list(co.get("key_strengths") or co.get("keyStrengths") or co.get("strengths"))
                weaknesses = safe_list(co.get("key_weaknesses") or co.get("keyWeaknesses") or co.get("weaknesses"))
                ps_url = co.get("playstore_url") or co.get("playstoreUrl") or ""
                web_url = co.get("website_url") or co.get("websiteUrl") or ""

                co_item = CompetitorOverviewItem(
                    report_id=report.id,
                    competitor_name=comp_name,
                    playstore_score=score,
                    ratings_count=ratings,
                    key_strengths_json=json.dumps(strengths),
                    key_weaknesses_json=json.dumps(weaknesses),
                    playstore_url=ps_url,
                    website_url=web_url
                )
                session.add(co_item)
            except Exception as e:
                logger.warning(f"Gagal memproses item CompetitorOverview: {e}")

        session.commit()
        session.refresh(report)
        return report
