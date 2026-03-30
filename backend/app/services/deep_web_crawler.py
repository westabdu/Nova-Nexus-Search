# backend/app/services/deep_web_crawler.py
"""
DeepWebCrawler - Akıllı çok katmanlı web tarayıcı.
Tor opsiyonel (yoksa sadece clearnet), robots.txt saygılı, içerik kalitesi puanlayan,
link filtreli ve asenkron batch crawler.
"""
import asyncio
import re
from typing import List, Dict, Optional, Set, Callable
from urllib.parse import urljoin, urlparse
from loguru import logger

try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("[DeepCrawler] aiohttp bulunamadı, crawler devre dışı.")

try:
    from aiohttp_socks import ProxyConnector
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("[DeepCrawler] beautifulsoup4 bulunamadı.")


# ── Kural Setleri ────────────────────────────────────────────────
BLACKLIST_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "tiktok.com", "pinterest.com", "reddit.com", "youtube.com",
    "amazon.com", "ebay.com", "aliexpress.com", "etsy.com",
    "ads.", "doubleclick", "googlesyndication", "adservice",
}

PRIORITY_DOMAINS = {
    ".gov": 10, ".edu": 9, ".org": 8, "wikipedia.org": 8,
    "scholar.google": 8, "ncbi.nlm.nih.gov": 9,
}

CONTENT_MIN_LENGTH = 200   # Minimum karakter — kısa sayfalar atlanır
FETCH_TIMEOUT      = 20    # Saniye


