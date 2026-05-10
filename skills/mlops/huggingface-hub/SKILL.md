---
name: huggingface-hub
description: "Use when downloading, uploading, searching, or managing Hugging Face models, datasets, or Spaces — or when managing HF repos, querying datasets with SQL, deploying inference endpoints, or managing buckets. Works with the `hf` CLI and `huggingface_hub` Python package. NOT for: general file downloads from arbitrary URLs, non-HuggingFace model hosting, model training/fine-tuning, running local inference with llama.cpp/vllm (use those skills instead), or when the native HuggingFace SDK (Python) is more convenient than the CLI."
category: general
---

## Install

bash
pip install huggingface_hub
# or
brew install huggingface-hub  # macOS

# Verify
hf --version


## Auth

bash
# Login (interactive — opens browser for token)
hf login

# Or set token directly
huggingface-cli login
# → Enter your HF token (from https://huggingface.co/settings/tokens)

# Read token from env (recommended for non-interactive use)
export HF_TOKEN=hf_xxxxx


## CLI (`hf`)

### Download
bash
# Download a model (all files)
hf download meta-llama/Llama-3.1-8B

# Download specific files
hf download bigcode/starcoder2-3b --filename config.json
hf download meta-llama/Llama-2-7b --include "*.safetensors"

# Download to a specific directory
hf download mistralai/Mistral-7B-v0.3 --local-dir ./models/mistral

# Download a dataset
hf download datasets wikitext --save-history

# Full directory via snapshot-download
hf hub snapshot-download <repo_id> [--local-dir <path>]


### Upload
bash
# Upload a file
hf upload username/my-model ./pytorch_model.bin --message "initial upload"

# Upload folder (handles multipart automatically)
hf upload my-org/my-model ./local_folder --message "initial upload"

# Upload with specific repo type
hf upload username/my-dataset ./data/ --repo-type dataset


### Search models/datasets
bash
hf search models --type text-classification
hf search datasets emoji
hf search models "text-classification" --limit 5
hf search datasets "chinese" --limit 5
hf hub search "text-classification" --author "distilbert"


### Manage repos
bash
hf repo create username/my-model --type model
hf repo ls
hf ls username/model-name


### Spaces & Inference Endpoints
bash
# Spaces
hf space create username/my-space --sdk streamlit
hf space replica username/my-space

# Inference endpoints (requires Pro+ subscription)
hf endpoint create --compute gpu --repo-id my-org/my-model
hf endpoints create --repo-id meta-llama/Llama-3-8B-Instruct

# Or via REST API
curl -X POST "https://api.endpoints.huggingface.cloud/v2/endpoint" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-2-7b-hf", "compute": {"accelerator": "gpu", "instanceSize": "medium"}}'


## Python API

python
from huggingface_hub import (
    snapshot_download, upload_folder, upload_file,
    HfApi, list_models, list_datasets
)
from datasets import load_dataset

api = HfApi()  # reads HF_TOKEN from env by default

# Upload file
api.upload_file(
    path_or_fileobj="./config.json",
    path_in_repo="config.json",
    repo_id="username/my-model",
    repo_type="model",
)

# Upload folder
api.upload_folder(
    folder_path="./outputs",
    repo_id="my-org/my-model",
    repo_type="model",
)

# Download model snapshot (all files, cached)
model_dir = snapshot_download("meta-llama/Llama-3.1-8B")
print(model_dir)  # ~/.cache/huggingface/hub/models--meta-llama--Llama-3.1-8B

# Download with token (private/gated models)
model_dir = snapshot_download(
    repo_id="meta-llama/Llama-2-7b-hf",
    cache_dir="./models",
    token=os.getenv("HF_TOKEN")
)

# Load model directly (downloads if needed)
from transformers import AutoModel
model = AutoModel.from_pretrained("meta-llama/Llama-2-7b-hf", token=os.getenv("HF_TOKEN"))

# Search models
results = api.list_models(task="text-classification", sort="downloads", direction=-1, limit=5)
for model in results:
    print(model.id, model.downloads)

# Load dataset (standard)
ds = load_dataset("philschmid/gpt-3.5-books", split="train")

