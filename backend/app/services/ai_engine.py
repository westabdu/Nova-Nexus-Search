"""
Multi-AI Engine - Hybrid (Groq + Gemini + DeepSeek)
Kullanıcıya özel API anahtarları, Rate limit retry, Token boyutu yönetimi ve Hibrit Yönlendirme.
"""
from groq import AsyncGroq
from backend.app.core.config import settings
from loguru import logger
import asyncio
import warnings

# Gemini SDK
warnings.filterwarnings("ignore", category=FutureWarning, module="google")
try:
    import google.generativeai as genai
    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False

try:
    import openai
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False


class MultiAIEngine:
    def __init__(self, groq_key: str = "", gemini_key: str = "", deepseek_key: str = ""):
        # Front-End'den kullanıcı key gelmezse, .env'deki genel ayarları kullan.
        self.groq_api_key = groq_key or settings.GROQ_API_KEY
        self.gemini_api_key = gemini_key or settings.GEMINI_API_KEY
        self.deepseek_api_key = deepseek_key

        self.groq_client = AsyncGroq(api_key=self.groq_api_key) if self.groq_api_key else None
        
        self.gemini_model = None
        if _HAS_GENAI and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            except Exception as e:
                logger.warning(f"Gemini init hatası: {e}")

        self.deepseek_client = None
        if _HAS_OPENAI and self.deepseek_api_key:
            try:
                self.deepseek_client = openai.AsyncOpenAI(api_key=self.deepseek_api_key, base_url="https://api.deepseek.com")
            except Exception as e:
                logger.warning(f"DeepSeek init hatası: {e}")

    # ─── Hibrit Seçici (Dynamic Router) ──────────────────────────────────
    async def hybrid_generate(self, prompt: str, task_type: str = "synthesis", system_message: str = "You are a research AI.", language: str = "tr") -> str:
        """
        Token sayısı ve göreve göre modelleri dinamik seçer.
        task_type: "filter" | "synthesis" | "translation" | "reasoning"
        """
        char_count = len(prompt)
        
        if task_type == "filter":
            # Hızlı Süzme: Daima Groq Llama-3.1-8B (Ucuz, hızlı)
            logger.info("[Hibrit] Model Seçildi: Groq Llama-3.1-8B (Girdi: Filtreleme)")
            return await self._analyze_with_groq(prompt, system_message, model="llama-3.1-8b-instant", max_tokens=600)

        elif task_type == "translation":
            # Çeviri: Gemini Flash
            logger.info("[Hibrit] Model Seçildi: Gemini 2.0 Flash (Girdi: Çeviri)")
            return await self._synthesize_with_gemini(prompt, system_message)

        elif task_type == "reasoning" and self.deepseek_client:
            # Yedek / Çok Karmaşık
            logger.info("[Hibrit] Model Seçildi: DeepSeek Reasoner (Girdi: Karmaşık Çıkarım)")
            return await self._analyze_with_deepseek(prompt, system_message, model="deepseek-reasoner", max_tokens=4000)

        elif task_type == "synthesis":
            # Sentez: Token sınırına (karakter sınırına) göre dinamik karar
            if char_count < 25000:
                logger.info(f"[Hibrit] Model Seçildi: Groq Llama-3.3-70B (Yük: {char_count} char)")
                return await self._analyze_with_groq(prompt, system_message, model="llama-3.3-70b-versatile", max_tokens=6000)
            else:
                if self.gemini_model:
                    logger.info(f"[Hibrit] Model Seçildi: Gemini 2.0 Flash (Yük: {char_count} char, Büyük Bağlam)")
                    return await self._synthesize_with_gemini(prompt, system_message)
                else:
                    # Gemini yok ama token büyükse, mecburen Groq'a gönder ama promptu kırp
                    logger.warning("[Hibrit] Uyarı: Büyük bağlam için Gemini bulunamadı, Groq ile kısaltılıp çalıştırılıyor.")
                    clipped = prompt[:25000] + "\n\n[...Token eşiği nedeniyle metin kırpıldı...]"
                    return await self._analyze_with_groq(clipped, system_message, model="llama-3.3-70b-versatile", max_tokens=6000)

        # Fallback
        return await self._synthesize_with_gemini(prompt, system_message)
        
    # ─── Model Spesifik Metotlar ──────────────────────────────────────────

    async def _analyze_with_deepseek(self, prompt: str, system_message: str, model: str = "deepseek-reasoner", max_tokens: int = 4000) -> str:
        if not self.deepseek_client:
            return "DEEPSEEK API KEY MISSING"
        try:
            resp = await self.deepseek_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek API Error: {e}")
            return f"Error: {e}"

    async def _analyze_with_groq(self, prompt: str, system_message: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 4096) -> str:
        if not self.groq_client:
            logger.warning("GROQ API KEY IS MISSING, fallback to Gemini")
            return await self._synthesize_with_gemini(prompt, system_message)
            
        # Retry mantığı
        for attempt in range(3):
            try:
                completion = await self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    model=model,
                    temperature=0.3,
                    max_tokens=max_tokens,
                )
                return completion.choices[0].message.content
            except Exception as e:
                err_str = str(e)
                if "rate_limit" in err_str or "429" in err_str:
                    wait = 5 * (attempt + 1)
                    logger.warning(f"Groq rate limit ({model}), {wait}s bekleniyor... (deneme {attempt+1}/3)")
                    await asyncio.sleep(wait)
                    if attempt == 1 and model != "llama-3.1-8b-instant":
                        model = "llama-3.1-8b-instant"
                        logger.info("Groq: Küçük model (8B) kullanılıyor...")
                    continue
                logger.error(f"Groq API Error: {e}")
                return await self._synthesize_with_gemini(prompt, system_message) # Fallback to Gemini if groq totally fails
        return "Error: Tüm AI modelleri şu anda meşgul (Groq rate limit aşıldı)."

    async def _synthesize_with_gemini(self, prompt: str, system_message: str) -> str:
        if not self.gemini_model:
            logger.warning("Gemini kullanılamıyor, Groq fallback aktif.")
            return await self._analyze_with_groq(prompt, system_message, model="llama-3.3-70b-versatile", max_tokens=6000)
            
        full_prompt = f"{system_message}\n\nTask:\n{prompt}"
        for attempt in range(2):
            try:
                response = await asyncio.to_thread(self.gemini_model.generate_content, full_prompt)
                return response.text
            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt == 0:
                    import re
                    wait_match = re.search(r'retry in (\d+)', err_str)
                    wait = int(wait_match.group(1)) + 2 if wait_match else 15
                    logger.warning(f"Gemini rate limit, {wait}s bekleniyor...")
                    await asyncio.sleep(wait)
                    continue
                logger.error(f"Gemini API Error: {e}")
                break
                
        logger.info("Groq fallback ile sentez yapılıyor...")
        return await self._analyze_with_groq(prompt, system_message, model="llama-3.1-8b-instant", max_tokens=6000)
