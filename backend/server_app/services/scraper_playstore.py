from typing import Dict, Any, List
import logging
from google_play_scraper import app as gp_app, reviews as gp_reviews, search as gp_search, Sort

logger = logging.getLogger(__name__)

class PlayStoreScraper:
    @staticmethod
    def search_competitor_apps(query: str, n_hits: int = 5, lang: str = "id", country: str = "id") -> List[Dict[str, Any]]:
        """
        Mencari aplikasi kompetitor di Google Play Store berdasarkan kata kunci pencarian.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        results = []
        try:
            results = gp_search(clean_query, n_hits=n_hits, lang=lang, country=country)
        except Exception as e:
            logger.warning(f"Pencarian Play Store regional ({lang}-{country}) gagal: {e}, fallback ke en-us...")
            try:
                results = gp_search(clean_query, n_hits=n_hits, lang="en", country="us")
            except Exception as e2:
                logger.error(f"Pencarian Play Store gagal total: {e2}")
                return []

        formatted = []
        for item in results:
            app_id = item.get("appId")
            if not app_id:
                continue

            raw_score = item.get("score")
            score = round(float(raw_score), 1) if raw_score is not None else 0.0

            formatted.append({
                "package_name": app_id,
                "title": item.get("title") or app_id,
                "developer": item.get("developer") or "",
                "score": score,
                "installs": item.get("installs") or "N/A",
                "icon": item.get("icon") or "",
                "description": item.get("description") or "",
                "genre": item.get("genre") or "",
                "playstore_url": f"https://play.google.com/store/apps/details?id={app_id}"
            })

        return formatted

    @staticmethod
    def scrape_app_details(package_name: str, lang: str = "id", country: str = "id") -> Dict[str, Any]:
        """
        Scrape detail metadata aplikasi Google Play Store.
        """
        clean_pkg = package_name.strip()
        playstore_url = f"https://play.google.com/store/apps/details?id={clean_pkg}"
        try:
            # Coba regional ID terlebih dahulu
            data = gp_app(clean_pkg, lang=lang, country=country)
        except Exception:
            try:
                # Fallback ke global / en-us
                data = gp_app(clean_pkg, lang="en", country="us")
            except Exception as e:
                logger.warning(f"Gagal mengambil metadata Play Store untuk {clean_pkg}: {e}")
                return {
                    "package_name": clean_pkg,
                    "title": clean_pkg,
                    "score": 0.0,
                    "ratings": 0,
                    "reviews": 0,
                    "description": "",
                    "recent_changes": "",
                    "playstore_url": playstore_url,
                    "website": "",
                    "error": str(e)
                }

        return {
            "package_name": clean_pkg,
            "title": data.get("title", clean_pkg),
            "summary": data.get("summary", ""),
            "description": data.get("description", ""),
            "score": round(data.get("score") or 0.0, 1),
            "ratings": data.get("ratings") or 0,
            "reviews": data.get("reviews") or 0,
            "installs": data.get("installs", "N/A"),
            "developer": data.get("developer", ""),
            "icon": data.get("icon", ""),
            "recent_changes": data.get("recentChanges", ""),
            "website": data.get("developerWebsite", "") or "",
            "playstore_url": playstore_url
        }

    @staticmethod
    def scrape_app_reviews(package_name: str, count: int = 100, lang: str = "id", country: str = "id") -> Dict[str, Any]:
        """
        Scrape ulasan pengguna Google Play Store dan membagi ulasan ke dalam kategori pujian & keluhan.
        """
        clean_pkg = package_name.strip()
        result_reviews = []
        try:
            rvs, _ = gp_reviews(
                clean_pkg,
                lang=lang,
                country=country,
                sort=Sort.MOST_RELEVANT,
                count=count
            )
            result_reviews = rvs
        except Exception:
            try:
                rvs, _ = gp_reviews(
                    clean_pkg,
                    lang="en",
                    country="us",
                    sort=Sort.MOST_RELEVANT,
                    count=count
                )
                result_reviews = rvs
            except Exception as e:
                logger.warning(f"Gagal mengambil review Play Store {clean_pkg}: {e}")

        praises = []
        complaints = []
        all_cleaned = []

        for r in result_reviews:
            score = r.get("score", 3)
            content = (r.get("content") or "").strip()
            user_name = r.get("userName") or "Pengguna Play Store"
            at_date = str(r.get("at") or "")
            item = {
                "score": score,
                "content": content,
                "user": user_name,
                "date": at_date
            }
            all_cleaned.append(item)
            if score >= 4 and len(content) > 15:
                praises.append(content)
            elif score <= 3 and len(content) > 15:
                complaints.append(content)

        return {
            "total_fetched": len(all_cleaned),
            "reviews": all_cleaned[:count],
            "praises": praises[:20],
            "complaints": complaints[:20]
        }
