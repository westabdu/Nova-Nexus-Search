"""
DeepSearchEngine - DuckDuckGo + Jina Reader & httpx Fallback ile ücretsiz veri kazıyıcı.
Gelişmiş filtreler, progress callback, iptal (cancel) desteği ve retry mantığı ile.
"""
from ddgs import DDGS
import httpx
import asyncio
from loguru import logger
from typing import Callable, Optional


class DeepSearchEngine:
    def __init__(self):
        self.jina_base_url = "https://r.jina.ai/"

    def search_duckduckgo(self, query: str, max_results: int = 10, time_filter: str = "all", domain_filter: str = "all") -> list:
        results = []
        try:
            with DDGS() as ddgs:
                final_query = query
                if domain_filter and domain_filter != "all":
                    final_query += f" site:{domain_filter}"

                timelimit = None
                if time_filter == "1y": timelimit = "y"
                elif time_filter == "1m": timelimit = "m"
                elif time_filter == "1w": timelimit = "w"
                elif time_filter == "1d": timelimit = "d"

                ddgs_gen = ddgs.text(final_query, max_results=max_results, timelimit=timelimit)
                for r in ddgs_gen:
                    results.append(r)
        except Exception as e:
            logger.error(f"DDG Search failed for '{query}': {e}")
        
        # DDG başarısızsa boş sorguyla tekrar dene (rate limit bypass)
        if not results:
            try:
                logger.info(f"DDG retry without filters for '{query}'")
                with DDGS() as ddgs:
                    ddgs_gen = ddgs.text(query, max_results=max_results)
                    for r in ddgs_gen:
                        results.append(r)
            except Exception as e:
                logger.error(f"DDG Retry also failed: {e}")
        
        return results

    async def fetch_url_markdown_jina(self, url: str) -> str:
        """Jina Reader ile sayfa içeriğini çek. Başarısızsa doğrudan httpx ile dene."""
        # Önce Jina dene
        jina_url = f"{self.jina_base_url}{url}"
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            try:
                response = await client.get(jina_url, headers={"Accept": "text/plain"})
                response.raise_for_status()
                text = response.text
                if text and len(text.strip()) > 100:
                    await asyncio.sleep(0.8)
                    return text
            except Exception as e:
                logger.warning(f"Jina failed [{url}]: {e}")
        
        # Jina başarısızsa doğrudan httpx ile HTML çek
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                resp.raise_for_status()
                html = resp.text
                # Basit HTML → text çevirme (etiketleri temizle)
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 100:
                    return text[:8000]  # Max 8000 karakter
        except Exception as e:
            logger.warning(f"Direct fetch also failed [{url}]: {e}")
        
        return ""

    async def process_search_queries(
        self,
        queries: list,
        max_per_query: int = 10,
        max_total: int = 20,
        progress_callback: Optional[Callable] = None,
        time_filter: str = "all",
        domain_filter: str = "all",
        cancel_check: Optional[Callable] = None
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
            if _is_cancelled():
                return []
            await _notify(f"🔍 Sorgu {i}/{len(queries)} aranıyor: '{query[:50]}...'")
            search_results = self.search_duckduckgo(
                query, max_results=max_per_query,
                time_filter=time_filter, domain_filter=domain_filter
            )
            for res in search_results:
                href = res.get('href') or res.get('url', '')
                if href and href not in all_links:
                    all_links[href] = res.get('title', href)
            await asyncio.sleep(1.5)  # Polite delay between queries

        if _is_cancelled():
            return []

        total_links = list(all_links.items())[:max_total]
        await _notify(f"🌐 Toplam {len(total_links)} benzersiz kaynak bulundu, içerikler indiriliyor...")

        documents = []
        # Paralel indirme (5'er 5'er batch)
        batch_size = 5
        for batch_start in range(0, len(total_links), batch_size):
            if _is_cancelled():
                return documents
            batch = total_links[batch_start:batch_start + batch_size]
            tasks = []
            for url, title in batch:
                tasks.append(self._fetch_one(url, title, batch_start + len(tasks) + 1, len(total_links), _notify))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, dict) and r:
                    documents.append(r)

        return documents

    async def _fetch_one(self, url, title, idx, total, notify):
        await notify(f"📄 [{idx}/{total}] İndiriliyor: {title[:60]}")
        content = await self.fetch_url_markdown_jina(url)
        if content and len(content.strip()) > 100:
            return {"url": url, "title": title, "content": content, "relevance_score": 0}
        return {}
