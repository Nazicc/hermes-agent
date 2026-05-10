#!/usr/bin/env python3
"""
Honcho Bridge — SINK mode (精简版)

Honcho 只做两件事：
  1. Write: session 消息 → deriver 自动提取 observations
  2. Sync: conclusions → viking_remember (L2)

读取路径统一走 L2 (viking_search / hindsight_recall)。
唯一例外: chat() 按需辩证推理（一次性，不持久化）。
"""

import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger("honcho_bridge")

HONCHO_BASE = "http://localhost:8889/v3"
DEFAULT_WS = "hermes-agent"


class HonchoBridge:
    def __init__(self, base_url: str = HONCHO_BASE, workspace: str = DEFAULT_WS):
        self.base_url = base_url.rstrip("/")
        self.workspace = workspace
        self._client = httpx.Client(timeout=15.0)

    # ─── Write: Hermes → Honcho (单向) ─────────────────────────

    def write_messages(self, session_id: str, peer_id: str, messages: list[dict]) -> int:
        """Sync session messages to Honcho. Deriver auto-processes."""
        # Ensure session
        try:
            self._client.post(
                f"{self.base_url}/workspaces/{self.workspace}/sessions",
                json={"id": session_id},
            )
        except Exception:
            pass

        # Add peer to session
        try:
            self._client.post(
                f"{self.base_url}/workspaces/{self.workspace}/sessions/{session_id}/peers",
                json={"peer_id": peer_id},
            )
        except Exception:
            pass

        # Write messages
        try:
            r = self._client.post(
                f"{self.base_url}/workspaces/{self.workspace}/sessions/{session_id}/messages",
                json={"messages": messages},
            )
            r.raise_for_status()
            result = r.json()
            count = len(result) if isinstance(result, list) else 1
            logger.info(f"Honcho: wrote {count} msgs to session {session_id}")
            return count
        except Exception as e:
            logger.error(f"Honcho write failed: {e}")
            return 0

    # ─── Sync: Honcho conclusions → L2 (viking_remember) ───────

    def get_conclusions(self, limit: int = 50) -> list[dict]:
        """Get derived conclusions from Honcho."""
        try:
            r = self._client.post(
                f"{self.base_url}/workspaces/{self.workspace}/conclusions/list",
                json={"limit": limit},
            )
            r.raise_for_status()
            data = r.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            return items if isinstance(items, list) else []
        except Exception as e:
            logger.warning(f"Honcho conclusions failed: {e}")
            return []

    def sync_conclusions_to_viking(self, viking_remember_fn, existing_check_fn=None) -> int:
        """
        Sync new conclusions to OpenViking L2.
        
        Args:
            viking_remember_fn: callable(content, category) 
            existing_check_fn: callable(query) → bool (skip if already in L2)
        """
        conclusions = self.get_conclusions()
        synced = 0
        for c in conclusions:
            content = c.get("content", "").strip()
            if not content:
                continue
            tagged = f"[L4] {content}"
            
            # Skip if already synced
            if existing_check_fn:
                try:
                    if existing_check_fn(content):
                        continue
                except Exception:
                    pass
            
            try:
                viking_remember_fn(content=tagged, category="pattern")
                synced += 1
            except Exception as e:
                logger.warning(f"Sync to Viking failed: {e}")
        
        logger.info(f"Honcho→Viking: synced {synced}/{len(conclusions)} conclusions")
        return synced

    # ─── Chat: 按需辩证推理（一次性，不持久化）────────────────

    def chat(self, query: str, peer_id: str = "r00tcc") -> str:
        """Dialectic Q&A — one-shot reasoning, not persisted."""
        try:
            r = self._client.post(
                f"{self.base_url}/workspaces/{self.workspace}/peers/{peer_id}/chat",
                json={"query": query},
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json().get("content", "")
        except Exception as e:
            logger.warning(f"Honcho chat failed: {e}")
            return ""

    # ─── Health ──────────────────────────────────────────────────

    def health(self) -> bool:
        try:
            r = self._client.get(self.base_url.replace("/v3", "") + "/health")
            return r.status_code == 200
        except Exception:
            return False

    def queue_status(self) -> dict:
        try:
            r = self._client.get(
                f"{self.base_url}/workspaces/{self.workspace}/queue/status",
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bridge = HonchoBridge()
    print(f"Health: {bridge.health()}")
    print(f"Queue: {json.dumps(bridge.queue_status(), indent=2)}")
    
    conclusions = bridge.get_conclusions()
    print(f"\nConclusions ({len(conclusions)}):")
    for c in conclusions[:5]:
        print(f"  - {c.get('content', '')[:80]}")
