import urllib.request, json, sys

endpoints = [
    ('Gateway', 8642, '/health'),
    ('SkillClaw', 30000, '/health'),
    ('OpenViking', 1934, '/health'),
    ('DeerFlow', 3000, '/api/health'),
    ('DeerFlow GW', 2026, '/api/health'),
]

for name, port, path in endpoints:
    try:
        url = f'http://127.0.0.1:{port}{path}'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read().decode()[:200]
            print(f'OK {name} (:{port}): {resp.status} - {data[:100]}')
    except Exception as e:
        print(f'FAIL {name} (:{port}): {e}')
