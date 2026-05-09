"""Extracted from gateway/run.py — UpdateManager."""
import asyncio
import json
import logging
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from gateway.platforms.base import MessageEvent
from gateway.config import Platform


def _get_hermes_home():
    """Resolve hermes_home at runtime — checks gateway.run._hermes_home for test patching."""
    import gateway.run as _gr
    return _gr._hermes_home


def _resolve_hermes_bin() -> Optional[list[str]]:
    """Resolve the Hermes update command as argv parts.

    Tries in order:
    1. ``shutil.which("hermes")`` — standard PATH lookup
    2. ``sys.executable -m hermes_cli.main`` — fallback when Hermes is running
       from a venv/module invocation and the ``hermes`` shim is not on PATH

    Returns argv parts ready for quoting/joining, or ``None`` if neither works.
    """
    hermes_bin = shutil.which("hermes")
    if hermes_bin:
        return [hermes_bin]

    try:
        import importlib.util
        if importlib.util.find_spec("hermes_cli") is not None:
            return [sys.executable, "-m", "hermes_cli.main"]
    except Exception:
        pass

    return None


def _is_managed() -> bool:
    """Check if this is a managed (non-self-updatable) installation."""
    try:
        from hermes_cli.config import is_managed
        return is_managed()
    except ImportError:
        return False


def _format_managed_message(action: str = "modify this Hermes installation") -> str:
    """Format a message for managed installations."""
    try:
        from hermes_cli.config import format_managed_message
        return format_managed_message(action)
    except ImportError:
        return f"This installation is managed and cannot {action}."

logger = logging.getLogger(__name__)


