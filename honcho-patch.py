#!/usr/bin/env python3
"""Honcho startup patch: fix embedding dims, disable json_mode, patch OpenAI backend for GLM, fix prompt for JSON output."""
import re

def patch_file(path, replacements, label):
    try:
        with open(path) as f:
            content = f.read()
        original = content
        for old, new in replacements:
            content = content.replace(old, new)
        if content != original:
            with open(path, 'w') as f:
                f.write(content)
            print(f"✅ Patched {label}")
        else:
            print(f"ℹ️  {label}: no changes needed")
    except FileNotFoundError:
        print(f"⚠️  {label}: file not found ({path})")

# 1. config.py: 1536 → 1024
patch_file('/app/src/config.py', [('1536', '1024')], 'config.py (dims)')

# 2. models.py: Vector(1536) → Vector(1024)
patch_file('/app/src/models.py', [('Vector(1536)', 'Vector(1024)')], 'models.py (Vector)')

# 3. deriver.py: json_mode=True → json_mode=False
patch_file('/app/src/deriver/deriver.py', [('json_mode=True', 'json_mode=False')], 'deriver.py (json_mode)')

# 4. Patch OpenAI backend: skip json_schema response_format for GLM compat
openai_path = '/app/src/llm/backends/openai.py'
try:
    with open(openai_path) as f:
        content = f.read()
    if 'GLM_COMPAT_PATCH' not in content:
        old = '''        if isinstance(response_format, type):
            params["response_format"] = response_format
            try:
                response = await self._client.chat.completions.parse(**params)'''
        new = '''        # GLM_COMPAT_PATCH: Skip response_format for models that don't support json_schema
        if isinstance(response_format, type):
            response = await self._client.chat.completions.create(**params)
            raw_content = response.choices[0].message.content or ""
            try:
                content = repair_response_model_json(raw_content, response_format, model)
                return self._normalize_response(response, content_override=content)
            except Exception:
                return self._normalize_response(response)
            # Original (disabled):
            # params["response_format"] = response_format
            # try:
            #     response = await self._client.chat.completions.parse(**params)'''
        content = content.replace(old, new)
        with open(openai_path, 'w') as f:
            f.write(content)
        print("✅ Patched openai.py (GLM compat: skip structured output)")
    else:
        print("ℹ️  openai.py already patched")
except FileNotFoundError:
    print("⚠️  openai.py not found")

# 5. Patch deriver prompt to request JSON output format
# CRITICAL: This is an f-string, so curly braces must be doubled for literal braces
prompts_path = '/app/src/deriver/prompts.py'
try:
    with open(prompts_path) as f:
        content = f.read()
    if 'RESPOND_IN_JSON' not in content:
        old = '''</messages>
"""'''
        new = '''</messages>

IMPORTANT: You MUST respond with valid JSON only. No markdown, no explanation, no prose.
Format: {{"explicit": [{{"content": "observation text"}}, ...]}}
RESPOND_IN_JSON: true
"""'''
        content = content.replace(old, new)
        with open(prompts_path, 'w') as f:
            f.write(content)
        print("✅ Patched prompts.py (JSON format instruction, escaped braces)")
    else:
        print("ℹ️  prompts.py already patched")
except FileNotFoundError:
    print("⚠️  prompts.py not found")

print("\n🚀 All patches applied. Starting Honcho...")