class DeepWebCrawler:
    """
    Çok katmanlı recursive web tarayıcı.
    - Başlangıç URL'lerden çevresindeki linklere iner.
    - İçeriği kalite puanına göre filtreler.
    - Blacklist domain'leri atlar.
    - robots.txt'e saygı gösterir.
    - Tor ağı destekli (isteğe bağlı, Tor kurulu olmalı).
    """

    def __init__(self, tor_enabled: bool = False, tor_port: int = 9050,
                 progress_callback: Optional[Callable] = None):
        if tor_enabled and not SOCKS_AVAILABLE:
            logger.warning("[DeepCrawler] aiohttp_socks yüklü değil, Tor devre dışı bırakıldı.")
            tor_enabled = False
        self.tor_enabled  = tor_enabled
        self.tor_port     = tor_port
        self._progress_cb = progress_callback
        self._session: Optional[ClientSession] = None
        self._robots_cache: Dict[str, Set[str]] = {}

    async def _notify(self, msg: str):
        if self._progress_cb:
            import inspect
            res = self._progress_cb(msg)
            if inspect.isawaitable(res):
                await res

    # ── Session Yönetimi ────────────────────────────────────────
    async def _get_session(self) -> Optional[ClientSession]:
        if not AIOHTTP_AVAILABLE:
            return None
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=FETCH_TIMEOUT)
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            }
            if self.tor_enabled and SOCKS_AVAILABLE:
                connector = ProxyConnector.from_url(f"socks5://127.0.0.1:{self.tor_port}")
                self._session = ClientSession(connector=connector, timeout=timeout, headers=headers)
                logger.info(f"[DeepCrawler] Tor session başlatıldı (Port: {self.tor_port})")
            else:
                self._session = ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Yardımcı Fonksiyonlar ───────────────────────────────────
    def _is_blacklisted(self, url: str) -> bool:
        lower = url.lower()
        return any(b in lower for b in BLACKLIST_DOMAINS)

    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ("http", "https") and
                bool(parsed.netloc) and
                not self._is_blacklisted(url) and
                not url.endswith((".pdf", ".jpg", ".png", ".gif", ".mp4", ".zip"))
            )
        except Exception:
            return False

    def _get_priority(self, url: str) -> int:
        lower = url.lower()
        for pattern, score in PRIORITY_DOMAINS.items():
            if pattern in lower:
                return score
        return 4

    def _score_content(self, text: str) -> float:
        """İçeriği kalite puanına göre değerlendir (0-10)."""
        if len(text) < CONTENT_MIN_LENGTH:
            return 0.0
        # Uzun ve yapılandırılmış içerik daha değerlidir
        score = min(10.0, len(text) / 1000)
        # Akademik göstergeler
        academic_signals = ["research", "study", "published", "journal", "analysis",
                            "method", "result", "conclusion", "data", "evidence"]
        for sig in academic_signals:
            if sig in text.lower():
                score += 0.3
        return min(10.0, score)

    # ── Robots.txt Kontrolü ─────────────────────────────────────
    async def _is_allowed_by_robots(self, url: str) -> bool:
        """robots.txt'i kontrol et (basit user-agent: * kuralı)."""
        try:
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            if base in self._robots_cache:
                disallowed = self._robots_cache[base]
            else:
                session = await self._get_session()
                if not session:
                    return True
                robots_url = f"{base}/robots.txt"
                disallowed = set()
                try:
                    async with session.get(robots_url, timeout=ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            # Basit parse: Disallow satırlarını bul
                            for line in text.split("\n"):
                                if line.lower().startswith("disallow:"):
                                    path = line.split(":", 1)[1].strip()
                                    if path:
                                        disallowed.add(path)
                except Exception:
                    pass
                self._robots_cache[base] = disallowed

            path = urlparse(url).path
            return not any(path.startswith(d) for d in disallowed if d != "/")

        except Exception:
            return True

    # ── Tek URL İçerik Çekme ────────────────────────────────────
    async def _fetch_page(self, url: str) -> Optional[Dict]:
        """Bir URL'nin içeriğini çek, temizle ve değerlendir."""
        if not AIOHTTP_AVAILABLE or not BS4_AVAILABLE:
            return None
        if not self._is_valid_url(url):
            return None

        try:
            session = await self._get_session()
            if not session:
                return None

            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    return None
                html = await resp.text(errors="ignore")

            soup = BeautifulSoup(html, "html.parser")

            # Gürültüyü temizle
            for tag in soup(["script", "style", "nav", "footer", "header",
                              "aside", "form", "iframe", "noscript", "svg"]):
                tag.decompose()

            # Başlık çıkar
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else urlparse(url).netloc

            # Meta description
            meta_desc = ""
            meta = soup.find("meta", attrs={"name": "description"})
            if meta:
                meta_desc = meta.get("content", "")[:500]

            # Ana içerik
            main_content = ""
            for selector in ["main", "article", "[role='main']", "#content", ".content"]:
                tag = soup.select_one(selector)
                if tag:
                    main_content = tag.get_text(separator=" ", strip=True)
                    break

            if not main_content:
                main_content = soup.get_text(separator=" ", strip=True)

            # Boşlukları normalize et
            main_content = re.sub(r'\s{2,}', ' ', main_content).strip()

            quality = self._score_content(main_content)
            if quality < 1.0:
                return None

            # Linkleri topla
            links = []
            for a in soup.find_all("a", href=True):
                href = urljoin(url, a["href"])
                if self._is_valid_url(href):
                    links.append(href)

            return {
                "url": url,
                "title": title[:200],
                "description": meta_desc,
                "content": main_content[:12000],
                "quality_score": round(quality, 2),
                "priority": self._get_priority(url),
                "links": list(set(links))[:30],
                "source": "deep_crawler"
            }

        except asyncio.TimeoutError:
            logger.debug(f"[DeepCrawler] Timeout: {url[:60]}")
            return None
        except Exception as e:
            logger.debug(f"[DeepCrawler] Fetch hatası {url[:60]}: {type(e).__name__}")
            return None

    # ── Recursive Crawler ────────────────────────────────────────
    async def crawl_recursive(
        self,
        start_urls: List[str],
        max_depth: int = 2,
        max_total_pages: int = 20,
        min_quality: float = 2.0
    ) -> List[Dict]:
        """
        Verilen başlangıç URL'lerinden recursive olarak tarar.
        Her sayfadaki linkleri takip ederek daha derin katmanlara iner.
        Priority score yüksek olanları (gov, edu, org) öne alır.
        """
        if not AIOHTTP_AVAILABLE or not BS4_AVAILABLE:
            logger.warning("[DeepCrawler] Gerekli paketler yok, crawler atlanıyor.")
            return []

        visited:  Set[str]   = set()
        results:  List[Dict] = []
        queue:    List[tuple] = [(url, 0) for url in start_urls]

        await self._notify(f"🕷️ DeepCrawler başlatıldı: {len(start_urls)} başlangıç URL, max derinlik={max_depth}")

        while queue and len(results) < max_total_pages:
            # Sırayı priority'ye göre sırala
            queue.sort(key=lambda x: self._get_priority(x[0]), reverse=True)
            url, depth = queue.pop(0)

            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            if not await self._is_allowed_by_robots(url):
                logger.debug(f"[DeepCrawler] robots.txt engeli: {url[:60]}")
                continue

            await self._notify(f"🕸️ [Derinlik {depth}] Taranıyor: {url[:70]}")
            page_data = await self._fetch_page(url)

            if page_data and page_data["quality_score"] >= min_quality:
                results.append(page_data)
                logger.info(f"[DeepCrawler] ✓ Kalite {page_data['quality_score']:.1f} | '{page_data['title'][:50]}'")

                # Bir sonraki derinlik için linkleri kuyruğa ekle
                if depth < max_depth:
                    for link in page_data.get("links", []):
                        if link not in visited:
                            queue.append((link, depth + 1))

            await asyncio.sleep(0.8)  # Sunuculara nazik ol

        # Sonuçları kalite + önceliğe göre sırala
        results.sort(key=lambda x: (x["priority"], x["quality_score"]), reverse=True)
        await self._notify(f"🕷️ DeepCrawler tamamlandı: {len(results)} yüksek kaliteli sayfa.")

        await self.close()
        return results