# backend/app/services/academic_search.py
"""
AcademicSearchEngine - arXiv, Semantic Scholar, PubMed ve CrossRef entegrasyonu.
Akademik makaleleri, atıf sayılarına ve ilgi puanına göre sıralayarak döndürür.
"""
import asyncio
import aiohttp
import arxiv
from typing import List, Dict, Optional
from loguru import logger
import re


class AcademicSearchEngine:
    """
    Çoklu akademik veritabanından eş zamanlı (paralel) kaynak çeken motor.
    - arXiv: Fizik, CS, Matematik, Biyoloji
    - Semantic Scholar: 200M+ makale, atıf ağı analizi
    - PubMed: Tıp ve biyomedikal (NCBI Entrez)
    - CrossRef: DOI metadatası ve yayın bilgisi
    """

    SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    PUBMED_FETCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    CROSSREF_URL      = "https://api.crossref.org/works"

    def __init__(self):
        self.arxiv_client = arxiv.Client()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ──────────────────────────────────────────────────────────────
    # arXiv
    # ──────────────────────────────────────────────────────────────
    async def search_arxiv(self, query: str, max_results: int = 8) -> List[Dict]:
        """
        arXiv'de arama yap. En alakalı ve en yeni makaleleri önceliklendir.
        Kategori, DOI ve özet uzunluğu dahil tam metadata döndürür.
        """
        results = []
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )

            def _blocking_fetch():
                papers = []
                for paper in self.arxiv_client.results(search):
                    papers.append(paper)
                return papers

            papers = await asyncio.to_thread(_blocking_fetch)

            for paper in papers:
                doi = paper.doi or ""
                categories = ", ".join(paper.categories) if paper.categories else "N/A"
                year = paper.published.year if paper.published else "?"
                authority = self._arxiv_authority(paper.categories)

                results.append({
                    "title": paper.title.strip(),
                    "authors": [a.name for a in paper.authors[:5]],
                    "summary": paper.summary[:1500].replace("\n", " ").strip(),
                    "url": paper.entry_id,
                    "pdf_url": paper.pdf_url,
                    "published": str(paper.published)[:10],
                    "year": year,
                    "doi": doi,
                    "categories": categories,
                    "source": "arxiv",
                    "authority": authority,
                    "content": f"[arXiv | {categories} | {year}]\n"
                               f"Authors: {', '.join([a.name for a in paper.authors[:5]])}\n"
                               f"DOI: {doi}\n\n"
                               f"Abstract:\n{paper.summary[:2000]}"
                })
                logger.info(f"[akademik:arXiv] Bulundu: '{paper.title[:60]}' ({year})")

        except Exception as e:
            logger.error(f"[akademik:arXiv] Hata: {e}")

        return results

    def _arxiv_authority(self, categories: list) -> int:
        """Makale kategorisine göre otorite puanı ata."""
        if not categories:
            return 7
        top_cats = ["cs.AI", "cs.LG", "physics", "math", "q-bio", "stat"]
        for cat in categories:
            if any(tc in cat for tc in top_cats):
                return 9
        return 8

    # ──────────────────────────────────────────────────────────────
    # Semantic Scholar
    # ──────────────────────────────────────────────────────────────
    async def search_semantic_scholar(self, query: str, limit: int = 8) -> List[Dict]:
        """
        Semantic Scholar GraphQL API üzerinden makale ara.
        Atıf sayısı (citation count) en yüksek olan makaleleri tercih eder.
        """
        results = []
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,abstract,url,year,citationCount,referenceCount,publicationTypes,fieldsOfStudy"
        }
        try:
            session = await self._get_session()
            async with session.get(self.SEMANTIC_SCHOLAR_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    papers = data.get("data", [])
                    # Atıf sayısına göre sırala
                    papers.sort(key=lambda x: x.get("citationCount", 0), reverse=True)

                    for p in papers:
                        citations = p.get("citationCount", 0)
                        year      = p.get("year", "?")
                        abstract  = (p.get("abstract") or "")[:1500]
                        authors   = [a.get("name", "") for a in p.get("authors", [])[:5]]
                        fields    = ", ".join(p.get("fieldsOfStudy") or [])
                        authority = min(10, 7 + (1 if citations > 100 else 0) + (1 if citations > 500 else 0))

                        results.append({
                            "title": p.get("title", "Başlıksız"),
                            "authors": authors,
                            "summary": abstract,
                            "url": p.get("url") or f"https://api.semanticscholar.org/paper/{p.get('paperId','')}",
                            "year": year,
                            "citation_count": citations,
                            "fields_of_study": fields,
                            "source": "semantic_scholar",
                            "authority": authority,
                            "content": f"[Semantic Scholar | {fields} | Atıf: {citations} | {year}]\n"
                                       f"Authors: {', '.join(authors)}\n\n"
                                       f"Abstract:\n{abstract}"
                        })
                        logger.info(f"[akademik:S2] '{p.get('title','')[:60]}' — {citations} atıf")
                elif resp.status == 429:
                    logger.warning("[akademik:S2] Rate limit — bekleniyor...")
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"[akademik:S2] Hata: {e}")

        return results

    # ──────────────────────────────────────────────────────────────
    # PubMed (Tıp + Biyomedikal)
    # ──────────────────────────────────────────────────────────────
    async def search_pubmed(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        NCBI PubMed API (ücretsiz, API key gerekmez).
        Tıp, biyomedikal ve sağlık bilimleri için en yetkili kaynak.
        """
        results = []
        try:
            session = await self._get_session()

            # Adım 1: Makale ID'lerini al
            search_params = {
                "db": "pubmed", "term": query, "retmax": max_results,
                "retmode": "json", "sort": "relevance"
            }
            async with session.get(self.PUBMED_SEARCH_URL, params=search_params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                ids = data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            # Adım 2: Özetleri çek
            fetch_params = {
                "db": "pubmed", "id": ",".join(ids),
                "rettype": "abstract", "retmode": "text"
            }
            async with session.get(self.PUBMED_FETCH_URL, params=fetch_params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Her makaleyi basit şekilde ayır
                    chunks = re.split(r'\n{3,}', text.strip())
                    for i, chunk in enumerate(chunks[:max_results]):
                        if len(chunk.strip()) < 50:
                            continue
                        pmid = ids[i] if i < len(ids) else "N/A"
                        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        # Başlığı çıkar
                        first_line = chunk.strip().split("\n")[0][:200]
                        results.append({
                            "title": first_line,
                            "authors": [],
                            "summary": chunk[:1500],
                            "url": url,
                            "source": "pubmed",
                            "authority": 9,  # PubMed her zaman yüksek otorite
                            "content": f"[PubMed | PMID: {pmid}]\n\n{chunk[:3000]}"
                        })
                        logger.info(f"[akademik:PubMed] PMID:{pmid} — {first_line[:50]}")

        except Exception as e:
            logger.error(f"[akademik:PubMed] Hata: {e}")

        return results

    # ──────────────────────────────────────────────────────────────
    # CrossRef (DOI Metadata)
    # ──────────────────────────────────────────────────────────────
    async def search_crossref(self, query: str, limit: int = 5) -> List[Dict]:
        """
        CrossRef REST API - 130M+ akademik yayın hakkında öcretsiz DOI metadatası.
        Yayıncı, ISSN, lisans bilgisi dahil.
        """
        results = []
        try:
            session = await self._get_session()
            params = {
                "query": query, "rows": limit,
                "select": "title,author,abstract,URL,published,type,publisher,is-referenced-by-count"
            }
            async with session.get(self.CROSSREF_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("message", {}).get("items", [])

                    for item in items:
                        title     = (item.get("title") or ["Başlıksız"])[0]
                        authors   = [f"{a.get('given','')} {a.get('family','')}".strip()
                                     for a in item.get("author", [])[:5]]
                        abstract  = (item.get("abstract") or "")[:1500]
                        url       = item.get("URL", "")
                        publisher = item.get("publisher", "")
                        citations = item.get("is-referenced-by-count", 0)
                        pub_date  = item.get("published", {}).get("date-parts", [[None]])[0]
                        year      = pub_date[0] if pub_date else "?"

                        if not url or len(title) < 5:
                            continue

                        authority = min(10, 7 + (1 if citations > 50 else 0) + (1 if citations > 200 else 0))
                        results.append({
                            "title": title,
                            "authors": authors,
                            "summary": abstract,
                            "url": url,
                            "year": year,
                            "publisher": publisher,
                            "citation_count": citations,
                            "source": "crossref",
                            "authority": authority,
                            "content": f"[CrossRef | {publisher} | Atıf: {citations} | {year}]\n"
                                       f"Authors: {', '.join(authors)}\n\n"
                                       f"{abstract}"
                        })
                        logger.info(f"[akademik:CrossRef] '{title[:60]}' — {citations} atıf")

        except Exception as e:
            logger.error(f"[akademik:CrossRef] Hata: {e}")

        return results

    # ──────────────────────────────────────────────────────────────
    # Ana Çoklu Arama Koordinatörü
    # ──────────────────────────────────────────────────────────────
    async def full_academic_search(self, query: str, mode: str = "deep") -> List[Dict]:
        """
        Tüm akademik kaynakları paralel olarak arar ve birleştirir.
        mode="deep"  → arXiv + Semantic Scholar
        mode="ultra" → arXiv + Semantic Scholar + PubMed + CrossRef
        """
        logger.info(f"[akademik] '{query}' için çoklu akademik arama başlıyor ({mode.upper()} mod)...")

        tasks = [
            self.search_arxiv(query, max_results=6),
            self.search_semantic_scholar(query, limit=6),
        ]
        if mode == "ultra":
            tasks.append(self.search_pubmed(query, max_results=4))
            tasks.append(self.search_crossref(query, limit=4))

        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        combined: List[Dict] = []
        seen_titles = set()
        for batch in all_results:
            if isinstance(batch, Exception):
                logger.warning(f"[akademik] Bir kaynak başarısız: {batch}")
                continue
            for doc in batch:
                title_key = re.sub(r'\W+', '', doc.get("title", "").lower())[:60]
                if title_key and title_key not in seen_titles:
                    seen_titles.add(title_key)
                    combined.append(doc)

        # Otorite puanına göre sırala
        combined.sort(key=lambda x: (x.get("authority", 5), x.get("citation_count", 0)), reverse=True)
        logger.info(f"[akademik] Toplam {len(combined)} benzersiz akademik kaynak bulundu.")

        await self.close()
        return combined