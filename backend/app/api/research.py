"""
Research API - WebSocket araştırma, iptal desteği, geçmiş kaydetme
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from backend.app.api.ws_manager import manager
from backend.app.services.research_agent import ResearchAgent
from backend.app.db.database import get_session
from backend.app.models.user import User, ResearchHistory
from loguru import logger
import uuid, json, asyncio

router = APIRouter()

# İptal edilmiş session'ları takip et
_cancelled_sessions = set()


class ResearchRequest(BaseModel):
    query: str
    depth: str = "medium"
    language: str = "tr"


@router.websocket("/ws/research/{session_id}")
async def research_websocket(session_id: str, websocket: WebSocket):
    await manager.connect(session_id, websocket)
    try:
        data = await websocket.receive_json()
        query = data.get("query", "")
        depth = data.get("depth", "medium")
        language = data.get("language", "tr")
        user_email = data.get("user_email", "")
        
        # Kullanıcıya Özel AI Anahtarları
        groq_api_key = data.get("groq_api_key", "")
        gemini_api_key = data.get("gemini_api_key", "")
        deepseek_api_key = data.get("deepseek_api_key", "")

        # Gelişmiş filtreler
        time_filter = data.get("time_filter", "all")       # all | 1y | 5y
        domain_filter = data.get("domain_filter", "all")   # all | edu | gov | org
        max_sources = data.get("max_sources", 0)            # 0 = default

        if not query:
            await manager.send_error(session_id, "Arama sorgusu boş olamaz!")
            return

        # İptal kontrolü
        _cancelled_sessions.discard(session_id)

        agent = ResearchAgent(
            progress_callback=lambda msg: manager.send_progress(session_id, msg),
            cancel_check=lambda: session_id in _cancelled_sessions,
            groq_key=groq_api_key,
            gemini_key=gemini_api_key,
            deepseek_key=deepseek_api_key,
        )

        # Arka planda iptal mesajı dinle
        async def listen_for_cancel():
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
                    if msg.get("type") == "cancel":
                        _cancelled_sessions.add(session_id)
                        await manager.send_progress(session_id, "⛔ Araştırma iptal ediliyor...")
                        break
            except (asyncio.TimeoutError, WebSocketDisconnect, Exception):
                pass

        cancel_task = asyncio.create_task(listen_for_cancel())

        result = await agent.run(
            query=query, depth=depth, language=language,
            time_filter=time_filter, domain_filter=domain_filter,
            max_sources_override=max_sources,
        )

        cancel_task.cancel()

        if result.get("cancelled"):
            await manager.send_progress(session_id, "⛔ Araştırma iptal edildi.")
            await manager.send_error(session_id, "Araştırma kullanıcı tarafından iptal edildi.")
        elif "error" in result:
            await manager.send_error(session_id, result["error"])
        else:
            await manager.send_result(session_id, result)

            # Geçmişe kaydet
            if user_email:
                try:
                    from backend.app.db.database import get_session as gs
                    db = next(gs())
                    user = db.exec(select(User).where(User.email == user_email)).first()
                    if user:
                        history = ResearchHistory(
                            user_id=user.id, query=query, depth=depth,
                            language=language,
                            result_json=json.dumps(result, ensure_ascii=False, default=str),
                            source_count=result.get("source_count", 0),
                            reliability_score=result.get("validation", {}).get("reliability_score", 0),
                        )
                        db.add(history)
                        # Kotayı düşür
                        if user.quota_remaining > 0:
                            user.quota_remaining -= 1
                            db.add(user)
                        db.commit()
                except Exception as ex:
                    logger.warning(f"Geçmiş kaydetme hatası: {ex}")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Research error: {e}")
        try:
            await manager.send_error(session_id, f"Araştırma hatası: {str(e)}")
        except Exception:
            pass
    finally:
        _cancelled_sessions.discard(session_id)
        await manager.disconnect(session_id)


@router.post("/cancel/{session_id}")
async def cancel_research(session_id: str):
    """HTTP ile araştırma iptali (yedek)."""
    _cancelled_sessions.add(session_id)
    return {"message": "İptal sinyali gönderildi."}


@router.post("/start")
async def start_research_session():
    session_id = str(uuid.uuid4())
    return {"session_id": session_id, "ws_url": f"/api/research/ws/research/{session_id}"}


@router.post("/check-quota")
async def check_quota(user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return {"quota_remaining": user.quota_remaining, "is_unlimited": False}
