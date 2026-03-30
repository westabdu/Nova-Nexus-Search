"""
Multi-AI Engine - OpenRouter Exclusive (Sadece Ücretsiz Modeller)
════════════════════════════════════════════════════════════════
Görev bazlı akıllı model seçimi (Tümü Ücretsiz):

  🔍 Filtreleme/Arama   → liquid/lfm-2.5-1.2b-instruct:free (Hızlı, 156 t/s)
  ⚡ Sentezleme & Rapor → openai/gpt-oss-120b:free (Birincil, 131k context)
                         → minimax/minimax-m2.5:free (Yedek)
  🧠 Son Çare Yedek     → nvidia/nemotron-3-super-120b-a12b:free (Büyük ve tutarlı)
  🌐 Çeviri             → openai/gpt-oss-120b:free
"""
import asyncio
from backend.app.core.config import settings
from loguru import logger

try:
    import openai
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False


class MultiAIEngine:
    """
    OpenRouter API kullanarak tüm AI işlemlerini yönetir.
    Sistem artık sadece bu servise bağımlıdır.
    """

    def __init__(self, openrouter_key: str = ""):
        self.api_key = openrouter_key or settings.OPENROUTER_API_KEY
        self.client = None

        if _HAS_OPENAI and self.api_key:
            try:
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://openrouter.ai/api/v1",
                    timeout=400.0, # Çok büyük modeller / raporlar için uzun timeout
                )
                logger.info("[OpenRouter] Client başarıyla oluşturuldu.")
            except Exception as e:
                logger.warning(f"[OpenRouter] Init hatası: {e}")

    async def hybrid_generate(
        self,
        prompt: str,
        task_type: str = "synthesis",
        system_message: str = "You are an elite intelligence researcher.",
        language: str = "tr"  # API'de kullanılmıyorsa da imza gereği tutuyoruz
    ) -> str:
        """
        OpenRouter üzerinden görev tipine uygun ücretsiz modeli seçer.
        """
        if not self.client:
            return "CRITICAL_ERROR: OpenRouter API anahtarı boş veya hatalı yapılandırılmış. Lütfen .env dosyanızı veya profilinizi kontrol edin."

        # Dil bilgisini sisteme zorunlu olarak ekle
        lang_instruction = f"\n\nCRITICAL INSTRUCTION: You MUST write your ENTIRE response strictly in the following language: {language.upper()}. Do NOT use any other language."
        system_message += lang_instruction

        # ── 1. Filtreleme (Hızlı Süzme) ────────────────────────
        if task_type == "filter":
            return await self._call_openrouter(
                prompt, system_message,
                model="liquid/lfm-2.5-1.2b-instruct:free",
                max_tokens=2000,
                fallback_models=["openai/gpt-oss-120b:free"]
            )

        # ── 2. Sentezleme & Raporlama (Derin Sentez) ───────────
        if task_type in ("synthesis", "report"):
            return await self._call_openrouter(
                prompt, system_message,
                model="openai/gpt-oss-120b:free",
                max_tokens=10000, # Serbest token (120B model raporu çok büyük atabilir)
                fallback_models=[
                    "minimax/minimax-m2.5:free",
                    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                    "nvidia/nemotron-3-super-120b-a12b:free"
                ]
            )

        # ── 3. Çeviri & Muhakeme (Genel) ───────────────────────
        if task_type in ("translation", "reasoning"):
            return await self._call_openrouter(
                prompt, system_message,
                model="openai/gpt-oss-120b:free",
                max_tokens=8000,
                fallback_models=["minimax/minimax-m2.5:free", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"]
            )

        # Default (Diğer tip çağrılar)
        return await self._call_openrouter(
            prompt, system_message,
            model="openai/gpt-oss-120b:free",
            max_tokens=8000,
            fallback_models=["minimax/minimax-m2.5:free", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"]
        )

    async def _call_openrouter(
        self, prompt: str, system_message: str,
        model: str, max_tokens: int, fallback_models: list = None
    ) -> str:
        """
        OpenRouter çağrısı yapar, başarısız olursa fallback listesindeki modellere geçer.
        """
        models_to_try = [model] + (fallback_models or [])
        last_err = ""

        for current_model in models_to_try:
            for attempt in range(2):
                try:
                    logger.info(f"[OpenRouter] İstek gönderiliyor: {current_model} (deneme {attempt+1})")
                    
                    # Prompt kırpması: 100K karakter toleransı (modellerin çökmemesi için ufak güvenlik payı)
                    safe_prompt = prompt if len(prompt) < 250000 else prompt[:250000] + "\n\n[...Kırpıldı...]"

                    resp = await self.client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": safe_prompt},
                        ],
                        max_tokens=max_tokens,
                        temperature=0.3, # Sentez için nispeten katı (0.3)
                        extra_headers={
                            "HTTP-Referer": "https://github.com/",
                            "X-Title": "Nova Nexus Search",
                        }
                    )
                    
                    content = resp.choices[0].message.content
                    logger.info(f"[OpenRouter] ✅ Başarılı ({current_model}) — {len(content)} karakter üretildi.")
                    return content

                except Exception as e:
                    err_str = str(e)
                    last_err = err_str

                    # Kesin Hatalar (API Key yanlış vb.)
                    if "401" in err_str or "unauthorized" in err_str.lower():
                        logger.error(f"[OpenRouter] Kritik API yetki hatası (401).")
                        return "CRITICAL_ERROR: OpenRouter API anahtarınız hatalı (401 Unauthorized)."

                    # OpenRouter kredi sıkıntısı var ise
                    if "402" in err_str or "payment" in err_str.lower() or "insufficient" in err_str.lower():
                        # Free model kullanıldığında normalde 402 gelmemeli ama geliyorsa fallback yapmaksızın bitirelim
                        return "CRITICAL_ERROR: OpenRouter 402 Bakiye Hatası."

                    # Rate Limit
                    if "429" in err_str or "rate limit" in err_str.lower():
                        logger.warning(f"[OpenRouter] {current_model} rate limit (ücretsiz sınıra takıldınız). 5 sn bekleniyor...")
                        await asyncio.sleep(5)
                        continue
                    
                    # Timeout veya Provider meşgul/kapalı vs.
                    if "timeout" in err_str.lower():
                        logger.warning(f"[OpenRouter] {current_model} timeout aldı.")
                        break # Direkt sonraki fallback modele geç
                    
                    # Provider error 502/503 (OpenRouter bazen free modellerde hata fırlatabilir)
                    logger.warning(f"[OpenRouter] Beklenmeyen hata ({current_model}): {err_str[:150]}")
                    break # Diğer denemeye geçmeden direkt diğer fallback modele atla

        # Hiçbir model çalışmadı
        return f"CRITICAL_ERROR: Tüm OpenRouter modelleri çöktü veya rate-limit/yoğunluk sebebiyle meşgul. Son Hata: {last_err[:200]}"