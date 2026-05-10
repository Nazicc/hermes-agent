import urllib.request, json

# Test the gateway health endpoint
try:
    req = urllib.request.Request('http://127.0.0.1:8642/health')
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(f'Health: {resp.status} - {resp.read().decode()[:200]}')
except Exception as e:
    print(f'Health check: {e}')

# Test the gateway models endpoint
try:
    req = urllib.request.Request('http://127.0.0.1:8642/v1/models')
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print(f'Models: {resp.status} - {json.dumps(data, indent=2)[:200]}')
except Exception as e:
    print(f'Models: {e}')
