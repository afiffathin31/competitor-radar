from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import json
from server_app.core.config import settings
from server_app.core.database import init_db, engine
from sqlmodel import Session, select
from server_app.models.models import Project, InternalApp, Competitor
from server_app.api.routers import projects, internal_app, competitors, analysis, exports, settings as api_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_sample_data():
    """
    Mengisi data awal sampel proyek riset jika database masih kosong.
    """
    with Session(engine) as session:
        existing = session.exec(select(Project)).first()
        if existing:
            return

        logger.info("Database kosong. Memasukkan data inisial sampel riset...")
        sample_proj = Project(
            title="Benchmark Aplikasi Quick Commerce & Retail 2026",
            category="Retail & E-Commerce",
            description="Riset komprehensif inovasi fitur pemesanan instan, alur checkout, dan program loyalitas pelanggan."
        )
        session.add(sample_proj)
        session.commit()
        session.refresh(sample_proj)

        # Internal App Baseline
        sample_internal = InternalApp(
            project_id=sample_proj.id,
            app_name="TokoKita Mobile",
            category="Quick Commerce & Groceries",
            description="Aplikasi belanja kebutuhan sehari-hari dengan pengiriman cepat 1-2 jam.",
            target_audience="Ibu rumah tangga, profesional muda perkotaan yang butuh belanja praktis.",
            modules_features_json=json.dumps([
                {
                    "module_name": "Katalog & Pencarian",
                    "features": [
                        {"name": "Pencarian Teks Manual", "description": "Mencari produk berdasarkan nama SKU"},
                        {"name": "Filter Kategori & Harga", "description": "Menyaring produk berdasarkan kategori dan rentang harga"}
                    ]
                },
                {
                    "module_name": "Checkout & Pembayaran",
                    "features": [
                        {"name": "Transfer Bank Manual", "description": "Pembayaran dengan konfirmasi upload bukti transfer"},
                        {"name": "Virtual Account Otomatis", "description": "Pembayaran VA bank BCA/Mandiri/BRI"},
                        {"name": "Voucher Kupon Manual", "description": "Pengguna harus mengetikkan kode promo manual"}
                    ]
                },
                {
                    "module_name": "Pengiriman & Logistik",
                    "features": [
                        {"name": "Pilihan Kurir Standar", "description": "Pengiriman same-day atau reguler"},
                        {"name": "Status Pesanan Statis", "description": "Update status: Diproses -> Dikirim -> Selesai"}
                    ]
                }
            ], ensure_ascii=False),
            user_flows_json=json.dumps([
                {
                    "flow_name": "Alur Pembelian & Checkout",
                    "steps": [
                        "1. Pilih barang dari katalog",
                        "2. Masuk ke halaman keranjang belanja",
                        "3. Masukkan kode kupon diskon manual",
                        "4. Pilih alamat pengiriman dari daftar",
                        "5. Pilih opsi kurir ekspedisi",
                        "6. Pilih metode pembayaran Virtual Account",
                        "7. Buka aplikasi m-banking dan bayar dalam 2 jam",
                        "8. Menunggu konfirmasi verifikasi admin"
                    ],
                    "notes": "Alur cukup panjang (8 langkah) dengan potensi drop-off tinggi saat bayar ke m-banking."
                },
                {
                    "flow_name": "Registrasi Pengguna Baru",
                    "steps": [
                        "1. Buka aplikasi TokoKita",
                        "2. Input nomor telepon",
                        "3. Tunggu kode OTP via SMS",
                        "4. Isi nama lengkap, email, tanggal lahir, dan alamat rumah",
                        "5. Buat PIN 6 digit",
                        "6. Masuk ke Beranda"
                    ],
                    "notes": "Form profil lengkap wajib diisi di awal sebelum bisa browsing produk."
                }
            ], ensure_ascii=False)
        )
        session.add(sample_internal)

        # Competitor Samples
        comp1 = Competitor(
            project_id=sample_proj.id,
            name="Astro - Quick Commerce",
            playstore_package="com.astronauts.app",
            website_url="https://astronauts.id",
            extra_urls_json=json.dumps(["https://astronauts.id/blog"])
        )
        comp2 = Competitor(
            project_id=sample_proj.id,
            name="Alfamagift",
            playstore_package="com.alfamart.alfagift",
            website_url="https://alfagift.id",
            extra_urls_json=json.dumps(["https://alfagift.id/promo"])
        )
        session.add(comp1)
        session.add(comp2)
        session.commit()
        logger.info("Data sampel awal berhasil diinisialisasi.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_sample_data()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(internal_app.router, prefix="/api")
app.include_router(competitors.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(api_settings.router, prefix="/api")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

@app.get("/api/health")
def healthcheck():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Abaikan prefix api
        if full_path.startswith("api/"):
            return None
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

