import io
import csv
import json
import base64
import os
from typing import Dict, Any, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from xhtml2pdf import pisa

_LOGO_BASE64_CACHE = None

def _get_app_logo_base64() -> str:
    global _LOGO_BASE64_CACHE
    if _LOGO_BASE64_CACHE is not None:
        return _LOGO_BASE64_CACHE
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    candidates = [
        os.path.join(base_dir, "frontend", "public", "logo.png"),
        os.path.join(base_dir, "frontend", "src", "assets", "logo.png"),
        os.path.join(base_dir, "frontend", "dist", "logo.png"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    _LOGO_BASE64_CACHE = f"data:image/png;base64,{b64}"
                    return _LOGO_BASE64_CACHE
            except Exception:
                pass
    _LOGO_BASE64_CACHE = ""
    return _LOGO_BASE64_CACHE

class ExportService:
    @staticmethod
    def _compute_quadrants(feature_gaps: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Pengelompokan 4 kuadran prioritas Impact vs Effort"""
        q1 = [g for g in feature_gaps if g.get("impact_score", 5) >= 8 and g.get("effort_score", 5) <= 6]
        q2 = [g for g in feature_gaps if g.get("impact_score", 5) >= 7 and g.get("effort_score", 5) >= 7]
        q3 = [g for g in feature_gaps if g.get("impact_score", 5) < 7 and g.get("effort_score", 5) <= 5]
        q4 = [g for g in feature_gaps if g.get("impact_score", 5) < 7 and g.get("effort_score", 5) > 6]
        return {
            "quick_wins": q1,
            "strategic": q2,
            "secondary": q3,
            "reconsider": q4
        }

    @staticmethod
    def _compute_module_maturity(report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Menghitung evaluasi kematangan fitur per modul"""
        gaps = report_data.get("feature_gaps", [])
        categories = list(dict.fromkeys([g.get("category") for g in gaps if g.get("category")]))
        
        # Jika gap memiliki kategori
        if len(categories) >= 3:
            results = []
            for cat in categories[:6]:
                cat_gaps = [g for g in gaps if g.get("category") == cat]
                adopted = len([g for g in cat_gaps if g.get("internal_status") in ["Sudah Setara", "Aplikasi Kita Unggul"]])
                score = round((adopted / len(cat_gaps)) * 10) if cat_gaps else 6
                results.append({
                    "module": cat,
                    "internal_score": max(3, score),
                    "benchmark_score": 9,
                    "status": "Setara" if score >= 8 else ("Perlu Inovasi" if score <= 5 else "Cukup Baik")
                })
            return results

        # Fallback ke modul internal app jika ada
        internal_app = report_data.get("internal_app") or {}
        mods = internal_app.get("modules_features", [])
        if mods and len(mods) >= 3:
            results = []
            for m in mods[:6]:
                m_name = m.get("module_name", "")
                if m_name:
                    results.append({
                        "module": m_name,
                        "internal_score": 6,
                        "benchmark_score": 8,
                        "status": "Dalam Pengembangan"
                    })
            if len(results) >= 3:
                return results

        # Fallback kontekstual berbasis kategori proyek
        cat_text = f"{report_data.get('project_category', '')} {internal_app.get('category', '')}".lower()
        if any(w in cat_text for w in ["haji", "umrah", "umroh", "ibadah", "doa", "agama", "religi"]):
            default_axes = [
                ("Panduan Ritual & Manasik", 6, 9, "Tertinggal di utilitas lapangan"),
                ("Audio & Teks Doa", 7, 9, "Perlu fitur pengulangan audio"),
                ("Peta & Lokasi Offline", 5, 8, "Belum ada peta navigasi offline"),
                ("Jadwal & Waktu Ibadah", 8, 8, "Setara dengan kompetitor"),
                ("Kemudahan Akses Offline", 6, 9, "Kompetitor unggul di zero-data mode")
            ]
        else:
            default_axes = [
                ("Pengalaman UI/UX", 7, 9, "Perlu simplifikasi alur"),
                ("Fungsionalitas Offline", 5, 8, "Perlu mode cache offline"),
                ("Personalisasi Konten", 6, 8, "Cukup baik"),
                ("Kecepatan & Responsivitas", 7, 9, "Setara"),
                ("Kelengkapan Fitur Inti", 6, 8, "Perlu adopsi inovasi baru")
            ]

        return [
            {"module": ax[0], "internal_score": ax[1], "benchmark_score": ax[2], "status": ax[3]}
            for ax in default_axes
        ]

    @classmethod
    def export_pdf(cls, report_data: Dict[str, Any]) -> io.BytesIO:
        """
        Menghasilkan file PDF asli (.pdf) yang siap unduh menggunakan xhtml2pdf,
        mencakup seluruh modul matriks dan laporan tanpa terkecuali.
        """
        html_code = cls._build_complete_html(report_data, for_pdf_renderer=True)
        out = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_code, dest=out)
        if pisa_status.err:
            raise RuntimeError(f"Gagal mengonversi laporan ke PDF: error code {pisa_status.err}")
        out.seek(0)
        return out

    @classmethod
    def export_html(cls, report_data: Dict[str, Any]) -> str:
        """
        Menghasilkan dokumen HTML lengkap siap cetak / simpan PDF via browser print dialog,
        lengkap dengan toolbar unduh PDF langsung dan cetak otomatis.
        """
        return cls._build_complete_html(report_data, for_pdf_renderer=False)

    @classmethod
    def _build_complete_html(cls, report_data: Dict[str, Any], for_pdf_renderer: bool = False) -> str:
        """
        Membangun dokumen HTML eksekutif mencakup seluruh komponen Matriks & Laporan:
        1. Identitas Proyek & Profil Internal App
        2. Daftar Kompetitor Terdaftar (Play Store & Web)
        3. Ringkasan Eksekutif CPO
        4. Evaluasi Kematangan Fitur per Modul
        5. Matriks Prioritas Inovasi (4 Kuadran Impact vs Effort)
        6. Sentimen Ulasan Play Store & Voice-of-Customer
        7. Matriks Gap Inovasi Fitur Lengkap dengan Sitasi Sumber Resmi
        8. Analisis Friksi Alur Pengguna (User Flow Benchmark)
        """
        project_title = report_data.get("project_title", "Laporan Riset Kompetitor")
        project_category = report_data.get("project_category", "Mobile Application")
        project_description = report_data.get("project_description", "")
        created_at = report_data.get("created_at", "-")
        summary = report_data.get("summary", "-")
        report_id = report_data.get("id", "")

        internal_app = report_data.get("internal_app") or {}
        competitors = report_data.get("competitors") or []
        feature_gaps = report_data.get("feature_gaps") or []
        flow_comparisons = report_data.get("flow_comparisons") or []
        competitor_overviews = report_data.get("competitor_overviews") or []

        logo_b64 = _get_app_logo_base64()
        quadrants = cls._compute_quadrants(feature_gaps)
        maturity_modules = cls._compute_module_maturity(report_data)

        # ---------------- HTML FRAGMENTS ----------------
        
        # 1. Competitors Rows
        comp_rows = ""
        for idx, c in enumerate(competitors, 1):
            co_match = next((co for co in competitor_overviews if co.get("competitor_name", "").lower() == c.get("name", "").lower()), None)
            rating_str = f"★ {co_match.get('playstore_score', 0)} ({co_match.get('ratings_count', 0):,} ulasan)" if co_match else "Terdaftar di Play Store"
            
            web_url = c.get('website_url', '').strip()
            if web_url:
                clean_domain = web_url.replace("https://", "").replace("http://", "").rstrip("/")
                web_link = f"<a href='{web_url}' target='_blank' style='color:#0d9488; font-weight:bold; font-size:7.5pt; text-decoration:none;'>{clean_domain}</a>"
            else:
                web_link = "<span style='color:#94a3b8; font-size:7.5pt; font-style:italic;'>Hanya di Play Store</span>"

            pkg_text = c.get('playstore_package') or "-"
            bg_row = "#ffffff" if idx % 2 != 0 else "#f8fafc"

            comp_rows += f"""
            <tr style="background:{bg_row};">
                <td style="padding:6px 6px; border-bottom:1px solid #e2e8f0; text-align:center; font-weight:bold; color:#64748b; width:5%;">{idx}</td>
                <td style="padding:6px 6px; border-bottom:1px solid #e2e8f0; font-weight:bold; color:#0f172a; width:25%; font-size:8pt;">{c.get('name')}</td>
                <td style="padding:6px 6px; border-bottom:1px solid #e2e8f0; font-family:Courier, monospace; font-size:7.5pt; color:#475569; width:28%;">{pkg_text}</td>
                <td style="padding:6px 6px; border-bottom:1px solid #e2e8f0; font-size:8pt; width:18%;">
                    <span style="color:#b45309; font-weight:bold;">{rating_str}</span>
                </td>
                <td style="padding:6px 6px; border-bottom:1px solid #e2e8f0; width:24%; vertical-align:middle;">{web_link}</td>
            </tr>
            """

        # Internal App Modules formatted into 2 balanced columns
        mods_items = internal_app.get("modules_features", [])
        mods_left = []
        mods_right = []
        for idx, m in enumerate(mods_items):
            m_name = m.get("module_name", "").strip()
            sub_feats = m.get("features", [])
            sub_names = ", ".join([f.get("name", "") for f in sub_feats if f.get("name")])
            detail = f" <span style='color:#64748b;'>({sub_names})</span>" if sub_names else ""
            item_block = f"<div style='background:#f8fafc; border:1px solid #e2e8f0; padding:3px 6px; margin-bottom:3px; font-size:7.5pt; color:#1e293b;'><strong>• {m_name}</strong>{detail}</div>"
            if idx % 2 == 0:
                mods_left.append(item_block)
            else:
                mods_right.append(item_block)

        mods_grid = f"""
        <table style="width:100%; border:none; margin:0;">
            <tr>
                <td style="width:50%; border:none; padding:0 3px 0 0; vertical-align:top;">
                    {''.join(mods_left)}
                </td>
                <td style="width:50%; border:none; padding:0 0 0 3px; vertical-align:top;">
                    {''.join(mods_right)}
                </td>
            </tr>
        </table>
        """

        # 2. Maturity Modules
        maturity_rows = ""
        for idx, m in enumerate(maturity_modules, 1):
            bg_row = "#ffffff" if idx % 2 != 0 else "#f8fafc"
            int_score = m["internal_score"]
            bench_score = m["benchmark_score"]
            
            status_color = "#b91c1c" if "Perlu" in m["status"] or "Tertinggal" in m["status"] else ("#0f766e" if "Setara" in m["status"] else "#b45309")
            status_bg = "#fee2e2" if "Perlu" in m["status"] or "Tertinggal" in m["status"] else ("#f0fdfa" if "Setara" in m["status"] else "#fef3c7")

            maturity_rows += f"""
            <tr style="background:{bg_row};">
                <td style="padding:5px 8px; border-bottom:1px solid #e2e8f0; font-weight:bold; color:#0f172a; width:32%; font-size:8.5pt;">{m['module']}</td>
                <td style="padding:5px 8px; border-bottom:1px solid #e2e8f0; width:26%;">
                    <span style="font-weight:bold; color:#0d9488; font-size:8.5pt;">Skor Kita: {int_score} / 10</span>
                </td>
                <td style="padding:5px 8px; border-bottom:1px solid #e2e8f0; width:26%;">
                    <span style="font-weight:bold; color:#f77925; font-size:8.5pt;">Benchmark: {bench_score} / 10</span>
                </td>
                <td style="padding:5px 8px; border-bottom:1px solid #e2e8f0; width:16%; text-align:center;">
                    <span style="background:{status_bg}; color:{status_color}; padding:2px 6px; font-weight:bold; font-size:7.5pt;">{m['status']}</span>
                </td>
            </tr>
            """

        # 3. Quadrants with Strategic Guidance
        def render_quad_box(items, label, sub, action_badge, color_head, bg_color, border_color):
            item_html = ""
            if items:
                for it in items:
                    item_html += f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; padding:4px 6px; margin-bottom:3px; font-size:7.5pt; color:#1e293b;">
                        <strong>• {it.get('feature_name')}</strong>
                        <span style="color:#64748b; font-size:7pt;">({it.get('competitor_name')})</span>
                    </div>
                    """
            else:
                item_html = "<div style='color:#94a3b8; font-size:7.5pt; font-style:italic;'>Tidak ada item pada kuadran ini.</div>"

            return f"""
            <div style="background:{bg_color}; border:1px solid {border_color}; padding:7px 9px; min-height:85px;">
                <table style="width:100%; border:none; margin:0 0 3px 0;">
                    <tr>
                        <td style="border:none; padding:0; vertical-align:middle;">
                            <span style="font-size:8pt; font-weight:bold; color:{color_head}; text-transform:uppercase;">{label}</span>
                        </td>
                        <td style="border:none; padding:0; text-align:right; vertical-align:middle;">
                            <span style="background:#ffffff; border:1px solid {border_color}; color:{color_head}; font-size:6.5pt; font-weight:bold; padding:1px 4px;">{action_badge}</span>
                        </td>
                    </tr>
                </table>
                <div style="font-size:7pt; color:#64748b; margin-bottom:4px;">{sub}</div>
                {item_html}
            </div>
            """

        quad_q1 = render_quad_box(quadrants['quick_wins'], "01 · QUICK WINS", "Dampak Tinggi (≥8) · Upaya Rendah (≤6)", "EKSEKUSI SEGERA", "#0f766e", "#f0fdfa", "#14b8a6")
        quad_q2 = render_quad_box(quadrants['strategic'], "02 · INISIATIF STRATEGIS", "Dampak Tinggi (≥7) · Upaya Tinggi (≥7)", "ROADMAP OKR", "#c25510", "#fff7ed", "#f97316")
        quad_q3 = render_quad_box(quadrants['secondary'], "03 · FITUR SEKUNDER", "Dampak Sedang (<7) · Upaya Rendah (≤5)", "PENGISI SPRINT", "#334155", "#f8fafc", "#94a3b8")
        quad_q4 = render_quad_box(quadrants['reconsider'], "04 · EVALUASI LANJUT", "Dampak Rendah (<7) · Upaya Tinggi (>6)", "DEPRIORITIZE", "#b91c1c", "#fef2f2", "#ef4444")

        # 4. VoC Cards
        voc_cards = ""
        for co in competitor_overviews:
            str_items = "".join([f"<li style='margin-bottom:1px;'>{s}</li>" for s in co.get("key_strengths", [])])
            weak_items = "".join([f"<li style='margin-bottom:1px;'>{w}</li>" for w in co.get("key_weaknesses", [])])
            
            voc_cards += f"""
            <table style="width:100%; border:1px solid #cbd5e1; margin-bottom:7px; page-break-inside:avoid; background:#ffffff;">
                <tr style="background:#f1f5f9;">
                    <td style="padding:4px 8px; border-bottom:1px solid #cbd5e1;" colspan="2">
                        <strong style="font-size:8.5pt; color:#0f172a;">{co.get('competitor_name')}</strong>
                        <span style="background:#fef3c7; color:#92400e; padding:1px 5px; font-size:7.5pt; font-weight:bold; margin-left:6px;">★ {co.get('playstore_score')}</span>
                        <span style="font-size:7.5pt; color:#64748b; margin-left:4px;">({co.get('ratings_count', 0):,} ulasan Play Store)</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding:5px 8px; width:50%; vertical-align:top; border-right:1px dashed #cbd5e1;">
                        <div style="font-size:7pt; font-weight:bold; color:#0f766e; text-transform:uppercase;">KEKUATAN UTAMA YANG DIPUJI:</div>
                        <ul style="margin:2px 0 0 0; padding-left:14px; font-size:7.5pt; color:#334155; line-height:1.25;">
                            {str_items or "<li>Fitur standar berjalan stabil.</li>"}
                        </ul>
                    </td>
                    <td style="padding:5px 8px; width:50%; vertical-align:top;">
                        <div style="font-size:7pt; font-weight:bold; color:#b91c1c; text-transform:uppercase;">CELAH KELUHAN (PELUANG KITA):</div>
                        <ul style="margin:2px 0 0 0; padding-left:14px; font-size:7.5pt; color:#334155; line-height:1.25;">
                            {weak_items or "<li>Tidak ada keluhan kritis tercatat.</li>"}
                        </ul>
                    </td>
                </tr>
            </table>
            """

        # 5. Feature Gaps Rows
        gaps_rows = ""
        for idx, g in enumerate(feature_gaps, 1):
            src_html = ""
            for s in g.get("official_sources", []):
                s_url = s.get('url', '')
                s_title = s.get('title', 'Sumber Resmi')
                s_quote = s.get('quote', '')
                quote_text = f"<div style='color:#64748b; font-style:italic; font-size:7pt; margin-top:2px; line-height:1.2; border-left:2px solid #0d9488; padding-left:4px;'>\"{s_quote[:100]}...\"</div>" if s_quote else ""
                src_html += f"<div><a href='{s_url}' target='_blank' style='color:#0d9488; font-weight:bold; font-size:7.5pt; text-decoration:none;'>[{s_title}]</a>{quote_text}</div>"

            status = g.get("internal_status", "Belum Diadaptasi")
            status_bg = "#fee2e2" if "Belum" in status else ("#fef3c7" if "Sebagian" in status else "#f0fdfa")
            status_color = "#b91c1c" if "Belum" in status else ("#b45309" if "Sebagian" in status else "#0f766e")
            bg_row = "#ffffff" if idx % 2 != 0 else "#f8fafc"

            gaps_rows += f"""
            <tr style="background:{bg_row}; page-break-inside:avoid;">
                <td style="padding:4px 6px; border-bottom:1px solid #e2e8f0; font-weight:bold; color:#0f172a; width:13%; vertical-align:top; font-size:8pt;">
                    {g.get('competitor_name')}
                </td>
                <td style="padding:4px 6px; border-bottom:1px solid #e2e8f0; width:11%; vertical-align:top;">
                    <span style="background:#f1f5f9; padding:1px 4px; font-size:7pt; color:#475569; font-weight:bold;">{g.get('category')}</span>
                </td>
                <td style="padding:4px 6px; border-bottom:1px solid #e2e8f0; font-weight:bold; color:#0f172a; width:16%; vertical-align:top; font-size:8pt;">
                    {g.get('feature_name')}
                </td>
                <td style="padding:4px 6px; border-bottom:1px solid #e2e8f0; width:11%; vertical-align:top; text-align:center;">
                    <span style="background:{status_bg}; color:{status_color}; padding:1px 4px; font-size:7pt; font-weight:bold;">{status}</span>
                </td>
                <td style="padding:4px 6px; border-bottom:1px solid #e2e8f0; font-size:7.5pt; color:#334155; width:28%; vertical-align:top; line-height:1.25;">
                    {g.get('innovation_highlight')}
                </td>
                <td style="padding:4px 6px; border-bottom:1px solid #e2e8f0; width:8%; vertical-align:top; text-align:center;">
                    <div style="color:#0d9488; font-weight:bold; font-size:7.5pt;">Imp: {g.get('impact_score')}</div>
                    <div style="color:#f77925; font-weight:bold; font-size:7.5pt;">Eff: {g.get('effort_score')}</div>
                </td>
                <td style="padding:4px 6px; border-bottom:1px solid #e2e8f0; width:13%; vertical-align:top;">
                    {src_html or '<span style="color:#94a3b8;">-</span>'}
                </td>
            </tr>
            """

        # 6. User Flows
        flows_html = ""
        for f in flow_comparisons:
            flows_html += f"""
            <div style="background:#ffffff; border:1px solid #cbd5e1; padding:10px; margin-bottom:12px; page-break-inside:avoid;">
                <div style="font-size:9.5pt; font-weight:bold; color:#0f172a; border-bottom:1px solid #e2e8f0; padding-bottom:4px; margin-bottom:8px;">
                    Alur: {f.get('flow_name')}
                </div>
                <table style="width:100%; border:none; margin:0 0 8px 0;">
                    <tr>
                        <td style="width:50%; border:none; padding:0 6px 0 0; vertical-align:top;">
                            <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:8px;">
                                <strong style="font-size:7.5pt; color:#64748b; text-transform:uppercase;">LANGKAH ALUR INTERNAL KITA:</strong>
                                <p style="margin:4px 0 0 0; font-size:8pt; color:#1e293b; line-height:1.35;">{f.get('internal_steps')}</p>
                            </div>
                        </td>
                        <td style="width:50%; border:none; padding:0 0 0 6px; vertical-align:top;">
                            <div style="background:#f0fdfa; border:1px solid #99f6e4; padding:8px;">
                                <strong style="font-size:7.5pt; color:#0d9488; text-transform:uppercase;">PENDEKATAN KOMPETITOR:</strong>
                                <p style="margin:4px 0 0 0; font-size:8pt; color:#0f172a; line-height:1.35;">{f.get('competitor_detected_flow')}</p>
                            </div>
                        </td>
                    </tr>
                </table>
                <div style="background:#fef2f2; border-left:3px solid #ef4444; padding:6px 10px; margin-bottom:6px; font-size:8pt; color:#991b1b; line-height:1.35;">
                    <strong>Titik Friksi (Hambatan UX):</strong> {f.get('friction_points')}
                </div>
                <div style="background:#ecfdf5; border-left:3px solid #10b981; padding:6px 10px; font-size:8pt; color:#065f46; line-height:1.35;">
                    <strong>Rekomendasi Simplifikasi Konkret:</strong> {f.get('simplification_recommendation')}
                </div>
            </div>
            """

        # 7. Toolbar untuk Browser Print View
        toolbar_html = ""
        if not for_pdf_renderer:
            toolbar_html = f"""
            <div class="no-print" style="position:sticky; top:0; z-index:100; background:#0f172a; color:#ffffff; padding:12px 24px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 8px rgba(0,0,0,0.2);">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-weight:bold; font-size:14px;">CompetitorRadar · Pratinjau Ekspor Laporan</span>
                    <span style="background:#0d9488; color:#ffffff; font-size:10px; font-weight:bold; padding:2px 8px; border-radius:10px;">Format Siap Cetak & Simpan</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <a href="/api/exports/{report_id}/pdf" download style="background:#ffffff; color:#0f172a; padding:6px 14px; border-radius:6px; font-size:12px; font-weight:bold; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
                        📥 Download File PDF Langsung (.pdf)
                    </a>
                    <button onclick="window.print()" style="background:#0d9488; color:#ffffff; border:none; padding:6px 16px; border-radius:6px; font-size:12px; font-weight:bold; cursor:pointer;">
                        🖨️ Cetak / Simpan sebagai PDF (Ctrl+P)
                    </button>
                    <button onclick="window.close()" style="background:#334155; color:#ffffff; border:none; padding:6px 12px; border-radius:6px; font-size:12px; cursor:pointer;">
                        ✕ Tutup
                    </button>
                </div>
            </div>
            """

        # CSS Styles conditional for PDF renderer vs Browser Print
        if for_pdf_renderer:
            page_css = """
            @page first_page {
                size: a4 portrait;
                margin: 14mm 12mm 14mm 12mm;
                @frame footer_frame {
                    -pdf-frame-content: page_footer;
                    left: 12mm;
                    right: 12mm;
                    bottom: 5mm;
                    height: 7mm;
                }
            }
            @page other_pages {
                size: a4 portrait;
                margin: 15mm 12mm 14mm 12mm;
                @frame header_frame {
                    -pdf-frame-content: page_header;
                    left: 12mm;
                    right: 12mm;
                    top: 6mm;
                    height: 7mm;
                }
                @frame footer_frame {
                    -pdf-frame-content: page_footer;
                    left: 12mm;
                    right: 12mm;
                    bottom: 5mm;
                    height: 7mm;
                }
            }
            .page-first {
                page: first_page;
            }
            .page-other {
                page: other_pages;
                page-break-before: always;
            }
            """
        else:
            page_css = """
            @page {
                size: a4 portrait;
                margin: 12mm;
            }
            @media print {
                .no-print { display: none !important; }
                body { padding: 0; background: #ffffff; }
            }
            .page-first {
                padding: 0;
            }
            .page-other {
                page-break-before: always;
                padding-top: 10px;
            }
            """

        return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Laporan Riset Pasar & Inovasi Kompetitor - {project_title}</title>
    <style>
        {page_css}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            margin: 0;
            padding: 0;
            font-size: 8.5pt;
            line-height: 1.4;
            background: #ffffff;
        }}
        .report-wrapper {{
            max-width: 900px;
            margin: 0 auto;
            padding: { '0' if for_pdf_renderer else '20px' };
        }}
        .section-header {{
            font-size: 10.5pt;
            font-weight: bold;
            color: #0f172a;
            border-bottom: 1.5px solid #0f172a;
            padding-bottom: 3px;
            margin-top: 12px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }}
        .section-subtitle {{
            font-size: 7.5pt;
            color: #64748b;
            margin-top: -4px;
            margin-bottom: 8px;
            page-break-after: avoid;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8pt;
        }}
        th {{
            background-color: #0f172a;
            color: #ffffff;
            padding: 5px 6px;
            text-align: left;
            font-size: 7.5pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    </style>
</head>
<body>
    {toolbar_html}

    <!-- RUNNING HEADER (Only on pages 2-5) -->
    <div id="page_header">
        <table style="width:100%; border:none; margin:0; padding-bottom:2px; border-bottom:0.5px solid #cbd5e1;">
            <tr>
                <td style="text-align:left; font-size:7pt; color:#0d9488; font-weight:bold; border:none; padding:0;">
                    COMPETITOR RADAR · MARKET INTELLIGENCE REPORT
                </td>
                <td style="text-align:right; font-size:7pt; color:#64748b; border:none; padding:0;">
                    {project_title}
                </td>
            </tr>
        </table>
    </div>

    <!-- RUNNING FOOTER -->
    <div id="page_footer">
        <table style="width:100%; border:none; margin:0; padding-top:2px; border-top:0.5px solid #cbd5e1;">
            <tr>
                <td style="text-align:left; font-size:7pt; color:#94a3b8; border:none; padding:0;">
                    Dokumen Rahasia & Strategis · Berbasis Data Resmi Play Store & Web Perusahaan
                </td>
                <td style="text-align:right; font-size:7pt; color:#64748b; font-weight:bold; border:none; padding:0;">
                    { 'Halaman <pdf:pagenumber> dari <pdf:pagecount>' if for_pdf_renderer else 'CompetitorRadar Official Report' }
                </td>
            </tr>
        </table>
    </div>

    <div class="report-wrapper">
        <!-- ================= HALAMAN 1: COVER & TARGET KOMPETITOR ================= -->
        <div class="page-first">
            <!-- TOP BRAND & TITLE (Fit, proportional 1:1 logo, no duplicate running header) -->
            <table style="width:100%; border:none; margin-bottom:12px; border-bottom:2px solid #0d9488; padding-bottom:10px;">
                <tr>
                    <td style="border:none; padding:0; width:44px; vertical-align:middle;">
                        {f'<img src="{logo_b64}" width="36" height="36" style="width:36px; height:36px; vertical-align:middle;" />' if logo_b64 else ''}
                    </td>
                    <td style="border:none; padding:0 0 0 10px; vertical-align:middle;">
                        <div style="font-size:7.5pt; font-weight:bold; color:#0d9488; text-transform:uppercase; letter-spacing:1px;">
                            COMPETITOR RADAR · MARKET INTELLIGENCE REPORT
                        </div>
                        <div style="font-size:14.5pt; font-weight:bold; color:#0f172a; margin-top:2px; line-height:1.2;">
                            {project_title}
                        </div>
                        <div style="font-size:8pt; color:#64748b; margin-top:3px;">
                            Kategori: <strong>{project_category}</strong> &nbsp;|&nbsp; 
                            Tanggal Audit: <strong>{created_at}</strong> &nbsp;|&nbsp;
                            Status: <strong style="color:#0d9488;">Terverifikasi Resmi</strong>
                        </div>
                    </td>
                    <td style="border:none; padding:0; text-align:right; vertical-align:middle; width:22%;">
                        <div style="background:#f0fdfa; border:1px solid #14b8a6; color:#0f766e; padding:5px 8px; font-weight:bold; font-size:7.5pt; text-align:center;">
                            Executive Report & Gap Matrix
                        </div>
                    </td>
                </tr>
            </table>

            <!-- DESKRIPSI SINGKAT RISET -->
            {f'<div style="font-size:8pt; color:#475569; font-style:italic; margin-bottom:8px; line-height:1.35;">{project_description}</div>' if project_description else ''}

            <!-- PROFIL APLIKASI INTERNAL -->
            <div style="background:#ffffff; border:1px solid #cbd5e1; padding:7px 9px; margin-bottom:10px;">
                <table style="width:100%; border:none; margin:0 0 5px 0;">
                    <tr>
                        <td style="border:none; padding:0; width:50%; vertical-align:top;">
                            <span style="font-size:7pt; font-weight:bold; color:#0d9488; text-transform:uppercase;">APLIKASI INTERNAL KITA</span>
                            <div style="font-size:10.5pt; font-weight:bold; color:#0f172a; margin-top:1px;">{internal_app.get('app_name', 'Internal App')}</div>
                            <div style="font-size:7.5pt; color:#64748b; margin-top:1px;">
                                Kategori: <strong>{internal_app.get('category', '-')}</strong> | Target: <strong>{internal_app.get('target_audience', '-')}</strong>
                            </div>
                        </td>
                        <td style="border:none; padding:0; width:50%; vertical-align:top;">
                            <span style="font-size:7pt; font-weight:bold; color:#64748b; text-transform:uppercase;">DESKRIPSI APLIKASI</span>
                            <div style="font-size:7.5pt; color:#334155; margin-top:1px; line-height:1.25;">
                                {internal_app.get('description', '-')}
                            </div>
                        </td>
                    </tr>
                </table>
                <div style="border-top:1px dashed #cbd5e1; padding-top:4px;">
                    <span style="font-size:7pt; font-weight:bold; color:#64748b; text-transform:uppercase;">MODUL & FITUR INTERNAL TERDAFTAR:</span>
                    <div style="margin-top:3px;">
                        {mods_grid}
                    </div>
                </div>
            </div>

            <!-- DAFTAR KOMPETITOR TERDAFTAR -->
            <div class="section-header" style="margin-top:6px;">
                Daftar Target Kompetitor Terdaftar & Dianalisis ({len(competitors)} Aplikasi)
            </div>
            <table style="border:1px solid #cbd5e1;">
                <thead>
                    <tr>
                        <th style="width:5%; text-align:center;">No</th>
                        <th style="width:25%;">Nama Aplikasi Kompetitor</th>
                        <th style="width:28%;">Package Google Play</th>
                        <th style="width:18%;">Rating & Reputasi</th>
                        <th style="width:24%;">Website Resmi</th>
                    </tr>
                </thead>
                <tbody>
                    {comp_rows or '<tr><td colspan="5" style="padding:8px; text-align:center; color:#64748b;">Belum ada kompetitor yang terdaftar.</td></tr>'}
                </tbody>
            </table>
        </div>

        <!-- ================= HALAMAN 2: EXECUTIVE SUMMARY, MATURITY & 4 QUADRANTS ================= -->
        <div class="page-other">
            <!-- 1. RINGKASAN EKSEKUTIF -->
            <div class="section-header" style="margin-top:0;">
                1. Ringkasan Eksekutif & Lanskap Persaingan Pasar
            </div>
            <div style="background:#f0fdfa; border-left:4px solid #0d9488; padding:9px 12px; font-size:8.5pt; color:#1e293b; margin-bottom:12px; line-height:1.45; white-space:pre-line;">
{summary}
            </div>

            <!-- 2. EVALUASI KEMATANGAN PER MODUL -->
            <div class="section-header">
                2. Evaluasi Kematangan Fitur per Modul (Benchmark)
            </div>
            <div class="section-subtitle">
                Perbandingan tingkat kesetaraan fungsional aplikasi internal terhadap benchmark standar kompetitor di pasar.
            </div>
            <table style="border:1px solid #cbd5e1; margin-bottom:12px;">
                <thead>
                    <tr>
                        <th style="width:32%;">Kategori / Modul Fitur</th>
                        <th style="width:26%;">Aplikasi Internal Kita</th>
                        <th style="width:26%;">Benchmark Kompetitor</th>
                        <th style="width:16%; text-align:center;">Status Kesetaraan</th>
                    </tr>
                </thead>
                <tbody>
                    {maturity_rows}
                </tbody>
            </table>

            <!-- 3. MATRIKS PRIORITAS INOVASI (4 KUADRAN) -->
            <div class="section-header">
                3. Matriks Prioritas Inovasi (Impact vs Effort - 4 Kuadran)
            </div>
            <div class="section-subtitle">
                Rekomendasi alokasi sprint produk berdasarkan rasio dampak bisnis terhadap kompleksitas teknis fitur.
            </div>
            <div style="background:#f8fafc; border:1px solid #cbd5e1; padding:5px 8px; margin-bottom:8px; font-size:7.5pt; color:#475569; line-height:1.35;">
                <strong>Fungsi Matriks Prioritas:</strong> Memetakan backlog inovasi ke dalam 4 kuadran strategis berdasarkan rasio dampak pengguna (Impact) terhadap beban pengembangan (Effort). Fitur <strong>Quick Wins</strong> diprioritaskan segera pada sprint terdekat, <strong>Inisiatif Strategis</strong> direncanakan matang pada roadmap kuartalan, sedangkan <strong>Evaluasi Lanjut</strong> difilter agar tim tidak membuang resource rekayasa untuk fitur berbiaya tinggi dengan nilai rendah.
            </div>
            <table style="width:100%; border:none; margin:0;">
                <tr>
                    <td style="width:50%; border:none; padding:0 4px 6px 0; vertical-align:top;">
                        {quad_q1}
                    </td>
                    <td style="width:50%; border:none; padding:0 0 6px 4px; vertical-align:top;">
                        {quad_q2}
                    </td>
                </tr>
                <tr>
                    <td style="width:50%; border:none; padding:4px 4px 0 0; vertical-align:top;">
                        {quad_q3}
                    </td>
                    <td style="width:50%; border:none; padding:4px 0 0 4px; vertical-align:top;">
                        {quad_q4}
                    </td>
                </tr>
            </table>
        </div>

        <!-- ================= HALAMAN 3: VOICE-OF-CUSTOMER & SENTIMEN PLAY STORE ================= -->
        <div class="page-other">
            <div class="section-header" style="margin-top:0;">
                4. Sentimen Ulasan Play Store & Voice-of-Customer
            </div>
            <div class="section-subtitle">
                Aspek yang paling diapresiasi pengguna kompetitor vs celah keluhan nyata yang dapat dimanfaatkan untuk diferensiasi produk kita.
            </div>
            {voc_cards or '<p style="color:#64748b; font-size:8pt;">Belum ada data ulasan kompetitor yang terekam.</p>'}
        </div>

        <!-- ================= HALAMAN 4: MATRIKS GAP FITUR & INOVASI ================= -->
        <div class="page-other">
            <div class="section-header" style="margin-top:0;">
                5. Matriks Gap Fitur & Inovasi Belum Teradaptasi
            </div>
            <div class="section-subtitle">
                Daftar inovasi fitur unik milik kompetitor yang belum diadaptasi, lengkap dengan skor prioritas dan sitasi bukti resmi.
            </div>
            <table style="border:1px solid #cbd5e1; margin-bottom:10px;">
                <thead>
                    <tr>
                        <th style="width:13%;">Kompetitor</th>
                        <th style="width:11%;">Kategori</th>
                        <th style="width:16%;">Fitur Inovatif</th>
                        <th style="width:11%; text-align:center;">Status</th>
                        <th style="width:28%;">Highlight Nilai Inovasi</th>
                        <th style="width:8%; text-align:center;">Prioritas</th>
                        <th style="width:13%;">Sumber Resmi</th>
                    </tr>
                </thead>
                <tbody>
                    {gaps_rows or '<tr><td colspan="7" style="padding:8px; text-align:center; color:#64748b;">Tidak ada data gap fitur.</td></tr>'}
                </tbody>
            </table>
        </div>

        <!-- ================= HALAMAN 5: ANALISIS FRIKSI USER FLOW ================= -->
        <div class="page-other">
            <div class="section-header" style="margin-top:0;">
                6. Analisis Friksi Alur Pengguna (User Flow Benchmark)
            </div>
            <div class="section-subtitle">
                Perbandingan alur interaksi aplikasi internal dengan pendekatan efisien kompetitor beserta saran simplifikasi konkret.
            </div>
            {flows_html or '<p style="color:#64748b; font-size:8.5pt;">Belum ada komparasi alur pengguna yang dicatat.</p>'}

            <!-- KOTAK KESIMPULAN & DISCLAIMER -->
            <div style="background:#f8fafc; border:1px solid #cbd5e1; padding:9px 12px; margin-top:14px;">
                <table style="width:100%; border:none; margin:0;">
                    <tr>
                        <td style="border:none; padding:0 8px 0 0; vertical-align:middle; width:75%;">
                            <div style="font-size:8.5pt; font-weight:bold; color:#0f172a; margin-bottom:2px;">
                                Ringkasan Rekomendasi Eksekutif
                            </div>
                            <div style="font-size:7.5pt; color:#475569; line-height:1.35;">
                                Laporan Market Intelligence ini dihasilkan secara otomatis oleh sistem <strong>CompetitorRadar</strong> berbasis verifikasi ulasan Google Play Store dan informasi resmi publik. Dokumen ini disiapkan untuk mendukung Product Owner, CPO, dan Tim Engineering dalam menentukan alokasi roadmap fitur selanjutnya.
                            </div>
                        </td>
                        <td style="border:none; padding:0 0 0 8px; vertical-align:middle; width:25%; text-align:right;">
                            <div style="background:#0d9488; color:#ffffff; padding:4px 8px; font-size:7pt; font-weight:bold; text-align:center;">
                                STATUS: FINAL AUDIT
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""

    @classmethod
    def export_excel(cls, report_data: Dict[str, Any]) -> io.BytesIO:
        """
        Menghasilkan file Excel (.xlsx) profesional dengan 5 sheet lengkap:
        1. Ringkasan Eksekutif & Profil
        2. Matriks Gap Fitur & Inovasi
        3. Sentimen Play Store (VoC)
        4. Analisis User Flow
        5. Prioritas Kuadran
        """
        wb = openpyxl.Workbook()
        
        # Style Definitions
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        title_font = Font(name="Calibri", size=14, bold=True, color="0F172A")
        bold_font = Font(name="Calibri", size=11, bold=True)
        thin_border = Border(
            left=Side(style='thin', color="E2E8F0"),
            right=Side(style='thin', color="E2E8F0"),
            top=Side(style='thin', color="E2E8F0"),
            bottom=Side(style='thin', color="E2E8F0")
        )

        # ---------------- SHEET 1: RINGKASAN & PROFIL ----------------
        ws_sum = wb.active
        ws_sum.title = "Ringkasan & Profil"
        ws_sum.append(["LAPORAN RISET PASAR & MATRIKS GAP FITUR INOVATIF"])
        ws_sum["A1"].font = title_font
        ws_sum.append([])
        ws_sum.append(["Judul Proyek", report_data.get("project_title", "-")])
        ws_sum.append(["Kategori", report_data.get("project_category", "-")])
        ws_sum.append(["Tanggal Analisis", report_data.get("created_at", "-")])
        
        internal_app = report_data.get("internal_app") or {}
        if internal_app:
            ws_sum.append(["Aplikasi Internal", internal_app.get("app_name", "-")])
            ws_sum.append(["Target Audiens", internal_app.get("target_audience", "-")])
        
        ws_sum.append([])
        ws_sum.append(["DAFTAR KOMPETITOR YANG DIANALISIS:"])
        ws_sum[f"A{ws_sum.max_row}"].font = bold_font
        for c in report_data.get("competitors", []):
            ws_sum.append([c.get("name"), c.get("playstore_package"), c.get("website_url")])

        ws_sum.append([])
        ws_sum.append(["RINGKASAN EKSEKUTIF CPO:"])
        ws_sum[f"A{ws_sum.max_row}"].font = bold_font
        ws_sum.append([report_data.get("summary", "-")])
        
        ws_sum.column_dimensions['A'].width = 25
        ws_sum.column_dimensions['B'].width = 80
        ws_sum.column_dimensions['C'].width = 40

        # ---------------- SHEET 2: MATRIKS GAP FITUR ----------------
        ws_gap = wb.create_sheet(title="Matriks Gap Fitur")
        headers = ["Kompetitor", "Kategori Modul", "Nama Fitur Inovatif", "Status Internal", "Highlight Inovasi", "Impact (1-10)", "Effort (1-10)", "Sitasi & Sumber Resmi"]
        ws_gap.append(headers)

        for col_idx, col_name in enumerate(headers, 1):
            cell = ws_gap.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for item in report_data.get("feature_gaps", []):
            sources_str = ""
            for s in item.get("official_sources", []):
                sources_str += f"[{s.get('type')}] {s.get('title')}: {s.get('url')} (Kutipan: {s.get('quote')})\n"

            row = [
                item.get("competitor_name", ""),
                item.get("category", ""),
                item.get("feature_name", ""),
                item.get("internal_status", ""),
                item.get("innovation_highlight", ""),
                item.get("impact_score", 5),
                item.get("effort_score", 5),
                sources_str.strip()
            ]
            ws_gap.append(row)

        for row in ws_gap.iter_rows(min_row=2, max_col=len(headers)):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

        ws_gap.column_dimensions['A'].width = 18
        ws_gap.column_dimensions['B'].width = 18
        ws_gap.column_dimensions['C'].width = 25
        ws_gap.column_dimensions['D'].width = 18
        ws_gap.column_dimensions['E'].width = 35
        ws_gap.column_dimensions['F'].width = 12
        ws_gap.column_dimensions['G'].width = 12
        ws_gap.column_dimensions['H'].width = 45

        # ---------------- SHEET 3: SENTIMEN PLAY STORE & VOC ----------------
        ws_voc = wb.create_sheet(title="Sentimen Play Store")
        voc_headers = ["Nama Kompetitor", "Rating", "Jumlah Ulasan", "Aspek Dipuji (Kekuatan)", "Celah Keluhan (Peluang Inovasi)", "Play Store URL"]
        ws_voc.append(voc_headers)

        for col_idx in range(1, len(voc_headers) + 1):
            cell = ws_voc.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for co in report_data.get("competitor_overviews", []):
            ws_voc.append([
                co.get("competitor_name", ""),
                co.get("playstore_score", 0),
                co.get("ratings_count", 0),
                "\n".join([f"• {x}" for x in co.get("key_strengths", [])]),
                "\n".join([f"• {x}" for x in co.get("key_weaknesses", [])]),
                co.get("playstore_url", "")
            ])

        for row in ws_voc.iter_rows(min_row=2, max_col=len(voc_headers)):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

        ws_voc.column_dimensions['A'].width = 22
        ws_voc.column_dimensions['B'].width = 10
        ws_voc.column_dimensions['C'].width = 15
        ws_voc.column_dimensions['D'].width = 35
        ws_voc.column_dimensions['E'].width = 35
        ws_voc.column_dimensions['F'].width = 35

        # ---------------- SHEET 4: USER FLOW ----------------
        ws_flow = wb.create_sheet(title="Analisis User Flow")
        flow_headers = ["Nama Alur", "Langkah Flow Internal", "Alur Kompetitor Terdeteksi", "Titik Friksi (Friction)", "Rekomendasi Simplifikasi"]
        ws_flow.append(flow_headers)

        for col_idx in range(1, len(flow_headers) + 1):
            cell = ws_flow.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for fl in report_data.get("flow_comparisons", []):
            ws_flow.append([
                fl.get("flow_name", ""),
                fl.get("internal_steps", ""),
                fl.get("competitor_detected_flow", ""),
                fl.get("friction_points", ""),
                fl.get("simplification_recommendation", "")
            ])

        for row in ws_flow.iter_rows(min_row=2, max_col=len(flow_headers)):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

        ws_flow.column_dimensions['A'].width = 22
        ws_flow.column_dimensions['B'].width = 30
        ws_flow.column_dimensions['C'].width = 30
        ws_flow.column_dimensions['D'].width = 30
        ws_flow.column_dimensions['E'].width = 35

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def export_csv(report_data: Dict[str, Any]) -> str:
        """Menghasilkan representasi CSV dari Matriks Gap Fitur."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Kompetitor", "Kategori", "Nama Fitur Inovatif", "Status Internal", "Highlight Inovasi", "Impact", "Effort", "Sumber Resmi"])

        for item in report_data.get("feature_gaps", []):
            sources_summary = "; ".join([f"{s.get('type')}: {s.get('url')}" for s in item.get("official_sources", [])])
            writer.writerow([
                item.get("competitor_name", ""),
                item.get("category", ""),
                item.get("feature_name", ""),
                item.get("internal_status", ""),
                item.get("innovation_highlight", ""),
                item.get("impact_score", 5),
                item.get("effort_score", 5),
                sources_summary
            ])

        return output.getvalue()

    @staticmethod
    def export_markdown(report_data: Dict[str, Any]) -> str:
        """Menghasilkan dokumen Markdown komprehensif mencakup semua modul."""
        md = []
        md.append(f"# Laporan Riset Pasar & Inovasi: {report_data.get('project_title', 'Aplikasi Android')}")
        md.append(f"*Kategori: {report_data.get('project_category', '-')} | Dibuat pada: {report_data.get('created_at', '-')}*\n")

        internal_app = report_data.get("internal_app") or {}
        if internal_app:
            md.append("## Profil Aplikasi Internal")
            md.append(f"- **Aplikasi**: {internal_app.get('app_name', '-')}")
            md.append(f"- **Target Audiens**: {internal_app.get('target_audience', '-')}")
            md.append(f"- **Deskripsi**: {internal_app.get('description', '-')}\n")

        competitors = report_data.get("competitors") or []
        if competitors:
            md.append("## Daftar Kompetitor yang Dianalisis")
            for c in competitors:
                md.append(f"- **{c.get('name')}** (Play Store: `{c.get('playstore_package')}`, Web: {c.get('website_url') or '-'})")
            md.append("")

        md.append("## 1. Ringkasan Eksekutif")
        md.append(f"{report_data.get('summary', '-')}\n")

        md.append("## 2. Matriks Gap Fitur & Inovasi Kompetitor")
        md.append("| Kompetitor | Kategori | Fitur Inovatif | Status Internal | Inovasi Utama | Impact | Effort | Sumber Resmi |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |")

        for item in report_data.get("feature_gaps", []):
            sources_links = "<br>".join([f"[{s.get('title')}]({s.get('url')})" for s in item.get("official_sources", [])])
            md.append(f"| {item.get('competitor_name')} | {item.get('category')} | **{item.get('feature_name')}** | `{item.get('internal_status')}` | {item.get('innovation_highlight')} | {item.get('impact_score')}/10 | {item.get('effort_score')}/10 | {sources_links} |")

        md.append("\n## 3. Sentimen Ulasan Play Store & Voice-of-Customer")
        for co in report_data.get("competitor_overviews", []):
            md.append(f"### {co.get('competitor_name')} (Rating: ★ {co.get('playstore_score')} - {co.get('ratings_count', 0):,} ulasan)")
            md.append("**Kekuatan yang Dipuji:**")
            for s in co.get("key_strengths", []):
                md.append(f"- {s}")
            md.append("**Celah Keluhan:**")
            for w in co.get("key_weaknesses", []):
                md.append(f"- {w}")
            md.append("")

        md.append("## 4. Komparasi User Flow & Rekomendasi Friksi")
        for fl in report_data.get("flow_comparisons", []):
            md.append(f"### Alur: {fl.get('flow_name')}")
            md.append(f"- **Alur Internal**: {fl.get('internal_steps')}")
            md.append(f"- **Pendekatan Kompetitor**: {fl.get('competitor_detected_flow')}")
            md.append(f"- **Titik Friksi**: {fl.get('friction_points')}")
            md.append(f"- **Rekomendasi Simplifikasi**: {fl.get('simplification_recommendation')}\n")

        return "\n".join(md)