class UpdateManager:
    """Extracted from GatewayRunner — manages update."""

    _UPDATE_ALLOWED_PLATFORMS = frozenset({
        Platform.TELEGRAM, Platform.DISCORD, Platform.SLACK, Platform.WHATSAPP,
        Platform.SIGNAL, Platform.MATTERMOST, Platform.MATRIX,
        Platform.HOMEASSISTANT, Platform.EMAIL, Platform.SMS, Platform.DINGTALK,
        Platform.FEISHU, Platform.WECOM, Platform.WECOM_CALLBACK, Platform.WEIXIN,
        Platform.BLUEBUBBLES, Platform.QQBOT, Platform.LOCAL,
    })

    def __init__(self, runner):
        self._r = runner
        self._update_prompt_pending = {}

    def handle_pending_update_response(self, source, event):
        """If an update prompt is pending for this session, intercept the user's response.

        Returns a confirmation message if intercepted (caller should skip normal
        message handling), or None if no prompt was pending.
        """
        session_key = self._r._session_key_for_source(source)
        if not self._update_prompt_pending.get(session_key):
            return None
        raw = (event.text or "").strip()
        # Accept /approve and /deny as shorthand for yes/no
        cmd = event.get_command() if hasattr(event, 'get_command') else None
        if cmd in ("approve", "yes"):
            response_text = "y"
        elif cmd in ("deny", "no"):
            response_text = "n"
        else:
            response_text = raw
        if response_text:
            response_path = _get_hermes_home() / ".update_response"
            try:
                tmp = response_path.with_suffix(".tmp")
                tmp.write_text(response_text)
                tmp.replace(response_path)
            except OSError as e:
                logger.warning("Failed to write update response: %s", e)
                return f"✗ Failed to send response to update process: {e}"
        self._update_prompt_pending.pop(session_key, None)
        label = response_text if len(response_text) <= 20 else response_text[:20] + "…"
        return f"✓ Sent `{label}` to the update process."

    async def handle_update_command(self, event: MessageEvent) -> str:
        """Handle /update command — update Hermes Agent to the latest version.

        Spawns ``hermes update`` in a detached session (via ``setsid``) so it
        survives the gateway restart that ``hermes update`` may trigger. Marker
        files are written so either the current gateway process or the next one
        can notify the user when the update finishes.
        """

        # Block non-messaging platforms (API server, webhooks, ACP)
        platform = event.source.platform
        if platform not in self._r._UPDATE_ALLOWED_PLATFORMS:
            return "✗ /update is only available from messaging platforms. Run `hermes update` from the terminal."

        if _is_managed():
            return f"✗ {_format_managed_message('update Hermes Agent')}"

        project_root = Path(__file__).parent.parent.parent.resolve()  # runners/ -> gateway/ -> project_root
        git_dir = project_root / '.git'

        if not git_dir.exists():
            return "✗ Not a git repository — cannot update."

        hermes_cmd = _resolve_hermes_bin()
        if not hermes_cmd:
            return (
                "✗ Could not locate the `hermes` command. "
                "Hermes is running, but the update command could not find the "
                "executable on PATH or via the current Python interpreter. "
                "Try running `hermes update` manually in your terminal."
            )

        pending_path = _get_hermes_home() / ".update_pending.json"
        output_path = _get_hermes_home() / ".update_output.txt"
        exit_code_path = _get_hermes_home() / ".update_exit_code"
        session_key = self._r._session_key_for_source(event.source)
        pending = {
            "platform": event.source.platform.value,
            "chat_id": event.source.chat_id,
            "user_id": event.source.user_id,
            "session_key": session_key,
            "timestamp": datetime.now().isoformat(),
        }
        _tmp_pending = pending_path.with_suffix(".tmp")
        _tmp_pending.write_text(json.dumps(pending))
        _tmp_pending.replace(pending_path)
        exit_code_path.unlink(missing_ok=True)

        # Spawn `hermes update --gateway` detached so it survives gateway restart.
        # --gateway enables file-based IPC for interactive prompts (stash
        # restore, config migration) so the gateway can forward them to the
        # user instead of silently skipping them.
        # Use setsid for portable session detach (works under system services
        # where systemd-run --user fails due to missing D-Bus session).
        # PYTHONUNBUFFERED ensures output is flushed line-by-line so the
        # gateway can stream it to the messenger in near-real-time.
        hermes_cmd_str = " ".join(shlex.quote(part) for part in hermes_cmd)
        update_cmd = (
            f"PYTHONUNBUFFERED=1 {hermes_cmd_str} update --gateway"
            f" > {shlex.quote(str(output_path))} 2>&1; "
            f"status=$?; printf '%s' \"$status\" > {shlex.quote(str(exit_code_path))}"
        )
        try:
            setsid_bin = shutil.which("setsid")
            if setsid_bin:
                # Preferred: setsid creates a new session, fully detached
                subprocess.Popen(
                    [setsid_bin, "bash", "-c", update_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            else:
                # Fallback: start_new_session=True calls os.setsid() in child
                subprocess.Popen(
                    ["bash", "-c", update_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
        except Exception as e:
            pending_path.unlink(missing_ok=True)
            exit_code_path.unlink(missing_ok=True)
            return f"✗ Failed to start update: {e}"

        self.schedule_update_notification_watch()
        return "⚕ Starting Hermes update… I'll stream progress here."



    def schedule_update_notification_watch(self) -> None:
        """Ensure a background task is watching for update completion."""
        existing_task = getattr(self, "_update_notification_task", None)
        if existing_task and not existing_task.done():
            return

        try:
            self._r._update_notification_task = asyncio.create_task(
                self.watch_update_progress()
            )
        except RuntimeError:
            logger.debug("Skipping update notification watcher: no running event loop")



    async def watch_update_progress(
        self,
        poll_interval: float = 2.0,
        stream_interval: float = 4.0,
        timeout: float = 1800.0,
    ) -> None:
        """Watch ``hermes update --gateway``, streaming output + forwarding prompts.

        Polls ``.update_output.txt`` for new content and sends chunks to the
        user periodically.  Detects ``.update_prompt.json`` (written by the
        update process when it needs user input) and forwards the prompt to
        the messenger.  The user's next message is intercepted by
        ``_handle_message`` and written to ``.update_response``.
        """

        pending_path = _get_hermes_home() / ".update_pending.json"
        claimed_path = _get_hermes_home() / ".update_pending.claimed.json"
        output_path = _get_hermes_home() / ".update_output.txt"
        exit_code_path = _get_hermes_home() / ".update_exit_code"
        prompt_path = _get_hermes_home() / ".update_prompt.json"

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        # Resolve the adapter and chat_id for sending messages
        adapter = None
        chat_id = None
        session_key = None
        for path in (claimed_path, pending_path):
            if path.exists():
                try:
                    pending = json.loads(path.read_text())
                    platform_str = pending.get("platform")
                    chat_id = pending.get("chat_id")
                    session_key = pending.get("session_key")
                    if platform_str and chat_id:
                        platform = Platform(platform_str)
                        adapter = self._r.adapters.get(platform)
                        # Fallback session key if not stored (old pending files)
                        if not session_key:
                            session_key = f"{platform_str}:{chat_id}"
                    break
                except Exception:
                    pass

        if not adapter or not chat_id:
            logger.warning("Update watcher: cannot resolve adapter/chat_id, falling back to completion-only")
            # Fall back to old behavior: wait for exit code and send final notification
            while (pending_path.exists() or claimed_path.exists()) and loop.time() < deadline:
                if exit_code_path.exists():
                    await self.send_update_notification()
                    return
                await asyncio.sleep(poll_interval)
            if (pending_path.exists() or claimed_path.exists()) and not exit_code_path.exists():
                exit_code_path.write_text("124")
                await self.send_update_notification()
            return

        def _strip_ansi(text: str) -> str:
            return re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)

        bytes_sent = 0
        last_stream_time = loop.time()
        buffer = ""

        async def _flush_buffer() -> None:
            """Send buffered output to the user."""
            nonlocal buffer, last_stream_time
            if not buffer.strip():
                buffer = ""
                return
            # Chunk to fit message limits (Telegram: 4096, others: generous)
            clean = _strip_ansi(buffer).strip()
            buffer = ""
            last_stream_time = loop.time()
            if not clean:
                return
            # Split into chunks if too long
            max_chunk = 3500
            chunks = [clean[i:i + max_chunk] for i in range(0, len(clean), max_chunk)]
            for chunk in chunks:
                try:
                    await adapter.send(chat_id, f"```\n{chunk}\n```")
                except Exception as e:
                    logger.debug("Update stream send failed: %s", e)

        while loop.time() < deadline:
            # Check for completion
            if exit_code_path.exists():
                # Read any remaining output
                if output_path.exists():
                    try:
                        content = output_path.read_text()
                        if len(content) > bytes_sent:
                            buffer += content[bytes_sent:]
                            bytes_sent = len(content)
                    except OSError:
                        pass
                await _flush_buffer()

                # Send final status
                try:
                    exit_code_raw = exit_code_path.read_text().strip() or "1"
                    exit_code = int(exit_code_raw)
                    if exit_code == 0:
                        await adapter.send(chat_id, "✅ Hermes update finished.")
                    else:
                        await adapter.send(chat_id, "❌ Hermes update failed (exit code {}).".format(exit_code))
                    logger.info("Update finished (exit=%s), notified %s", exit_code, session_key)
                except Exception as e:
                    logger.warning("Update final notification failed: %s", e)

                # Cleanup
                for p in (pending_path, claimed_path, output_path,
                          exit_code_path, prompt_path):
                    p.unlink(missing_ok=True)
                (_get_hermes_home() / ".update_response").unlink(missing_ok=True)
                self._update_prompt_pending.pop(session_key, None)
                return

            # Check for new output
            if output_path.exists():
                try:
                    content = output_path.read_text()
                    if len(content) > bytes_sent:
                        buffer += content[bytes_sent:]
                        bytes_sent = len(content)
                except OSError:
                    pass

            # Flush buffer periodically
            if buffer.strip() and (loop.time() - last_stream_time) >= stream_interval:
                await _flush_buffer()

            # Check for prompts — only forward if we haven't already sent
            # one that's still awaiting a response.  Without this guard the
            # watcher would re-read the same .update_prompt.json every poll
            # cycle and spam the user with duplicate prompt messages.
            if (prompt_path.exists() and session_key
                    and not self._update_prompt_pending.get(session_key)):
                try:
                    prompt_data = json.loads(prompt_path.read_text())
                    prompt_text = prompt_data.get("prompt", "")
                    default = prompt_data.get("default", "")
                    if prompt_text:
                        # Flush any buffered output first so the user sees
                        # context before the prompt
                        await _flush_buffer()
                        # Try platform-native buttons first (Discord, Telegram)
                        sent_buttons = False
                        if getattr(type(adapter), "send_update_prompt", None) is not None:
                            try:
                                await adapter.send_update_prompt(
                                    chat_id=chat_id,
                                    prompt=prompt_text,
                                    default=default,
                                    session_key=session_key,
                                )
                                sent_buttons = True
                            except Exception as btn_err:
                                logger.debug("Button-based update prompt failed: %s", btn_err)
                        if not sent_buttons:
                            default_hint = f" (default: {default})" if default else ""
                            await adapter.send(
                                chat_id,
                                f"⚕ **Update needs your input:**\n\n"
                                f"{prompt_text}{default_hint}\n\n"
                                f"Reply `/approve` (yes) or `/deny` (no), "
                                f"or type your answer directly."
                            )
                        self._update_prompt_pending[session_key] = True
                        # Remove the prompt file so it isn't re-read on the
                        # next poll cycle.  The update process only needs
                        # .update_response to continue — it doesn't re-check
                        # .update_prompt.json while waiting.
                        prompt_path.unlink(missing_ok=True)
                        logger.info("Forwarded update prompt to %s: %s", session_key, prompt_text[:80])
                except (json.JSONDecodeError, OSError) as e:
                    logger.debug("Failed to read update prompt: %s", e)

            await asyncio.sleep(poll_interval)

        # Timeout
        if not exit_code_path.exists():
            logger.warning("Update watcher timed out after %.0fs", timeout)
            exit_code_path.write_text("124")
            await _flush_buffer()
            try:
                await adapter.send(chat_id, "❌ Hermes update timed out after 30 minutes.")
            except Exception:
                pass
            for p in (pending_path, claimed_path, output_path,
                      exit_code_path, prompt_path):
                p.unlink(missing_ok=True)
            (_get_hermes_home() / ".update_response").unlink(missing_ok=True)
            self._update_prompt_pending.pop(session_key, None)



    async def send_update_notification(self) -> bool:
        """If an update finished, notify the user.

        Returns False when the update is still running so a caller can retry
        later. Returns True after a definitive send/skip decision.

        This is the legacy notification path used when the streaming watcher
        cannot resolve the adapter (e.g. after a gateway restart where the
        platform hasn't reconnected yet).
        """

        pending_path = _get_hermes_home() / ".update_pending.json"
        claimed_path = _get_hermes_home() / ".update_pending.claimed.json"
        output_path = _get_hermes_home() / ".update_output.txt"
        exit_code_path = _get_hermes_home() / ".update_exit_code"

        if not pending_path.exists() and not claimed_path.exists():
            return False

        cleanup = True
        active_pending_path = claimed_path
        try:
            if pending_path.exists():
                try:
                    pending_path.replace(claimed_path)
                except FileNotFoundError:
                    if not claimed_path.exists():
                        return True
            elif not claimed_path.exists():
                return True

            pending = json.loads(claimed_path.read_text())
            platform_str = pending.get("platform")
            chat_id = pending.get("chat_id")

            if not exit_code_path.exists():
                logger.info("Update notification deferred: update still running")
                cleanup = False
                active_pending_path = pending_path
                claimed_path.replace(pending_path)
                return False

            exit_code_raw = exit_code_path.read_text().strip() or "1"
            exit_code = int(exit_code_raw)

            # Read the captured update output
            output = ""
            if output_path.exists():
                output = output_path.read_text()

            # Resolve adapter
            platform = Platform(platform_str)
            adapter = self._r.adapters.get(platform)

            if adapter and chat_id:
                # Strip ANSI escape codes for clean display
                output = re.sub(r'\x1b\[[0-9;]*m', '', output).strip()
                if output:
                    if len(output) > 3500:
                        output = "…" + output[-3500:]
                    if exit_code == 0:
                        msg = f"✅ Hermes update finished.\n\n```\n{output}\n```"
                    else:
                        msg = f"❌ Hermes update failed.\n\n```\n{output}\n```"
                else:
                    if exit_code == 0:
                        msg = "✅ Hermes update finished successfully."
                    else:
                        msg = "❌ Hermes update failed. Check the gateway logs or run `hermes update` manually for details."
                await adapter.send(chat_id, msg)
                logger.info(
                    "Sent post-update notification to %s:%s (exit=%s)",
                    platform_str,
                    chat_id,
                    exit_code,
                )
        except Exception as e:
            logger.warning("Post-update notification failed: %s", e)
        finally:
            if cleanup:
                active_pending_path.unlink(missing_ok=True)
                claimed_path.unlink(missing_ok=True)
                output_path.unlink(missing_ok=True)
                exit_code_path.unlink(missing_ok=True)

        return True



    async def send_restart_notification(self) -> None:
        """Notify the chat that initiated /restart that the gateway is back."""
        notify_path = _get_hermes_home() / ".restart_notify.json"
        if not notify_path.exists():
            return

        try:
            data = json.loads(notify_path.read_text())
            platform_str = data.get("platform")
            chat_id = data.get("chat_id")
            thread_id = data.get("thread_id")

            if not platform_str or not chat_id:
                return

            platform = Platform(platform_str)
            adapter = self._r.adapters.get(platform)
            if not adapter:
                logger.debug(
                    "Restart notification skipped: %s adapter not connected",
                    platform_str,
                )
                return

            metadata = {"thread_id": thread_id} if thread_id else None
            await adapter.send(
                chat_id,
                "♻ Gateway restarted successfully. Your session continues.",
                metadata=metadata,
            )
            logger.info(
                "Sent restart notification to %s:%s",
                platform_str,
                chat_id,
            )
        except Exception as e:
            logger.warning("Restart notification failed: %s", e)
        finally:
            notify_path.unlink(missing_ok=True)



