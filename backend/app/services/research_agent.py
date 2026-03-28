"""
Research Agent - Orkestratör: Arama → Kazıma → Groq Süzgeci → Sentez → Doğrulama
Cancel flag + Gelişmiş filtreler desteği.
"""
import asyncio
from typing import Callable, Optional
from loguru import logger
from backend.app.services.search_engine import DeepSearchEngine
from backend.app.services.ai_engine import MultiAIEngine

DEPTH_CONFIG = {
    "surface": {"results_per_query": 5,  "max_sources": 5},
    "medium":  {"results_per_query": 10, "max_sources": 15},
    "deep":    {"results_per_query": 20, "max_sources": 30},
    "ultra":   {"results_per_query": 30, "max_sources": 50},
}


class CancelledError(Exception):
    pass


class ResearchAgent:
    def __init__(self, progress_callback: Callable = None, cancel_check: Callable = None,
                 groq_key: str = "", gemini_key: str = "", deepseek_key: str = ""):
        self.search_engine = DeepSearchEngine()
        self.ai_engine = MultiAIEngine(groq_key=groq_key, gemini_key=gemini_key, deepseek_key=deepseek_key)
        self._progress_cb = progress_callback
        self._cancel_check = cancel_check  # () -> bool

    def _is_cancelled(self) -> bool:
        return self._cancel_check and self._cancel_check()

    async def _check_cancel(self):
        if self._is_cancelled():
            raise CancelledError("Kullanıcı tarafından iptal edildi.")

    async def progress(self, msg: str):
        if self._progress_cb is None:
            return
        import inspect
        result = self._progress_cb(msg)
        if inspect.isawaitable(result):
            await result

    async def run(
        self, query: str, depth: str = "medium", language: str = "tr",
        time_filter: str = "all", domain_filter: str = "all",
        max_sources_override: int = 0,
    ) -> dict:
        cfg = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["medium"])
        max_sources = max_sources_override if max_sources_override > 0 else cfg["max_sources"]

        try:
            await self.progress(f"🔍 Araştırma başlatılıyor: '{query}' ({depth})...")
            await self._check_cancel()

            # Step 1: Sub-queries
            await self.progress("🧠 Arama sorguları genişletiliyor...")
            sub_queries_raw = await self.ai_engine.hybrid_generate(
                prompt=f"""Given the research topic: "{query}"
Generate 3 diverse search queries (in English) that cover different angles.
Return only the queries, one per line. Do NOT use numbers, bullet points, or quotes.""",
                system_message="You are an expert research assistant.",
                task_type="filter"
            )
            import re
            cleaned_queries = []
            for qstr in sub_queries_raw.strip().split("\n"):
                q_clean = re.sub(r'^\d+\.\s*|["\'-]|^\s*-\s*', '', qstr).strip()
                if q_clean and len(q_clean) > 3:
                    cleaned_queries.append(q_clean)
            sub_queries = cleaned_queries[:3]
            sub_queries.insert(0, query)
            await self.progress(f"📋 {len(sub_queries)} arama sorgusu oluşturuldu.")
            await self._check_cancel()

            # Step 2: Web Search (with filters)
            await self.progress(f"🌐 Kaynaklar aranıyor...")
            documents = await self.search_engine.process_search_queries(
                queries=sub_queries,
                max_per_query=cfg["results_per_query"],
                max_total=max_sources,
                progress_callback=self.progress,
                time_filter=time_filter,
                domain_filter=domain_filter,
                cancel_check=self._cancel_check,
            )
            await self.progress(f"📥 {len(documents)} kaynak indirildi.")
            await self._check_cancel()

            if not documents:
                # Kaynak bulunamadıysa bile AI'ın kendi bilgisiyle rapor üretmesini sağla
                await self.progress("⚠️ Web kaynağı bulunamadı. Sentinel AI kendi bilgi tabanıyla rapor üretiyor...")
                synthesis = await self._ai_synthesis(query, [], language)
                return {
                    "query": query, "depth": depth, "language": language,
                    "documents": [], "synthesis": synthesis,
                    "validation": {"reliability_score": 4, "hallucination_risk": "high",
                                   "unsupported_claims": [], "contradictions": [],
                                   "verdict": "Kaynak bulunamadığı için AI kendi bilgisiyle yazdı. Doğrulama yapınız."},
                    "source_count": 0, "reliable_source_count": 0,
                }

            # Step 3: Groq Filter (3'ten az kaynak varsa filtrelemeyi atla)
            if len(documents) <= 3:
                await self.progress(f"ℹ️ Az kaynak ({len(documents)}) — filtreleme atlanıyor.")
                filtered_docs = documents
            else:
                await self.progress("⚡ Kaynaklar değerlendiriliyor (Groq)...")
                filtered_docs = await self._groq_filter_pass(query, documents)
                if not filtered_docs:
                    await self.progress("⚠️ Filtre geçen kaynak yok, tüm kaynaklar kullanılıyor.")
                    filtered_docs = documents[:5]
            await self.progress(f"✅ {len(filtered_docs)} kaynak senteze hazır.")
            await self._check_cancel()

            # Step 4: Synthesis (keep-alive ile)
            await self.progress("✨ Derin analiz ve sentez yapılıyor... (Bu adım 30-90 saniye sürebilir)")

            # Sentez sırasında bağlantıyı canlı tut
            async def _keep_alive():
                secs = 0
                while True:
                    await asyncio.sleep(10)
                    secs += 10
                    await self.progress(f"⏱️ Sentez devam ediyor... ({secs}s)")

            keep_alive_task = asyncio.create_task(_keep_alive())
            try:
                synthesis = await self._ai_synthesis(query, filtered_docs, language)
            finally:
                keep_alive_task.cancel()

            await self.progress("📝 Sentez tamamlandı, doğrulama başlıyor...")
            await self._check_cancel()

            # Step 5: Cross Validation
            await self.progress("🔎 Çapraz doğrulama yapılıyor...")
            validation = await self._cross_validate(query, synthesis, filtered_docs)
            await self.progress("✔️ Araştırma tamamlandı!")

            return {
                "query": query, "depth": depth, "language": language,
                "documents": filtered_docs, "synthesis": synthesis,
                "validation": validation,
                "source_count": len(documents),
                "reliable_source_count": len(filtered_docs),
            }

        except CancelledError:
            return {"cancelled": True}
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return {"error": str(e)}

    async def _groq_filter_pass(self, query: str, documents: list) -> list:
        """Tüm kaynakları tek bir Groq çağrısında toplu değerlendir (rate limit koruması)."""
        import json as _json, re

        # Kısa özetler oluştur
        summaries = []
        for i, doc in enumerate(documents[:30], 1):
            snippet = doc.get("content", "")[:500]
            summaries.append(f"[{i}] Title: {doc.get('title','')}\nSnippet: {snippet}")
        
        batch_prompt = f"""Evaluate relevance of these sources for the query: "{query}"

{chr(10).join(summaries)}

Reply with JSON array only. For each source, include index and score (1-10):
[{{"index": 1, "score": 8}}, {{"index": 2, "score": 3}}, ...]
Only include sources scoring 5 or higher."""

        raw = await self.ai_engine.hybrid_generate(
            prompt=batch_prompt,
            system_message="You are a strict relevance filter. Reply with JSON array only.",
            task_type="filter"
        )

        filtered = []
        try:
            # JSON array çıkart
            m = re.search(r'\[.*\]', raw, re.DOTALL)
            if m:
                scores = _json.loads(m.group())
                for item in scores:
                    idx = item.get("index", 0) - 1
                    score = item.get("score", 0)
                    if 0 <= idx < len(documents) and score >= 5:
                        documents[idx]["relevance_score"] = score
                        filtered.append(documents[idx])
        except Exception as e:
            logger.warning(f"Batch filter parse: {e}")
            # Parse başarısızsa ilk 5 kaynağı al
            for doc in documents[:5]:
                doc["relevance_score"] = 6
                filtered.append(doc)
        
        return sorted(filtered, key=lambda x: x.get("relevance_score", 0), reverse=True)

    async def _ai_synthesis(self, query: str, documents: list, language: str) -> str:
        parts = []
        # Max 15 kaynak, her biri max 1500 karakter (Dinamik hybrid_generate'e uyumlu)
        for i, doc in enumerate(documents[:15], 1):
            content = doc.get('content', '')[:1500]
            parts.append(
                f"### Source {i}: {doc['title']}\nURL: {doc['url']}\n"
                f"Score: {doc.get('relevance_score', 'N/A')}/10\n\n"
                f"{content}"
            )
        ctx = "\n\n---\n\n".join(parts)
        lang_map = {"tr": "Turkish", "en": "English", "de": "German", "fr": "French", "ru": "Russian", "ar": "Arabic"}
        target = lang_map.get(language, "Turkish")
        prompt = f"""You are an elite academic AI researcher working in a high-tech intelligence agency (Nova Nexus).
Your task is to synthesize the provided web sources into an exhaustive, highly-structured, and deeply analytical report.

RESEARCH TOPIC: "{query}"

SOURCES:
{ctx}

REQUIREMENTS:
1. Write the entire report in {target}.
2. Use professional, authoritative, and academic language.
3. Length: Minimum 1500 words. DO NOT WRITE A SHORT SUMMARY. Provide deep contextual analysis.
4. Structure:
   - **Yönetici Özeti (Executive Summary)**: A high-level 3-paragraph summary of the core findings.
   - **Kapsamlı Analiz (Deep Analysis)**: Break down the topic systematically. Use subheadings, bullet points, and data where available.
   - **Metodoloji & Tarihçe (Timeline/Methodology)**: Chronological or methodological breakdown.
   - **Karşıt Görüşler ve Limitasyonlar (Contradictions & Nuances)**: Different perspectives or missing data in the sources.
   - **Karşılaştırmalı Tablolar / Veri Özetleri (Data Tables)**: If applicable, use Markdown tables to compare entities/concepts.
   - **Sonuç & Stratejik Öngörüler (Conclusion & Strategic Insights)**.
   - **Kaynaklar (References)**: A numbered list of the sources used, with their URLs.
5. In-text Citations: You MUST cite every claim using [Source N] format.

Produce the absolute best Markdown document possible. Delay no details."""
        return await self.ai_engine.hybrid_generate(
            prompt=prompt,
            task_type="synthesis",
            language=language
        )

    async def _cross_validate(self, query: str, synthesis: str, documents: list) -> dict:
        snippet = synthesis[:4000]
        sources = "\n".join([f"- {d['title']}: {d.get('content','')[:500]}" for d in documents[:5]])
        prompt = f"""Fact-check this synthesis against sources.

Topic: "{query}"
Synthesis: {snippet}
Sources: {sources}

JSON only:
{{"reliability_score": 1-10, "hallucination_risk": "low/medium/high",
"unsupported_claims": ["..."], "contradictions": ["..."], "verdict": "brief"}}"""

        import json as _json, re
        raw = await self.ai_engine.hybrid_generate(
            prompt=prompt,
            system_message="Fact-check the provided synthesis. Provide brief JSON output.",
            task_type="filter"
        )
        try:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return _json.loads(m.group())
        except Exception as e:
            logger.warning(f"Validation parse: {e}")
        return {
            "reliability_score": 6, "hallucination_risk": "medium",
            "unsupported_claims": [], "contradictions": [],
            "verdict": "Doğrulama ayrıştırılamadı."
        }
