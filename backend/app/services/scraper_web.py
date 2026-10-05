import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class WebScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id,en-US;q=0.9,en;q=0.8"
    }

    @classmethod
    async def scrape_url(cls, url: str) -> Dict[str, Any]:
        """
        Scrape konten tekstual dan proposisi fitur dari sebuah URL website.
        """
        clean_url = url.strip()
        if not clean_url:
            return {"url": url, "title": "", "content": "", "headings": []}

        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=cls.HEADERS) as client:
                resp = await client.get(clean_url)
                if resp.status_code >= 400:
                    return {
                        "url": clean_url,
                        "title": f"HTTP Error {resp.status_code}",
                        "content": "",
                        "headings": [],
                        "error": f"Status code: {resp.status_code}"
                    }
                
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Buang tag yang tidak relevan
                for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
                    tag.decompose()

                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                
                # Ambil meta description
                meta_desc = ""
                meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                if meta_tag and meta_tag.get("content"):
                    meta_desc = meta_tag["content"].strip()

                # Ekstrak headings fitur
                headings = []
                for h in soup.find_all(["h1", "h2", "h3"]):
                    txt = h.get_text(strip=True)
                    if txt and len(txt) > 3 and len(txt) < 120 and txt not in headings:
                        headings.append(txt)

                # Ekstrak poin-poin fitur dalam list
                list_items = []
                for li in soup.find_all("li"):
                    txt = li.get_text(strip=True)
                    if txt and 10 < len(txt) < 200 and txt not in list_items:
                        list_items.append(txt)

                # Ambil paragraf utama
                paragraphs = []
                for p in soup.find_all("p"):
                    txt = p.get_text(strip=True)
                    if txt and len(txt) > 20 and txt not in paragraphs:
                        paragraphs.append(txt)

                # Rangkum teks relevan untuk konteks LLM
                combined_text = f"Meta Description: {meta_desc}\n\n"
                if headings:
                    combined_text += "Fitur & Topik Utama:\n- " + "\n- ".join(headings[:20]) + "\n\n"
                if list_items:
                    combined_text += "Poin Fitur & Layanan:\n- " + "\n- ".join(list_items[:25]) + "\n\n"
                if paragraphs:
                    combined_text += "Deskripsi Produk:\n" + "\n\n".join(paragraphs[:15])

                return {
                    "url": clean_url,
                    "title": title,
                    "meta_description": meta_desc,
                    "headings": headings[:20],
                    "content": combined_text[:10000] # Batas aman teks bersih
                }

        except Exception as e:
            logger.warning(f"Gagal scrape web {clean_url}: {e}")
            return {
                "url": clean_url,
                "title": "",
                "meta_description": "",
                "headings": [],
                "content": "",
                "error": str(e)
            }

    @classmethod
    async def scrape_multiple_urls(cls, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        for u in urls:
            if u and u.strip():
                res = await cls.scrape_url(u.strip())
                results.append(res)
        return results
