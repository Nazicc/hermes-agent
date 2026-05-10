import urllib.request, json, sys

# Check SkillClaw endpoints
for path in ['/', '/health', '/v1/models', '/status', '/v1/chat/completions']:
    try:
        url = f'http://127.0.0.1:30000{path}'
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = resp.read().decode()[:200]
            print(f'OK :30000{path} -> {resp.status} {data[:100]}')
    except Exception as e:
        print(f'FAIL :30000{path} -> {e}')

# Check DeerFlow GW with auth
for path in ['/api/health', '/health', '/api/v1/health']:
    try:
        url = f'http://127.0.0.1:2026{path}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', 'Bearer test')
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read().decode()[:200]
            print(f'OK :2026{path} -> {resp.status} {data[:100]}')
    except Exception as e:
        print(f'FAIL :2026{path} -> {e}')
