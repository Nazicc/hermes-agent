import urllib.request, json

# Test SkillClaw models endpoint
try:
    req = urllib.request.Request('http://127.0.0.1:30000/v1/models')
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        models = [m['id'] for m in data.get('data', [])]
        print(f'SkillClaw Models: {resp.status}')
        for m in models[:10]:
            print(f'  - {m}')
        if len(models) > 10:
            print(f'  ... and {len(models) - 10} more')
except Exception as e:
    print(f'SkillClaw Models: {e}')
