# backend/app/services/research_agent.py
"""
Research Agent - Ana Orkestratör
Çok katmanlı araştırma motoru:
  - Web araması (DuckDuckGo + Jina Reader)
  - Akademik kaynak araması (arXiv + Semantic Scholar + PubMed + CrossRef)
  - Derin web taraması (Recursive DeepCrawler — Ultra modda)
  - Hibrit AI Sentezi ve Doğrulama
"""
import asyncio
import json as _json
import re
from typing import Callable, List, Optional
from loguru import logger

from backend.app.services.search_engine  import DeepSearchEngine
from backend.app.services.ai_engine      import MultiAIEngine
from backend.app.services.academic_search import AcademicSearchEngine
from backend.app.services.deep_web_crawler import DeepWebCrawler


# ══════════════════════════════════════════════════════════════════
#  Araştırma Derinlik Yapılandırması
# ══════════════════════════════════════════════════════════════════
DEPTH_CONFIG = {
    "surface": {
        "num_queries": 3, "results_per_query": 5, "max_sources": 10,
        "use_academic": False, "use_crawler": False,
        "crawler_depth": 0, "crawler_pages": 0,
        "query_instruction": (
            "Generate 3 basic search queries covering different basic angles of the topic."
        ),
        "synthesis_instruction": (
            "Provide a clear, accessible, multi-faceted summary of the topic."
        )
    },
    "medium": {
        "num_queries": 5, "results_per_query": 10, "max_sources": 20,
        "use_academic": False, "use_crawler": False,
        "crawler_depth": 0, "crawler_pages": 0,
        "query_instruction": (
            "Generate 5 search queries covering DIFFERENT ANGLES: "
            "historical context, current news, economic impact, expert opinions, pros/cons."
        ),
        "synthesis_instruction": (
            "Provide a detailed multi-dimensional report covering history, "
            "current state, future implications and expert perspectives."
        )
    },
    "deep": {
        "num_queries": 7, "results_per_query": 15, "max_sources": 35,
        "use_academic": True, "use_crawler": False,
        "crawler_depth": 0, "crawler_pages": 0,
        "query_instruction": (
            "Generate 7 advanced search queries covering distinct dimensions: "
            "1) Technical/Operational, 2) Historical/Timeline, 3) Legal/Ethical, "
            "4) Financial/Economic, 5) Social/Key Actors, 6) Scientific Research, "
            "7) Comparative Analysis. Avoid basic overview queries."
        ),
        "synthesis_instruction": (
            "Assume the reader is knowledgeable. Structure the report to cover "
            "technical details, legal issues, financial aspects, key actors, "
            "scientific findings and comparative analysis systematically."
        )
    },
    "ultra": {
        "num_queries": 10, "results_per_query": 20, "max_sources": 60,
        "use_academic": True, "use_crawler": True,
        "crawler_depth": 2, "crawler_pages": 15,
        "query_instruction": (
            "Generate 10 highly specific, investigative search queries. "
            "ACTIVELY SEEK: hidden financial networks, specific legal documents, "
            "contradictory academic opinions, deep historical roots, "
            "operational mechanisms, whistleblower reports, declassified documents. "
            "Cover every possible angle. Do NOT repeat similar queries."
        ),
        "synthesis_instruction": (
            "Assume the reader is an elite domain expert. STRICTLY FORBIDDEN to write "
            "generic introductions. Produce a MASSIVE, exhaustive, multi-layered report. "
            "Deeply analyze every dimension: Financial, Legal, Operational, Social, Historical, "
            "Scientific. Use academic sources to validate claims. Cite contradictions explicitly."
        )
    },
}


# ══════════════════════════════════════════════════════════════════
#  Agent
# ══════════════════════════════════════════════════════════════════
class CancelledError(Exception):
    pass