# Load dataset (streaming for large datasets)
ds = load_dataset("philschmid/gpt-3.5-books", streaming=True, split="train")

# Dataset with SQL
ds = load_dataset("hf://datasets/lamini/lamini-docs", split="train")


## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_TOKEN` | `~/.cache/huggingface/token` | Auth token for private repos |
| `HF_HOME` | `~/.cache/huggingface/` | Cache location |
| `HF_ENDPOINT` | `https://huggingface.co` | Override for enterprise/proxy |
| `HF_HUB_ENABLE_HF_TRANSFER` | `0` | Set to `1` for faster transfers |

**China region mirror:** `HF_ENDPOINT=https://hf-mirror.com`

## Decision Tree

1. **What is the target?** Model, dataset, Space, or repo?
2. **Is it public or private?** Public → no token needed. Private/gated → requires `HF_TOKEN`.
3. **Python or CLI?** Python (`huggingface_hub`) for scripts; CLI (`hf`) for quick one-liners.
4. **For downloads:**
   - Quick load: `from_pretrained()` or `load_dataset()`
   - Full directory: `snapshot_download()` or `hf hub snapshot-download`
   - Single file: `hf hub download <model>/<file>`
5. **For uploads:** Use `upload_folder()` or `hf upload` — requires `HF_TOKEN` with write permission.
6. **For search:** Use `list_models()` / `list_datasets()` with filters, or `hf search`.
7. **For dataset SQL:** Use `hfql` CLI or `load_dataset("hf://datasets/<repo_id>", sql=...)`.
8. **For large datasets:** Use streaming (`load_dataset(..., streaming=True)`).

## Edge Cases

| Situation | Solution |
|-----------|----------|
| Large model (50GB+) | Use `hf download --resume`; check disk space first |
| Gated model (Llama, StarCoder, etc.) | Set `HF_TOKEN`; run `hf login` first; accept terms at huggingface.co |
| Rate limiting | Set `HF_ENDPOINT` to a mirror; add `HF_HUB_ENABLE_HF_TRANSFER=1` |
| Network timeout | Use `--local-dir-use-symlinks False`; retry |
| Network interruption during download | Use `resume_download=True` in `snapshot_download()` or `hf download --resume` |
| Enterprise HF (hf.co/moon-enterprise) | Set `HF_ENDPOINT` env var to your enterprise URL |
| China region SSL | Use `HF_ENDPOINT=https://hf-mirror.com` |
| Partial download | Use `--resume` to continue; delete incomplete file first |
| Duplicate downloads | `hf download` is idempotent; `snapshot_download` skips if cache exists |
| Upload conflicts | Use `--create` flag or specify `repo_type` to avoid overwrite errors |
| Very large models/datasets | Use streaming (`load_dataset(..., streaming=True)`) or `hf_hub_download` for individual files |
| Model not loading (RAM/VRAM) | Use `from_pretrained(..., low_cpu_mem_usage=True)` or `device_map="auto"` |
| `huggingface_hub` not installed | `pip install huggingface_hub` — same package provides CLI |

## Quick Reference

| Operation | CLI | Python |
|-----------|-----|--------|
| Search models | `hf search models <query>` | `list_models(search=...)` |
| Search datasets | `hf search datasets <query>` | `list_datasets(search=...)` |
| Download model | `hf download <repo_id>` | `snapshot_download()` |
| Upload file | `hf upload <repo_id> <file>` | `api.upload_file()` |
| Upload folder | `hf upload <repo_id> ./folder` | `api.upload_folder()` |
| Create repo | `hf repo create <name> --type <type>` | `api.create_repo()` |
| List repos | `hf ls` | `api.list_models()` / `list_datasets()` |
| Download dataset | `hf download datasets/<id>` | `load_dataset()` |
| Login | `hf login` | — |

## Health Check

bash
# Verify hf CLI
hf --version

# Verify auth
hf whoami

# Verify Python package
python3 -c "import huggingface_hub; print(huggingface_hub.__version__)"

# Check token is readable
cat ~/.cache/huggingface/token 2>/dev/null || echo "No token cached"

