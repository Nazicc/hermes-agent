#!/usr/bin/env python3
"""
Team Mailbox — 跨 Worker 异步通信协议 v2

改进（基于代码审查）:
  - 文件锁: 使用 os.open()+fcntl.flock 先锁后写，避免截断竞态
  - 消息大小限制: body 最大 1MB（按字节计算），subject 最大 200 字符
  - 输入校验: recipient/sender 用 regex 校验防路径遍历
  - 时间戳: 统一 UTC
  - 文件名精度: 毫秒级防碰撞

目录结构:
  ~/.hermes/team/mailbox/
  ├── lead/          # Lead 的收件箱
  ├── coder/         # Coder 的收件箱
  ├── reviewer/      # Reviewer 的收件箱
  └── researcher/    # Researcher 的收件箱

消息格式 (JSON):
  {
    "from": "coder",
    "to": "lead",
    "type": "task_complete|question|alert|status",
    "priority": "high|normal|low",
    "subject": "简短标题",
    "body": "详细内容",
    "timestamp": "2026-05-12T20:00:00+08:00",
    "refs": ["bd-xxx"]  # 可选: 关联的 Beads issue
  }
"""

import argparse
import fcntl
import json
import os
import re
import sys
import glob
from datetime import datetime, timezone

MAILBOX_ROOT = os.path.expanduser("~/.hermes/team/mailbox")
VALID_RECIPIENTS = ["lead", "coder", "reviewer", "researcher"]
VALID_TYPES = ["task_complete", "question", "alert", "status", "review_result"]
VALID_PRIORITIES = ["high", "normal", "low"]

# 安全限制
MAX_MESSAGE_SIZE = 1 * 1024 * 1024  # 1MB (bytes)
MAX_SUBJECT_LEN = 200
MAX_REFS_COUNT = 20
RECIPIENT_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


def _validate_recipient(name: str, label: str = "recipient"):
    """校验收件人/发件人名称，防止路径遍历"""
    if not RECIPIENT_PATTERN.match(name):
        print(f"❌ Invalid {label}: '{name}' — only [a-zA-Z0-9_-] allowed", file=sys.stderr)
        sys.exit(1)
    # Defense-in-depth: 二次路径检查
    if os.sep in name or '/' in name or '..' in name:
        print(f"❌ Invalid {label}: path traversal detected in '{name}'", file=sys.stderr)
        sys.exit(1)


