#!/usr/bin/env python3
"""Delete extracted UTIL methods from run.py (S1 cleanup)."""
import re

with open('gateway/run.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# 找所有类方法（indent=4）和类属性的位置
method_starts = []
for i, line in enumerate(lines):
    m = re.match(r'    (?:async )?def (\w+)\(', line)
    if m:
        method_starts.append((i, m.group(1)))

# 类属性
for i, line in enumerate(lines):
    m = re.match(r'    (_\w+)\s*=\s*', line)
    if m:
        if not any(i == s[0] for s in method_starts):
            method_starts.append((i, 'CLASS_ATTR:' + m.group(1)))

method_starts.sort(key=lambda x: x[0])

def find_block_end(start_idx):
    if start_idx + 1 < len(method_starts):
        next_start = method_starts[start_idx + 1][0]
    else:
        next_start = len(lines)
    end = next_start
    while end > start_idx + 1 and lines[end - 1].strip() == '':
        end -= 1
    return end

# 要删除的方法
targets = [
    '_has_setup_skill',
    '_VOICE_MODE_PATH',
    '_load_voice_modes',
    '_save_voice_modes',
    '_set_adapter_auto_tts_disabled',
    '_sync_voice_mode_state_to_adapter',
    '_session_key_for_source',
    '_load_background_notifications_mode',
    '_format_session_info',
    '_should_send_voice_reply',
    '_send_voice_reply',
    '_deliver_media_from_response',
    '_set_session_env',
    '_clear_session_env',
    '_get_guild_id',
]

to_delete = set()
for idx, (line_no, name) in enumerate(method_starts):
    base_name = name.replace('CLASS_ATTR:', '')
    if base_name in targets:
        start = line_no
        # 向上找注释块
        comment_start = start
        while comment_start > 0:
            prev = lines[comment_start - 1].rstrip()
            if prev.startswith('    #') or prev == '':
                comment_start -= 1
            else:
                break
        
        end = find_block_end(idx)
        print("DELETE: {} (L{}-L{}, {} lines)".format(
            name, comment_start + 1, end, end - comment_start))
        
        for i in range(comment_start, end):
            to_delete.add(i)

print()
print("Total lines to delete: {}".format(len(to_delete)))

new_lines = [line for i, line in enumerate(lines) if i not in to_delete]
with open('gateway/run.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("File written. Old: {} lines, New: {} lines, Deleted: {} lines".format(
    len(lines), len(new_lines), len(lines) - len(new_lines)))
