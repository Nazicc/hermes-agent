"""Extracted from gateway/run.py — MemoryFlushManager."""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryFlushManager:
    """Extracted from GatewayRunner — manages memoryflush."""

    def __init__(self, runner):
        self._r = runner

    def flush_memories_for_session(
        self,
        old_session_id: str,
        session_key: Optional[str] = None,
    ):
        """Prompt the agent to save memories/skills before context is lost.

        Synchronous worker — meant to be called via run_in_executor from
        an async context so it doesn't block the event loop.
        """
        # Skip cron sessions — they run headless with no meaningful user
        # conversation to extract memories from.
        if old_session_id and old_session_id.startswith("cron_"):
            logger.debug("Skipping memory flush for cron session: %s", old_session_id)
            return

        try:
            history = self._r.session_store.load_transcript(old_session_id)
            if not history or len(history) < 4:
                return

            from run_agent import AIAgent
            model, runtime_kwargs = self._r._resolve_session_agent_runtime(
                session_key=session_key,
            )
            if not runtime_kwargs.get("api_key"):
                return

            tmp_agent = AIAgent(
                **runtime_kwargs,
                model=model,
                max_iterations=8,
                quiet_mode=True,
                skip_memory=True,  # Flush agent — no memory provider
                enabled_toolsets=["memory", "skills"],
                session_id=old_session_id,
            )
            try:
                # Fully silence the flush agent — quiet_mode only suppresses init
                # messages; tool call output still leaks to the terminal through
                # _safe_print → _print_fn.  Set a no-op to prevent that.
                tmp_agent._print_fn = lambda *a, **kw: None

                # Build conversation history from transcript
                msgs = [
                    {"role": m.get("role"), "content": m.get("content")}
                    for m in history
                    if m.get("role") in ("user", "assistant") and m.get("content")
                ]

                # Read live memory state from disk so the flush agent can see
                # what's already saved and avoid overwriting newer entries.
                _current_memory = ""
                try:
                    from tools.memory_tool import get_memory_dir
                    _mem_dir = get_memory_dir()
                    for fname, label in [
                        ("MEMORY.md", "MEMORY (your personal notes)"),
                        ("USER.md", "USER PROFILE (who the user is)"),
                    ]:
                        fpath = _mem_dir / fname
                        if fpath.exists():
                            content = fpath.read_text(encoding="utf-8").strip()
                            if content:
                                _current_memory += f"\n\n## Current {label}:\n{content}"
                except Exception:
                    pass  # Non-fatal — flush still works, just without the guard

                # Give the agent a real turn to think about what to save
                flush_prompt = (
                    "[System: This session is about to be automatically reset due to "
                    "inactivity or a scheduled daily reset. The conversation context "
                    "will be cleared after this turn.\n\n"
                    "Review the conversation above and:\n"
                    "1. Save any important facts, preferences, or decisions to memory "
                    "(user profile or your notes) that would be useful in future sessions.\n"
                    "2. If you discovered a reusable workflow or solved a non-trivial "
                    "problem, consider saving it as a skill.\n"
                    "3. If nothing is worth saving, that's fine — just skip.\n\n"
                )

                if _current_memory:
                    flush_prompt += (
                        "IMPORTANT — here is the current live state of memory. Other "
                        "sessions, cron jobs, or the user may have updated it since this "
                        "conversation ended. Do NOT overwrite or remove entries unless "
                        "the conversation above reveals something that genuinely "
                        "supersedes them. Only add new information that is not already "
                        "captured below."
                        f"{_current_memory}\n\n"
                    )

                flush_prompt += (
                    "Do NOT respond to the user. Just use the memory and skill_manage "
                    "tools if needed, then stop.]"
                )

                tmp_agent.run_conversation(
                    user_message=flush_prompt,
                    conversation_history=msgs,
                )
            finally:
                self._r._cleanup_agent_resources(tmp_agent)
            logger.info("Pre-reset memory flush completed for session %s", old_session_id)
        except Exception as e:
            logger.debug("Pre-reset memory flush failed for session %s: %s", old_session_id, e)



    async def async_flush_memories(
        self,
        old_session_id: str,
        session_key: Optional[str] = None,
    ):
        """Run the sync memory flush in a thread pool so it won't block the event loop."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self._r._flush_memories_for_session,
            old_session_id,
            session_key,
        )