class ResearchAgent:
    """
    Tam entegre araştırma orkestratörü.
    Mod bazlı paralel kaynak toplama, AI filtreleme, hibrit sentez ve çapraz doğrulama.
    """

    def __init__(
        self,
        progress_callback: Optional[Callable] = None,
        cancel_check: Optional[Callable] = None,
        openrouter_key: str = ""
    ):
        self.search_engine   = DeepSearchEngine()
        self.ai_engine       = MultiAIEngine(openrouter_key=openrouter_key)
        self.academic_engine = AcademicSearchEngine()
        self._progress_cb    = progress_callback
        self._cancel_check   = cancel_check

    def _is_cancelled(self) -> bool:
        return bool(self._cancel_check and self._cancel_check())

    async def _check_cancel(self):
        if self._is_cancelled():
            raise CancelledError("Kullanıcı tarafından iptal edildi.")

    async def progress(self, msg: str):
        if self._progress_cb:
            import inspect
            res = self._progress_cb(msg)
            if inspect.isawaitable(res):
                await res

    # ── Ana Araştırma Akışı ──────────────────────────────────────
    async def run(
        self,
        query: str,
        depth: str = "medium",
        language: str = "tr",
        time_filter: str = "all",
        domain_filter: str = "all",
        max_sources_override: int = 0
    ) -> dict:
        cfg = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["medium"])
        max_sources = max_sources_override if max_sources_override > 0 else cfg["max_sources"]

        try:
            # ── Step 1: Alt Sorgu Üretimi ─────────────────────
            await self.progress(
                f"🧠 '{query}' için çok boyutlu araştırma stratejisi oluşturuluyor ({depth.upper()} MOD)..."
            )
            query_prompt = (
                f'Topic: "{query}"\n'
                f"{cfg['query_instruction']}\n"
                "Return ONLY the search queries, one per line. No numbers, no bullets, no extra text."
            )
            sub_queries_raw = await self.ai_engine.hybrid_generate(
                prompt=query_prompt,
                system_message="You are an expert investigative journalist aiming for total coverage.",
                task_type="filter"
            )
            cleaned_queries = [
                re.sub(r'^[\d\.\-\*\s\"\']+', '', q).strip()
                for q in sub_queries_raw.strip().split("\n") if len(q.strip()) > 5
            ]
            sub_queries = [query] + cleaned_queries[:cfg["num_queries"]]
            await self.progress(f"🔍 {len(sub_queries)} araştırma sorgusu oluşturuldu.")
            await self._check_cancel()

            # ── Step 2: Paralel Kaynak Toplama ────────────────
            await self.progress("📡 Paralel veri toplama başlıyor (Web + Akademik + Crawler)...")

            # Her zaman web araması yapılır
            web_task = self.search_engine.process_search_queries(
                queries=sub_queries,
                max_per_query=cfg["results_per_query"],
                max_total=max_sources,
                progress_callback=self.progress,
                time_filter=time_filter,
                domain_filter=domain_filter,
                cancel_check=self._cancel_check,
            )

            gather_tasks = [web_task]
            academic_task_idx = None
            crawler_task_idx  = None

            # Deep/Ultra modda akademik arama
            if cfg["use_academic"]:
                await self.progress("🎓 Akademik veri tabanları taranıyor (arXiv, Semantic Scholar, PubMed, CrossRef)...")
                academic_task = self.academic_engine.full_academic_search(query, mode=depth)
                gather_tasks.append(academic_task)
                academic_task_idx = len(gather_tasks) - 1

            # Ultra modda derin crawler (temel sorgular için)
            crawler_start_query = sub_queries[0]
            if cfg["use_crawler"]:
                await self.progress("🕷️ Ultra mod: Derin recursive web crawler başlatılıyor...")
                # Önce hızlı web araması yapıp URL'leri crawler'a ver
                quick_urls = await self._get_quick_urls(crawler_start_query, limit=6)
                if quick_urls:
                    crawler = DeepWebCrawler(
                        tor_enabled=False,
                        progress_callback=self.progress
                    )
                    crawler_task = crawler.crawl_recursive(
                        start_urls=quick_urls,
                        max_depth=cfg["crawler_depth"],
                        max_total_pages=cfg["crawler_pages"],
                        min_quality=2.0
                    )
                    gather_tasks.append(crawler_task)
                    crawler_task_idx = len(gather_tasks) - 1

            # Paralel çalıştır
            all_results_raw = await asyncio.gather(*gather_tasks, return_exceptions=True)
            await self._check_cancel()

            # ── Step 3: Kaynak Birleştirme ve Dedup ───────────
            web_docs = all_results_raw[0] if not isinstance(all_results_raw[0], Exception) else []
            academic_docs: List[dict] = []
            crawler_docs:  List[dict] = []

            if academic_task_idx and not isinstance(all_results_raw[academic_task_idx], Exception):
                academic_docs = all_results_raw[academic_task_idx] or []
                await self.progress(f"🎓 {len(academic_docs)} akademik kaynak bulundu.")

            if crawler_task_idx and not isinstance(all_results_raw[crawler_task_idx], Exception):
                crawler_docs = all_results_raw[crawler_task_idx] or []
                await self.progress(f"🕷️ DeepCrawler {len(crawler_docs)} sayfa döndürdü.")

            # Formatla + Birleştir (akademik kaynaklar en sona eklenir, ama sentezde önceliklenir)
            all_docs = self._merge_and_deduplicate(web_docs, academic_docs, crawler_docs)

            if not all_docs:
                return {"error": "Yeterli kaynak bulunamadı. Farklı arama terimleri deneyin."}

            await self.progress(f"📚 Toplam {len(all_docs)} benzersiz kaynak birleştirildi.")

            # ── Step 4: AI Filtreleme ─────────────────────────
            if len(all_docs) > 3:
                await self.progress("⚡ AI ile kaynak kalite filtrelemesi yapılıyor...")
                filtered_docs = await self._groq_filter_pass(query, all_docs)
            else:
                filtered_docs = all_docs

            # Akademik kaynakları her zaman koru (bunlar direkt güvenilir)
            preserved_academic = [d for d in academic_docs if d.get("authority", 0) >= 8]
            for doc in preserved_academic:
                if doc not in filtered_docs:
                    filtered_docs.insert(0, doc)

            await self.progress(f"✅ {len(filtered_docs)} nitelikli kaynak senteze hazır.")
            await self._check_cancel()

            # ── Step 5: AI Sentezi ────────────────────────────
            await self.progress("✨ Elite AI raporu yazılıyor... (bu işlem birkaç dakika sürebilir)")
            keep_alive_task = asyncio.create_task(self._keep_alive())
            try:
                synthesis = await self._ai_synthesis(query, filtered_docs, language, depth, cfg)
            finally:
                keep_alive_task.cancel()

            # Kritik API hatalarını UI'da hata olarak göster
            if synthesis.startswith("CRITICAL_ERROR:"):
                return {"error": synthesis.replace("CRITICAL_ERROR: ", "")}

            # ── Step 6: Çapraz Doğrulama ─────────────────────
            await self.progress("🛡️ Sentinel AI doğrulaması yapılıyor...")
            validation = await self._cross_validate(query, synthesis, filtered_docs)

            return {
                "query": query,
                "depth": depth,
                "language": language,
                "documents": filtered_docs,
                "synthesis": synthesis,
                "validation": validation,
                "source_count": len(all_docs),
                "reliable_source_count": len(filtered_docs),
                "academic_count": len(academic_docs),
                "crawler_count": len(crawler_docs),
            }

        except CancelledError:
            return {"cancelled": True}
        except Exception as e:
            logger.exception(f"[ResearchAgent] Hata: {e}")
            return {"error": str(e)}

    # ── Yardımcı: Hızlı URL Toplama (Crawler Başlangıcı İçin) ────
    async def _get_quick_urls(self, query: str, limit: int = 6) -> List[str]:
        """Crawler'a başlangıç URL'leri vermek için hızlı bir arama yap."""
        try:
            results = await self.search_engine.search_duckduckgo(query, max_results=limit)
            return [r.get("href") or r.get("url", "") for r in results if r.get("href") or r.get("url")]
        except Exception:
            return []

    # ── Kaynak Birleştirme ve Tekrar Eleme ──────────────────────
    def _merge_and_deduplicate(
        self,
        web_docs: list,
        academic_docs: list,
        crawler_docs: list
    ) -> list:
        """
        URL ve başlık bazlı deduplication ile tüm kaynakları birleştirir.
        Akademik kaynaklar başa yerleştirilir (yüksek otorite).
        """
        all_docs = []
        seen_urls  = set()
        seen_titles = set()

        def _add(docs: list, source_label: str = ""):
            for doc in docs:
                url   = (doc.get("url") or "").lower().strip()
                title = re.sub(r'\W+', '', (doc.get("title") or "").lower())[:50]

                if url in seen_urls or (title and title in seen_titles):
                    continue

                if url:
                    seen_urls.add(url)
                if title:
                    seen_titles.add(title)

                # İçerik yoksa summary'yi content olarak kullan
                if not doc.get("content") and doc.get("summary"):
                    doc["content"] = doc["summary"]

                all_docs.append(doc)

        # Önce akademik (yüksek otorite)
        _add(academic_docs, "academic")
        # Sonra web
        _add(web_docs, "web")
        # En son crawler
        _add(crawler_docs, "crawler")

        return all_docs

    # ── Keep-Alive ───────────────────────────────────────────────
    async def _keep_alive(self):
        secs = 0
        while True:
            await asyncio.sleep(10)
            secs += 10
            await self.progress(f"⏱️ Derin rapor yazılıyor... ({secs}s geçti, lütfen bekleyin)")

    # ── AI Filtreleme ────────────────────────────────────────────
    async def _groq_filter_pass(self, query: str, documents: list) -> list:
        """
        Tüm kaynakları tek bir Groq çağrısında puanlar.
        Akademik kaynaklar hiçbir zaman filtrelenmez (otorite >= 8).
        """
        # Akademikleri koru, web kaynaklarını filtrele
        academic_only = [d for d in documents if d.get("authority", 0) >= 8]
        web_only      = [d for d in documents if d.get("authority", 0) < 8]

        summaries = []
        for i, doc in enumerate(web_only[:40], 1):
            snippet = (doc.get("content") or doc.get("summary") or "")[:400]
            summaries.append(f"[{i}] Title: {doc.get('title', '')}\nSnippet: {snippet}")

        if not summaries:
            return academic_only + web_only

        batch_prompt = (
            f'Research topic: "{query}"\n'
            f'{chr(10).join(summaries)}\n\n'
            'Score each source 1-10 for relevance. '
            'Reply ONLY with a JSON array: [{"index": 1, "score": 8}]'
        )

        raw = await self.ai_engine.hybrid_generate(prompt=batch_prompt, task_type="filter")
        filtered_web = []
        try:
            json_str = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_str:
                scores = _json.loads(json_str.group())
                for item in scores:
                    idx = item.get("index", 0) - 1
                    if 0 <= idx < len(web_only) and item.get("score", 0) >= 3:
                        web_only[idx]["relevance_score"] = item["score"]
                        filtered_web.append(web_only[idx])
        except Exception:
            filtered_web = web_only[:15]

        # Birleştir: Akademik önce, sonra relevance puanlı web kaynakları
        combined = academic_only + sorted(
            filtered_web,
            key=lambda x: (x.get("relevance_score", 0), x.get("authority", 0)),
            reverse=True
        )
        return combined

    # ── AI Sentezi ───────────────────────────────────────────────
    async def _ai_synthesis(
        self, query: str, documents: list, language: str, depth: str, cfg: dict
    ) -> str:
        """
        Tüm kaynakları (web + akademik + crawler) AI'a göndererek
        çok bölümlü, kapsamlı bir Markdown raporu yazar.
        Akademik kaynaklar ayrı bir otorite katmanı olarak işaretlenir.
        """
        web_parts      = []
        academic_parts = []
        max_docs       = 15 if depth in ("surface", "medium") else 30

        # Kaynakları web ve akademik olarak ayır
        for i, doc in enumerate(documents[:max_docs], 1):
            source_label = doc.get("source", "web")
            authority    = doc.get("authority", 5)
            content      = (doc.get("content") or doc.get("summary") or "")[:6000]
            citations    = f" | Atıf: {doc['citation_count']}" if doc.get("citation_count") else ""
            year         = f" | {doc['year']}" if doc.get("year") else ""

            entry = (
                f"### Source {i} [{source_label.upper()} | Authority: {authority}/10{citations}{year}]\n"
                f"Title: {doc.get('title', 'N/A')}\n"
                f"URL: {doc.get('url', 'N/A')}\n"
                f"Authors: {', '.join(doc.get('authors', [])) if doc.get('authors') else 'N/A'}\n\n"
                f"{content}"
            )

            if source_label in ("arxiv", "semantic_scholar", "pubmed", "crossref"):
                academic_parts.append(entry)
            else:
                web_parts.append(entry)

        target = {"tr": "Turkish", "en": "English", "de": "German", "fr": "French"}.get(language, "Turkish")

        academic_section = ""
        if academic_parts:
            academic_section = (
                "\n\n## 📚 PEER-REVIEWED ACADEMIC SOURCES (High Authority — Prioritize These)\n"
                + "\n\n---\n\n".join(academic_parts)
            )

        web_section = "\n\n## 🌐 WEB SOURCES\n" + "\n\n---\n\n".join(web_parts) if web_parts else ""

        prompt = f"""You are an elite intelligence analyst and academic researcher at Nova Nexus AI.
Your mission: synthesize ALL provided sources into an EXHAUSTIVE, peer-reviewed-quality research report.

RESEARCH TOPIC: "{query}"
RESEARCH DEPTH: {depth.upper()} MODE
TARGET LANGUAGE: {target}
TOTAL SOURCES: {len(documents)} ({len(academic_parts)} academic, {len(web_parts)} web)

{academic_section}

{web_section}

══════════════════════════════════════════════════════════
CRITICAL SYNTHESIS INSTRUCTIONS:
══════════════════════════════════════════════════════════

1. {cfg['synthesis_instruction']}

2. ACADEMIC SOURCE PRIORITY: Academic sources (arXiv, Semantic Scholar, PubMed, CrossRef) 
   are peer-reviewed and must be given the HIGHEST PRIORITY. Use them to validate or challenge 
   claims from web sources. Explicitly note when academic evidence confirms or contradicts web sources.

3. LANGUAGE ENFORCEMENT: You MUST write your ENTIRE final response strictly in the {target.upper()} language! Translate ALL headings, body paragraphs, and analysis to {target.upper()}. Do NOT use any other language such as Chinese or Russian.

4. MANDATORY REPORT STRUCTURE — Write at minimum 4-5 DENSE paragraphs per section (translate these headings to {target.upper()}):
   - Executive Overview & Scope
   - Historical Background & Evolution
   - Academic Findings & Scientific Evidence
   - Key Actors, Networks & Relationship Map
   - Technical, Financial & Operational Mechanisms
   - Legal, Ethical & Controversial Dimensions
   - Strategic Conclusions & Future Outlook
   - References & Notes

5. CITATION MANDATE: EVERY specific claim, statistic, or date MUST reference [Source N] inline.

6. CONTRADICTION ANALYSIS: When sources conflict, explicitly state: 
   "While [Source X] claims..., [Source Y] (peer-reviewed) contradicts this by..."

7. FORBIDDEN: Generic introductions. Start immediately with substantive content.

8. LENGTH: Produce the ABSOLUTELY LONGEST, most comprehensive report possible. 
   Do not summarize — ELABORATE on every point.

Write the complete report now in {target.upper()}:"""

        return await self.ai_engine.hybrid_generate(
            prompt=prompt,
            task_type="report",
            system_message=f"You are a master intelligence analyst. You MUST respond exclusively in {target.upper()}.",
            language=language
        )

    # ── Çapraz Doğrulama ─────────────────────────────────────────
    async def _cross_validate(self, query: str, synthesis: str, documents: list) -> dict:
        """
        Sentezin kaynaklarla tutarlılığını kontrol eder.
        Akademik kaynak oranına göre güvenilirlik skoru boosted edilir.
        """
        academic_count = sum(1 for d in documents if d.get("source") in
                              ("arxiv", "semantic_scholar", "pubmed", "crossref"))
        academic_ratio = academic_count / max(len(documents), 1)

        prompt = f"""You are a rigorous academic fact-checker at Nova Nexus Sentinel AI.

Research topic: "{query}"
Academic sources in report: {academic_count}/{len(documents)} ({academic_ratio:.0%})

Synthesis to validate (first 4000 chars):
{synthesis[:4000]}

Perform a strict fact-check. Reply ONLY with this exact JSON:
{{
  "reliability_score": <int 1-10>,
  "hallucination_risk": "<low|medium|high>",
  "academic_backing": "<strong|moderate|weak>",
  "unsupported_claims": ["<claim 1 without citation>"],
  "contradictions": ["<contradiction found>"],
  "verdict": "<brief professional verdict in Turkish>"
}}"""

        raw = await self.ai_engine.hybrid_generate(prompt=prompt, task_type="filter")
        try:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                result = _json.loads(m.group())
                # Akademik kaynak oranına göre skoru güçlendir
                base_score = result.get("reliability_score", 7)
                boost = round(academic_ratio * 2)
                result["reliability_score"] = min(10, base_score + boost)
                return result
        except Exception as e:
            logger.warning(f"[Doğrulama] JSON parse hatası: {e}")

        return {
            "reliability_score": 6 + round(academic_ratio * 2),
            "hallucination_risk": "medium",
            "academic_backing": "moderate" if academic_ratio > 0.2 else "weak",
            "unsupported_claims": [],
            "contradictions": [],
            "verdict": "Otomatik doğrulama tamamlandı."
        }