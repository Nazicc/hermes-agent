import urllib.request
try:
    req = urllib.request.Request('http://127.0.0.1:2026/api/health')
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(f'Status: {resp.status}')
        print(f'Body: {resp.read().decode()[:200]}')
except Exception as e:
    print(f'Error: {e}')
