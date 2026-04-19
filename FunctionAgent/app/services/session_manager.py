# -*- coding: utf-8 -*-
"""会话上下文管理 — Redis优先，内存回退"""
import json
import time
import uuid
import threading
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionStore:
    """会话存储抽象（Redis / 内存）"""

    def __init__(self, use_redis: bool = False, host="localhost", port=6379,
                 db=0, password="", ttl=3600):
        self.use_redis = use_redis and self._check_redis(host, port)
        self.ttl = ttl
        self._memory: Dict[str, dict] = {}
        self._lock = threading.RLock()

        if self.use_redis:
            import redis
            self._redis = redis.Redis(host=host, port=port, db=db,
                                      password=password or None, decode_responses=True)
            logger.info(f"会话存储: Redis ({host}:{port})")
        else:
            self._redis = None
            logger.info("会话存储: 内存回退（Redis 未连接）")

    def _check_redis(self, host, port) -> bool:
        try:
            import redis
            r = redis.Redis(host=host, port=port, socket_connect_timeout=2)
            r.ping()
            return True
        except Exception:
            return False

    # ── 会话操作 ─────────────────────────────────────────────

    def create(self) -> str:
        sid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        data = {
            "session_id": sid,
            "messages": [],
            "created_at": now,
            "last_active": now,
            "tool_call_history": [],
        }
        self._save(sid, data)
        return sid

    def get(self, session_id: str) -> Optional[dict]:
        data = self._load(session_id)
        if data:
            data["last_active"] = datetime.now().isoformat()
            self._save(session_id, data)
        return data

    def add_message(self, session_id: str, role: str, content: str,
                    tool_calls: Optional[List[dict]] = None):
        data = self.get(session_id) or self._default_session(session_id)
        data["messages"].append({
            "role": role, "content": content, "timestamp": datetime.now().isoformat(),
            "tool_calls": tool_calls or [],
        })
        if tool_calls:
            data["tool_call_history"].extend(tool_calls)
        data["last_active"] = datetime.now().isoformat()
        self._save(session_id, data)

    def get_messages(self, session_id: str, max_turns: int = 10) -> List[dict]:
        data = self.get(session_id)
        if not data:
            return []
        msgs = data.get("messages", [])
        return msgs[-(max_turns * 2):]

    def add_tool_result(self, session_id: str, tool_call_id: str, content: str):
        data = self.get(session_id)
        if not data:
            return
        msgs = data["messages"]
        for m in reversed(msgs):
            if m.get("tool_call_id") == tool_call_id:
                m["tool_result"] = content
                break
        self._save(session_id, data)

    def list_sessions(self) -> List[dict]:
        with self._lock:
            if self.use_redis:
                keys = self._redis.keys("session:*")
                sessions = []
                for k in keys[:50]:
                    sid = k.split(":", 1)[1]
                    d = self._load(sid)
                    if d:
                        sessions.append({
                            "session_id": sid,
                            "message_count": len(d.get("messages", [])),
                            "created_at": d.get("created_at", ""),
                            "last_active": d.get("last_active", ""),
                        })
                return sorted(sessions, key=lambda x: x["last_active"], reverse=True)
            else:
                return sorted([
                    {"session_id": sid, "message_count": len(d.get("messages", [])),
                     "created_at": d.get("created_at", ""), "last_active": d.get("last_active", "")}
                    for sid, d in self._memory.items()
                ], key=lambda x: x["last_active"], reverse=True)

    def delete(self, session_id: str) -> bool:
        try:
            if self.use_redis:
                self._redis.delete(f"session:{session_id}")
            else:
                with self._lock:
                    if session_id in self._memory:
                        del self._memory[session_id]
            return True
        except Exception:
            return False

    def clear_all(self) -> int:
        """删除所有会话，返回删除数量"""
        sessions = self.list_sessions()
        count = 0
        for s in sessions:
            if self.delete(s["session_id"]):
                count += 1
        return count

    # ── 内部 ────────────────────────────────────────────────

    def _default_session(self, sid: str) -> dict:
        now = datetime.now().isoformat()
        return {"session_id": sid, "messages": [], "created_at": now,
                "last_active": now, "tool_call_history": []}

    def _save(self, session_id: str, data: dict):
        key = f"session:{session_id}"
        if self.use_redis:
            try:
                self._redis.setex(key, self.ttl, json.dumps(data, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Redis 保存失败: {e}")
                with self._lock:
                    self._memory[session_id] = data
        else:
            with self._lock:
                self._memory[session_id] = data

    def _load(self, session_id: str) -> Optional[dict]:
        key = f"session:{session_id}"
        if self.use_redis:
            try:
                raw = self._redis.get(key)
                if raw:
                    return json.loads(raw)
                return None
            except Exception as e:
                logger.error(f"Redis 加载失败: {e}")
                with self._lock:
                    return self._memory.get(session_id)
        else:
            with self._lock:
                return self._memory.get(session_id)


from app.config import settings
session_store = SessionStore(
    use_redis=settings.redis_host != "localhost" or settings.use_redis,
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    ttl=settings.redis_ttl,
)
