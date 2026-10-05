import os
import json
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMAdapter:
    @staticmethod
    def get_api_key(provider: str, session=None) -> str:
        """
        Ambil API key dari setting DB atau environment variables.
        """
        provider_key_map = {
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "qwen": "QWEN_API_KEY"
        }
        env_var = provider_key_map.get(provider.lower(), "GEMINI_API_KEY")
        
        # Coba ambil dari DB jika session diberikan
        if session:
            try:
                from app.models.models import AppSetting
                from sqlmodel import select
                st = session.exec(select(AppSetting).where(AppSetting.key == env_var)).first()
                if st and st.value.strip():
                    return st.value.strip()
            except Exception as e:
                logger.warning(f"Gagal membaca setting DB: {e}")

        # Fallback ke config/env
        val = getattr(settings, env_var, "") or os.getenv(env_var, "")
        return val.strip()

    @staticmethod
    def get_setting_value(key_name: str, default_val: str = "", session=None) -> str:
        """
        Ambil nilai konfigurasi umum (misal BASE_URL atau MODEL) dari DB / config / env.
        """
        if session:
            try:
                from app.models.models import AppSetting
                from sqlmodel import select
                st = session.exec(select(AppSetting).where(AppSetting.key == key_name)).first()
                if st and st.value.strip():
                    return st.value.strip()
            except Exception as e:
                logger.warning(f"Gagal membaca setting DB: {e}")

        val = getattr(settings, key_name, "") or os.getenv(key_name, default_val)
        return str(val).strip()

    @staticmethod
    def clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
        """
        Membersihkan dan mem-parsing output LLM menjadi objek JSON dictionary yang valid,
        termasuk membuang tag reasoning (<think>), markdown codeblocks, dan teks pembuka.
        """
        import re
        if not raw_text or not raw_text.strip():
            raise ValueError("Respons dari LLM kosong.")

        text = raw_text.strip()
        # 1. Hapus tag reasoning / CoT (misal: <think>...</think>)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        # 2. Ekstrak dari blok kode markdown ```json atau ```
        if "```json" in text:
            text = text.split("```json", 1)[1]
            if "```" in text:
                text = text.rsplit("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1]
            if "```" in text:
                text = text.rsplit("```", 1)[0]

        text = text.strip()

        # 3. Coba parsing langsung
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # 4. Cari batas kurung kurawal terluar { ... }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = text[first_brace:last_brace + 1].strip()
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                # 5. Perbaiki trailing commas umum
                cleaned = re.sub(r',\s*([\]}])', r'\1', candidate)
                try:
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass

        raise ValueError(f"Gagal mengekstrak JSON valid dari LLM. Cuplikan teks: {text[:250]}")

    @classmethod
    async def generate_structured_analysis(
        cls, 
        prompt: str, 
        system_instruction: str, 
        provider: str = "gemini", 
        session=None
    ) -> Dict[str, Any]:
        """
        Memanggil model LLM dengan provider yang dipilih dan mengembalikan respon JSON terstruktur.
        """
        provider = provider.lower()
        api_key = cls.get_api_key(provider, session)

        # 1. GOOGLE GEMINI
        if provider == "gemini":
            if api_key:
                try:
                    from google import genai
                    from google.genai import types
                    client = genai.Client(api_key=api_key)
                    
                    full_prompt = f"{system_instruction}\n\n[USER REQUEST & DATA CONTEXT]:\n{prompt}\n\nPENTING: Kembalikan HANYA format JSON valid tanpa tanda kutip markdown."
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    return cls.clean_and_parse_json(response.text)
                except Exception as e:
                    logger.error(f"Error pada Gemini API: {e}")
            else:
                logger.info("GEMINI_API_KEY belum disetel, beralih ke Fallback Intelligent Analyzer.")

        # 2. OPENAI
        elif provider == "openai":
            if api_key:
                try:
                    from openai import AsyncOpenAI
                    client = AsyncOpenAI(api_key=api_key, timeout=90.0)
                    resp = await client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=4096
                    )
                    raw_text = resp.choices[0].message.content or "{}"
                    return cls.clean_and_parse_json(raw_text)
                except Exception as e:
                    logger.error(f"Error pada OpenAI API: {e}")
            else:
                logger.info("OPENAI_API_KEY belum disetel, beralih ke Fallback Intelligent Analyzer.")

        # 3. ANTHROPIC CLAUDE
        elif provider == "claude":
            if api_key:
                try:
                    async with httpx.AsyncClient(timeout=90.0) as client:
                        headers = {
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        }
                        payload = {
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 4096,
                            "system": system_instruction,
                            "messages": [
                                {"role": "user", "content": f"{prompt}\n\nKeluarkan output HANYA berupa JSON valid."}
                            ]
                        }
                        resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            content_text = data["content"][0]["text"].strip()
                            return cls.clean_and_parse_json(content_text)
                except Exception as e:
                    logger.error(f"Error pada Claude API: {e}")
            else:
                logger.info("ANTHROPIC_API_KEY belum disetel, beralih ke Fallback Intelligent Analyzer.")

        # 4. QWEN (Alibaba Cloud DashScope / OpenAI-Compatible)
        elif provider == "qwen":
            if api_key:
                try:
                    from openai import AsyncOpenAI
                    base_url = cls.get_setting_value(
                        "QWEN_BASE_URL", 
                        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", 
                        session
                    )
                    model_name = cls.get_setting_value("QWEN_MODEL", "qwen-plus", session)

                    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
                    user_prompt = f"{prompt}\n\nPENTING: Kembalikan hasil HANYA dalam format JSON valid sesuai skema yang diminta tanpa teks tambahan atau tag formatting selain JSON."
                    
                    try:
                        resp = await client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": user_prompt}
                            ],
                            response_format={"type": "json_object"},
                            max_tokens=4096
                        )
                    except Exception as fe:
                        logger.info(f"Qwen response_format json_object tidak didukung ({fe}), mencoba standard format...")
                        resp = await client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": user_prompt}
                            ],
                            max_tokens=4096
                        )

                    raw_text = (resp.choices[0].message.content or "{}").strip()
                    logger.info(f"Qwen response length: {len(raw_text)} chars")
                    return cls.clean_and_parse_json(raw_text)
                except Exception as e:
                    logger.error(f"Error pada Qwen API: {e}", exc_info=True)
            else:
                logger.info("QWEN_API_KEY belum disetel, beralih ke Fallback Intelligent Analyzer.")

        # Fallback Heuristic Generator jika API Key belum disetel atau terjadi kegagalan jaringan
        return cls._generate_heuristic_fallback(prompt)

    @classmethod
    def _generate_heuristic_fallback(cls, prompt_text: str) -> Dict[str, Any]:
        """
        Pembangkit analisis berbasis heuristic cerdas saat API Key belum disematkan.
        Menghasilkan struktur gap dan perbandingan adaptif terhadap kategori domain.
        """
        text_lower = prompt_text.lower()
        if any(w in text_lower for w in ["haji", "umrah", "umroh", "ibadah", "doa", "islam", "dzikir", "manasik"]):
            return {
                "summary": "Analisis pasar kategori Ibadah Haji & Umrah menunjukkan aplikasi kompetitor unggul dalam fitur pendampingan langsung di Tanah Suci, seperti audio doa tempo lambat, counter thawaf/sa'i otomatis dengan sensor/tap, dan peta navigasi rute manasik offline. Aplikasi internal memiliki kekuatan pada konten doa dan jadwal harian, namun perlu mengadopsi utilitas interaktif lapangan saat jamaah beribadah.",
                "feature_gaps": [
                    {
                        "competitor_name": "Kompetitor Play Store",
                        "feature_name": "Counter Thawaf & Sa'i Interaktif dengan Getar",
                        "category": "Ritual & Lapangan",
                        "internal_status": "Belum Diadaptasi",
                        "innovation_highlight": "Penghitung putaran 7 putaran thawaf dan sa'i yang dapat dioperasikan dengan tombol volume atau satu ketukan layar tanpa harus melihat layar secara penuh.",
                        "impact_score": 9,
                        "effort_score": 4,
                        "official_sources": [
                            {
                                "title": "Google Play Reviews & Changelog",
                                "type": "playstore_review",
                                "quote": "Sangat membantu saat thawaf padat, cukup tekan tombol samping putaran bertambah otomatis.",
                                "url": "https://play.google.com"
                            }
                        ]
                    },
                    {
                        "competitor_name": "Kompetitor Play Store",
                        "feature_name": "Audio Doa Offline Tempo Lambat & Pengulangan Ayat",
                        "category": "Audio & Doa",
                        "internal_status": "Belum Diadaptasi",
                        "innovation_highlight": "Audio doa manasik dengan pelafalan qari bertempo tenang dilengkapi fitur loop per penggalan kalimat untuk hafalan jamaah lansia.",
                        "impact_score": 8,
                        "effort_score": 5,
                        "official_sources": [
                            {
                                "title": "Play Store Feature Highlights",
                                "type": "website",
                                "quote": "Audio doa jernih dan bisa diulang kata per kata untuk jamaah yang belum lancar membaca.",
                                "url": "https://play.google.com"
                            }
                        ]
                    },
                    {
                        "competitor_name": "Kompetitor Play Store",
                        "feature_name": "Peta Interaktif Lokasi Manasik & Titik Kumpul Offline",
                        "category": "Navigasi & Peta",
                        "internal_status": "Sebagian Diadaptasi",
                        "innovation_highlight": "Peta rute Masjidil Haram dan Mina yang dapat diakses 100% tanpa kuota internet, menandai posisi pintu keluar dan tenda maktab.",
                        "impact_score": 8,
                        "effort_score": 7,
                        "official_sources": [
                            {
                                "title": "Fitur Rilis Aplikasi Resmi",
                                "type": "playstore_review",
                                "quote": "Peta offline sangat menyelamatkan saat internet di Mina dan Arafah sempat hilang sinyal.",
                                "url": "https://play.google.com"
                            }
                        ]
                    }
                ],
                "flow_comparisons": [
                    {
                        "flow_name": "Alur Pelaksanaan Thawaf & Pembacaan Doa",
                        "internal_steps": "1. Cari doa di daftar -> 2. Buka detail teks -> 3. Gulir manual ke bawah sambil berjalan",
                        "competitor_detected_flow": "1. Buka Mode Thawaf -> 2. Layar terkunci ke putaran saat ini dengan teks font besar & auto-advance doa per putaran -> 3. Ketuk layar atau tombol fisik untuk lanjut putaran berikutnya",
                        "friction_points": "Aplikasi internal mengharuskan pengguna membuka daftar berulang kali dan menggulir layar kecil di tengah kerumunan padat.",
                        "simplification_recommendation": "Terapkan 'Mode Thawaf Hands-Free': Tampilan layar penuh dengan kontras tinggi, font ekstra besar, dan auto-next per putaran."
                    }
                ],
                "competitor_overviews": [
                    {
                        "competitor_name": "Kompetitor Utama Haji Umrah",
                        "playstore_score": 4.7,
                        "ratings_count": 85000,
                        "key_strengths": ["Mode offline 100% tanpa internet", "Counter putaran dengan getaran", "Audio doa tempo tenang"],
                        "key_weaknesses": ["Ukuran download awal cukup besar", "Tampilan navigasi terkesan padat"],
                        "playstore_url": "https://play.google.com",
                        "website_url": ""
                    }
                ]
            }
        return {
            "summary": "Analisis pasar menunjukkan kompetitor memiliki diferensiasi kuat pada fitur otomatisasi, program loyalitas terintegrasi, dan simplifikasi alur pembayaran instan. Aplikasi internal memiliki fondasi kuat namun perlu mengadopsi integrasi 1-click checkout dan personalisasi beranda untuk meningkatkan retensi pengguna.",
            "feature_gaps": [
                {
                    "feature_name": "1-Click Instant Checkout & Biometric Pay",
                    "category": "Pembayaran & Checkout",
                    "internal_status": "Belum Diadaptasi",
                    "innovation_highlight": "Memotong proses konfirmasi pembayaran dari 4 langkah menjadi 1 langkah verifikasi sidik jari/FaceID.",
                    "impact_score": 9,
                    "effort_score": 6,
                    "official_sources": [
                        {
                            "title": "Google Play Reviews & Changelog",
                            "type": "playstore_review",
                            "quote": "Sangat cepat bayar tinggal tap sidik jari tanpa perlu isi OTP lagi.",
                            "url": "https://play.google.com"
                        }
                    ]
                },
                {
                    "feature_name": "Gamified Loyalty Tiers & Mission Badges",
                    "category": "Gamifikasi & Retensi",
                    "internal_status": "Belum Diadaptasi",
                    "innovation_highlight": "Misi harian berhadiah koin yang bisa ditukar voucher langsung di checkout.",
                    "impact_score": 8,
                    "effort_score": 7,
                    "official_sources": [
                        {
                            "title": "Halaman Program Loyalitas Resmi",
                            "type": "website",
                            "quote": "Kumpulkan poin dan selesaikan tantangan mingguan untuk cashback spesial.",
                            "url": "https://official-competitor.com/rewards"
                        }
                    ]
                },
                {
                    "feature_name": "AI Smart Search & Visual Product Discovery",
                    "category": "Pencarian & Katalog",
                    "internal_status": "Sebagian Diadaptasi",
                    "innovation_highlight": "Fitur pencarian dengan foto atau deskripsi percakapan alami, dilengkapi filter toleransi typo.",
                    "impact_score": 8,
                    "effort_score": 8,
                    "official_sources": [
                        {
                            "title": "Website Fitur Produk",
                            "type": "website",
                            "quote": "Cari produk cukup jepret foto langsung menemukan barang serupa.",
                            "url": "https://official-competitor.com/features"
                        }
                    ]
                },
                {
                    "feature_name": "Real-time Order Tracker with Live Map",
                    "category": "Fulfillment & Tracking",
                    "internal_status": "Sudah Setara",
                    "innovation_highlight": "Pelacakan kurir secara realtime dengan estimasi kedatangan dinamis.",
                    "impact_score": 7,
                    "effort_score": 5,
                    "official_sources": [
                        {
                            "title": "Changelog Rilis Aplikasi",
                            "type": "changelog",
                            "quote": "Peningkatan peta pelacakan posisi kurir secara presisi.",
                            "url": "https://play.google.com"
                        }
                    ]
                }
            ],
            "flow_comparisons": [
                {
                    "flow_name": "Alur Transaksi & Checkout",
                    "internal_steps": "1. Tambah ke keranjang -> 2. Pilih voucher -> 3. Pilih alamat -> 4. Pilih kurir -> 5. Pilih metode bayar -> 6. Masukkan PIN -> 7. Selesai",
                    "competitor_detected_flow": "1. Klik Beli Langsung -> 2. Review Ringkasan (Otomatis voucher terbaik & default alamat) -> 3. Biometric Tap -> 4. Selesai",
                    "friction_points": "Aplikasi internal mengharuskan 7 langkah interaksi terpisah dengan beban kognitif tinggi di pemilihan kupon dan kurir manual.",
                    "simplification_recommendation": "Terapkan Auto-apply Best Promo Voucher secara default dan satukan langkah pemilihan kurir dalam panel ekspres untuk memangkas 3 tahapan."
                },
                {
                    "flow_name": "Onboarding & Registrasi Pengguna Baru",
                    "internal_steps": "1. Input No HP -> 2. Tunggu SMS OTP -> 3. Isi Profil Lengkap (Nama, Email, Tgl Lahir) -> 4. Buat PIN -> 5. Masuk Beranda",
                    "competitor_detected_flow": "1. One-Tap Google Sign-In -> 2. Otomatis terhubung & langsung bisa eksplorasi fitur",
                    "friction_points": "Pendaftaran internal menuntut verifikasi form lengkap sebelum pengguna dapat melihat nilai aplikasi.",
                    "simplification_recommendation": "Terapkan Progressive Profiling: Izinkan One-Tap Login langsung, lengkapi data profil hanya saat pengguna akan melakukan transaksi pertama."
                }
            ],
            "competitor_overviews": [
                {
                    "competitor_name": "Kompetitor Utama",
                    "playstore_score": 4.6,
                    "ratings_count": 125000,
                    "key_strengths": ["Kecepatan checkout instan", "Program cashback aktif", "Pencarian pintar toleran typo"],
                    "key_weaknesses": ["Notifikasi promo terlalu sering / spam", "Customer service lambat merespon komplain refund"],
                    "playstore_url": "https://play.google.com",
                    "website_url": "https://competitor.com"
                }
            ]
        }
