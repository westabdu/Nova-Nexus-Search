# backend/app/services/search_engine.py
"""
DeepSearchEngine - DuckDuckGo + Jina Reader + BeautifulSoup + Derin Tarama + Otorite Puanı
"""
from ddgs import DDGS
import httpx
import asyncio
from loguru import logger
from typing import Callable, Optional, List, Dict
from bs4 import BeautifulSoup
import re

class DeepSearchEngine:
    def __init__(self):
        self.jina_base_url = "https://r.jina.ai/"
        self.domain_authority = {
            ".gov": 10, ".edu": 9, ".org": 7, ".com": 5, ".net": 4, ".info": 3,
            "wikipedia.org": 8, "who.int": 9, "un.org": 9, "worldbank.org": 8,
            "imf.org": 8, "ec.europa.eu": 9, "europa.eu": 8, "coe.int": 8,
            "oecd.org": 8, "nato.int": 8, "icj-cij.org": 9, "icrc.org": 8,
            "hrw.org": 7, "amnesty.org": 7, "state.gov": 8, "defense.gov": 8,
            "treasury.gov": 8, "cia.gov": 7, "fbi.gov": 7, "interpol.int": 8,
            "europol.europa.eu": 8, "unodc.org": 8
        }
        self.blacklist_domains = ["facebook.com", "twitter.com", "instagram.com", "reddit.com", "pinterest.com", "tiktok.com"]
    
    def _get_authority_score(self, url: str) -> int:
        """Kaynağın otorite puanını hesapla (1-10)"""
        domain = url.lower()
        for pattern, score in self.domain_authority.items():
            if pattern in domain:
                return score
        if any(bad in domain for bad in self.blacklist_domains):
            return 1
        return 4  # Varsayılan
    
    async def fetch_url_with_fallback(self, url: str) -> Dict:
        """Jina önce, başarısızsa BeautifulSoup ile içerik al"""
        content = ""
        # Önce Jina
        jina_url = f"{self.jina_base_url}{url}"
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            try:
                resp = await client.get(jina_url, headers={"Accept": "text/plain"})
                if resp.status_code == 200:
                    content = resp.text
                    if len(content.strip()) > 200:
                        await asyncio.sleep(1)
                        return {"url": url, "content": content[:15000], "source": "jina"}
            except: pass
        
        # Jina başarısızsa BeautifulSoup
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    text = soup.get_text(separator=' ', strip=True)
                    content = text[:15000]
                    return {"url": url, "content": content, "source": "bs4"}
        except: pass
        
        return {"url": url, "content": "", "source": "none"}
    
    async def deep_search(self, query: str, max_results: int = 10, authority_threshold: int = 5) -> List[Dict]:
        """Otorite puanı yüksek kaynakları öne çıkaran derin arama"""
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results*2):
                    url = r.get('href') or r.get('url', '')
                    authority = self._get_authority_score(url)
                    results.append({
                        "url": url,
                        "title": r.get('title', url),
                        "snippet": r.get('body', ''),
                        "authority": authority
                    })
        except Exception as e:
            logger.error(f"DDGS error: {e}")
        
        # Otorite puanına göre filtrele ve sırala
        filtered = [r for r in results if r["authority"] >= authority_threshold]
        sorted_results = sorted(filtered, key=lambda x: x["authority"], reverse=True)
        
        # İçerikleri getir
        final_docs = []
        for res in sorted_results[:max_results]:
            content_data = await self.fetch_url_with_fallback(res["url"])
            if content_data["content"]:
                final_docs.append({
                    "url": res["url"],
                    "title": res["title"],
                    "content": content_data["content"],
                    "authority": res["authority"],
                    "relevance_score": 0
                })
            await asyncio.sleep(0.5)
        
        return final_docs

    # ============ ESKİ METHODLAR (Uyumluluk için) ============
    
    def _sync_ddgs_search(self, query: str, max_results: int, timelimit: Optional[str]) -> list:
        """Senkron DDGS çağrısını izole eder."""
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results, timelimit=timelimit):
                    results.append(r)
        except Exception as e:
            logger.error(f"DDG Sync Search failed for '{query}': {e}")
        return results

    async def search_duckduckgo(self, query: str, max_results: int = 10, time_filter: str = "all", domain_filter: str = "all") -> list:
        final_query = query
        if domain_filter and domain_filter != "all":
            final_query += f" site:{domain_filter}"

        timelimit = None
        if time_filter == "1y": timelimit = "y"
        elif time_filter == "1m": timelimit = "m"
        elif time_filter == "1w": timelimit = "w"
        elif time_filter == "1d": timelimit = "d"

        results = await asyncio.to_thread(self._sync_ddgs_search, final_query, max_results, timelimit)
        
        if not results:
            logger.info(f"DDG retry without filters for '{query}'")
            results = await asyncio.to_thread(self._sync_ddgs_search, query, max_results, None)
            
        return results

    async def fetch_url_markdown_jina(self, url: str) -> str:
        jina_url = f"{self.jina_base_url}{url}"
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            try:
                response = await client.get(jina_url, headers={"Accept": "text/plain"})
                response.raise_for_status()
                text = response.text
                if text and len(text.strip()) > 100:
                    await asyncio.sleep(1.0)
                    return text
            except Exception as e:
                logger.debug(f"Jina failed [{url[:50]}...]: {e}")
        
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                text = soup.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return text[:15000]
        except Exception as e:
            logger.debug(f"Direct fetch also failed [{url[:50]}...]: {e}")
        
        return ""

    async def process_search_queries(
        self, queries: list, max_per_query: int = 10, max_total: int = 20,
        progress_callback: Optional[Callable] = None, time_filter: str = "all",
        domain_filter: str = "all", cancel_check: Optional[Callable] = None
    ) -> list:
        async def _notify(msg):
            if progress_callback:
                import inspect
                res = progress_callback(msg)
                if inspect.isawaitable(res):
                    await res

        def _is_cancelled():
            return cancel_check and cancel_check()

        all_links = {}
        for i, query in enumerate(queries, 1):
            if _is_cancelled(): return []
            await _notify(f"🔍 Sorgu {i}/{len(queries)} aranıyor: '{query[:50]}...'")
            
            search_results = await self.search_duckduckgo(
                query, max_results=max_per_query, time_filter=time_filter, domain_filter=domain_filter
            )
            for res in search_results:
                href = res.get('href') or res.get('url', '')
                if href and href not in all_links:
                    all_links[href] = res.get('title', href)
            await asyncio.sleep(1.5)

        if _is_cancelled(): return []

        total_links = list(all_links.items())[:max_total]
        await _notify(f"🌐 Toplam {len(total_links)} benzersiz kaynak bulundu, içerikler indiriliyor...")

        documents = []
        batch_size = 5
        for batch_start in range(0, len(total_links), batch_size):
            if _is_cancelled(): return documents
            batch = total_links[batch_start:batch_start + batch_size]
            tasks = [self._fetch_one(url, title, batch_start + idx + 1, len(total_links), _notify) 
                     for idx, (url, title) in enumerate(batch)]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, dict) and r:
                    documents.append(r)

        return documents

    async def _fetch_one(self, url, title, idx, total, notify):
        await notify(f"📄 [{idx}/{total}] İndiriliyor: {title[:60]}")
        content = await self.fetch_url_markdown_jina(url)
        if content and len(content.strip()) > 100:
            authority = self._get_authority_score(url)
            return {"url": url, "title": title, "content": content, "relevance_score": 0, "authority": authority}
        return {}