def _write_json_locked(filepath: str, data: dict):
    """带文件锁的 JSON 写入 — 先锁后截断，防止并发冲突"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fd = os.open(filepath, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)       # 先加锁
        os.ftruncate(fd, 0)                   # 锁内截断
        os.lseek(fd, 0, os.SEEK_SET)
        content = json.dumps(data, ensure_ascii=False, indent=2)
        os.write(fd, content.encode('utf-8'))
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _read_json_locked(filepath: str) -> dict:
    """带文件锁的 JSON 读取 — 共享锁"""
    fd = os.open(filepath, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_SH)       # 共享锁
        content = b''
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            content += chunk
        return json.loads(content.decode('utf-8'))
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def send_message(from_id: str, to_id: str, msg_type: str, subject: str,
                 body: str, priority: str = "normal", refs: list = None):
    """发送消息到收件箱"""
    # 输入校验
    _validate_recipient(to_id, "recipient")
    _validate_recipient(from_id, "sender")

    if to_id not in VALID_RECIPIENTS:
        print(f"❌ Invalid recipient: {to_id}. Valid: {VALID_RECIPIENTS}", file=sys.stderr)
        sys.exit(1)
    if from_id not in VALID_RECIPIENTS:
        print(f"❌ Invalid sender: {from_id}. Valid: {VALID_RECIPIENTS}", file=sys.stderr)
        sys.exit(1)
    if msg_type not in VALID_TYPES:
        print(f"❌ Invalid type: {msg_type}. Valid: {VALID_TYPES}", file=sys.stderr)
        sys.exit(1)

    # 大小限制（按字节计算）
    body_bytes = len(body.encode('utf-8'))
    if body_bytes > MAX_MESSAGE_SIZE:
        print(f"❌ Message body too large: {body_bytes} bytes (max {MAX_MESSAGE_SIZE})", file=sys.stderr)
        sys.exit(1)
    if len(subject) > MAX_SUBJECT_LEN:
        print(f"❌ Subject too long: {len(subject)} chars (max {MAX_SUBJECT_LEN})", file=sys.stderr)
        sys.exit(1)

    # refs 数量限制
    safe_refs = (refs or [])[:MAX_REFS_COUNT]

    timestamp = datetime.now(timezone.utc).isoformat()
    msg = {
        "from": from_id,
        "to": to_id,
        "type": msg_type,
        "priority": priority,
        "subject": subject,
        "body": body,
        "timestamp": timestamp,
        "refs": safe_refs
    }

    inbox_dir = os.path.join(MAILBOX_ROOT, to_id)
    os.makedirs(inbox_dir, exist_ok=True)

    # 文件名：毫秒精度防碰撞
    ts_compact = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{ts_compact}_{from_id}_{msg_type}_{priority}.json"
    filepath = os.path.join(inbox_dir, filename)

    _write_json_locked(filepath, msg)

    print(f"✅ Message sent: {from_id} → {to_id} [{msg_type}/{priority}]")
    print(f"   Subject: {subject}")
    print(f"   File: {filename}")
    return filepath


def read_inbox(to_id: str, priority_filter: str = None, type_filter: str = None):
    """读取收件箱（不删除）"""
    _validate_recipient(to_id, "recipient")

    inbox_dir = os.path.join(MAILBOX_ROOT, to_id)
    if not os.path.isdir(inbox_dir):
        print(f"📭 Inbox empty for {to_id}")
        return []

    pattern = os.path.join(inbox_dir, "*.json")
    files = sorted(glob.glob(pattern))

    messages = []
    for fp in files:
        try:
            msg = _read_json_locked(fp)
            if priority_filter and msg.get("priority") != priority_filter:
                continue
            if type_filter and msg.get("type") != type_filter:
                continue
            msg["_file"] = os.path.basename(fp)
            messages.append(msg)
        except (json.JSONDecodeError, OSError):
            continue

    if not messages:
        print(f"📭 No messages for {to_id}" + 
              (f" (filter: priority={priority_filter}, type={type_filter})" if priority_filter or type_filter else ""))
    else:
        print(f"📬 {len(messages)} message(s) for {to_id}:")
        for msg in messages:
            priority_icon = {"high": "🔴", "normal": "🟡", "low": "⚪"}.get(msg["priority"], "⚪")
            print(f"\n{priority_icon} [{msg['type']}] {msg['subject']}")
            print(f"   From: {msg['from']} | Time: {msg['timestamp']}")
            if msg.get("refs"):
                print(f"   Refs: {', '.join(msg['refs'])}")
            print(f"   {msg['body'][:200]}{'...' if len(msg['body']) > 200 else ''}")
            print(f"   File: {msg['_file']}")

    return messages


def pop_inbox(to_id: str):
    """读取并删除收件箱（已处理）— 带锁删除防 TOCTOU"""
    messages = read_inbox(to_id)
    if not messages:
        return []

    inbox_dir = os.path.join(MAILBOX_ROOT, to_id)
    deleted = 0
    for msg in messages:
        fp = os.path.join(inbox_dir, msg["_file"])
        try:
            # 先锁后删，防止并发竞态
            fd = os.open(fp, os.O_RDWR)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                os.remove(fp)  # Linux: 对已打开 fd 可 remove
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            print(f"   🗑️ Deleted: {msg['_file']}")
            deleted += 1
        except FileNotFoundError:
            print(f"   ⚠️ Already deleted: {msg['_file']}")
        except OSError as e:
            print(f"   ❌ Delete failed: {msg['_file']} ({e})")

    print(f"\n✅ Processed and removed {deleted}/{len(messages)} message(s)")
    return messages


def check_inbox(to_id: str):
    """检查未读数量"""
    _validate_recipient(to_id, "recipient")

    inbox_dir = os.path.join(MAILBOX_ROOT, to_id)
    if not os.path.isdir(inbox_dir):
        print(f"0")
        return 0

    count = len(glob.glob(os.path.join(inbox_dir, "*.json")))
    high_count = len(glob.glob(os.path.join(inbox_dir, "*_high.json")))
    print(f"{count}" + (f" ({high_count} high)" if high_count else ""))
    return count


def main():
    parser = argparse.ArgumentParser(description="Hermes Team Mailbox v2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # send
    send_p = subparsers.add_parser("send", help="Send a message")
    send_p.add_argument("--from", dest="from_id", required=True)
    send_p.add_argument("--to", required=True)
    send_p.add_argument("--type", dest="msg_type", required=True, choices=VALID_TYPES)
    send_p.add_argument("--priority", default="normal", choices=VALID_PRIORITIES)
    send_p.add_argument("--subject", required=True)
    send_p.add_argument("--body", required=True)
    send_p.add_argument("--refs", nargs="*", default=[])

    # read
    read_p = subparsers.add_parser("read", help="Read inbox")
    read_p.add_argument("--to", required=True)
    read_p.add_argument("--priority", choices=VALID_PRIORITIES)
    read_p.add_argument("--type", choices=VALID_TYPES)

    # pop
    pop_p = subparsers.add_parser("pop", help="Read and remove inbox")
    pop_p.add_argument("--to", required=True)

    # check
    check_p = subparsers.add_parser("check", help="Check unread count")
    check_p.add_argument("--to", required=True)

    args = parser.parse_args()

    if args.command == "send":
        send_message(args.from_id, args.to, args.msg_type, args.subject,
                     args.body, args.priority, args.refs)
    elif args.command == "read":
        read_inbox(args.to, args.priority, getattr(args, 'type', None))
    elif args.command == "pop":
        pop_inbox(args.to)
    elif args.command == "check":
        check_inbox(args.to)


if __name__ == "__main__":
    main()
