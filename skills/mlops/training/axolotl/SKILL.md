---
name: axolotl
description: "Use when fine-tuning LLMs with Axolotl — YAML configs, 100+ model architectures, LoRA/QLoRA/DoRA/ExLlamaV2/QLoRA fine-tuning, DPO/KTO/ORPO/GRPO/CPO training methods, multimodal support, and custom dataset preparation. NOT for: inference-only tasks (use vllm or llama-cpp), full-parameter fine-tuning without LoRA (use trl-fine-tuning), or when simpler PEFT approaches suffice."
category: general
version: 1.0.0
...
author: Orchestra Research
...
license: MIT
...
dependencies: [axolotl, torch, transformers, datasets, peft, accelerate, deepspeed]
---

# Axolotl LLM Fine-Tuning Skill

## Overview

Axolotl is a unified fine-tuning platform that wraps dozens of training methods across all major PEFT and RLHF algorithms. It abstracts away the complexity of multi-stage training pipelines and heterogeneous hardware, letting you focus on YAML configuration.

## Core Capabilities

### Supported Architectures (100+ models)
- **Causal LMs**: Llama, Mistral, Mixtral, Qwen, Yi, Gemma, Phi, Falcon, StarCoder, Mamba, etc.
- **Multimodal**: LLaVA, Phi3-V, Pixtral, etc.
- **Specialized**: Math (WizardMath, Abel), Code (StarCoder2), etc.

### Training Methods

| Method | When to Use |
|--------|-------------|
| `loqalora` / `lora` | Standard PEFT fine-tuning on limited GPU memory |
| `qloalora` / `qlora` | 4-bit quantization + LoRA for extreme memory savings |
| `dora` | Dot product Re-parameterization for better stability |
| `exlora` | ExLlamaV2 kernel integration for 4/2/1-bit per parameter |
| `adapters` | Merging multiple adapter checkpoints |

### RLHF & Alignment

| Method | Use Case |
|--------|----------|
| `dpo` | Direct Preference Optimization — no reward model needed |
| `kto` | Kahneman-Taversky Optimization — handles mixed yes/no preferences |
| `orpo` | Odds Ratio Preference Optimization — simpler than DPO with comparable results |
| `grpo` | Group Relative Preference Optimization (SimBa / GRPO variants) |
| `cpo` | Contrastive Preference Optimization |
| `sft` | Supervised Fine-Tuning — baseline instruction tuning |

## Key Workflow

### 1. Dataset Preparation

Axolotl supports many dataset formats. The most common:

yaml
# Example: chatml format
datasets:
  - path: your/dataset
    type: chatml
    chat_template: chatml


Dataset types include: `chatml`, `completion`, `multi-turn`, `sharegpt`, `alpaca`,垂类

### 2. YAML Configuration

yaml
# Minimal QLoRA example
base_model: meta-llama/Llama-3.8B-Instruct
model_type: LlamaForCausalLM

load_in_4bit: true
bf16: true
quantization_config:
  load_in_4bit: true
  bnb_4bit_use_double_quant: true
  bnb_4bit_quant_type: nf4

adapter: qlora
lora_config:
  lora_r: 128
  lora_alpha: 256
  lora_dropout: 0.05
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]

dataset_prepared_path: data/prepared

epochs: 3
learning_rate: 0.0002
micro_batch_size: 1
gradient_accumulation_steps: 16
warmup_steps: 100

eval_steps: 100
save_steps: 100
save_total_limit: 3

logging_steps: 10
fp16: false
bf16: true


### 3. Training

bash
# From pre-configured YAML
axolotl train configs/your-config.yaml

# Or from CLI-only config (no YAML file)
axolotl train \
  --base_model meta-llama/Llama-3.8B-Instruct \
  --adapter qlora \
  --dataset your/dataset \
  --epochs 3


### 4. Merging Adapters

bash
# Merge LoRA adapters into base model
axolotl merge-lora configs/your-config.yaml


## Memory & Hardware Guidance

| GPU VRAM | Recommended Method | Approx. Model Size |
|----------|-------------------|--------------------|
| 6GB | 4-bit QLoRA | up to 7B |
| 10GB | 4-bit QLoRA + gradient checkpointing | up to 13B |
| 16GB | 4-bit QLoRA or 8-bit | up to 34B |
| 24GB+ | full bf16 LoRA or DoRA | up to 70B |
| 80GB+ | full fine-tune or multi-GPU | 70B+ |

## Common Configuration Patterns

### FSDP Configuration

yaml
fsdp_version: 2
fsdp_config:
  offload_params: true
  state_dict_type: FULL_STATE_DICT
  auto_wrap_policy: TRANSFORMER_BASED_WRAP
  transformer_layer_cls_to_wrap: LlamaDecoderLayer
  reshard_after_forward: true


### Context Parallelism

The `context_parallel_size` should be a divisor of the total number of GPUs:

- With 8 GPUs and no sequence parallelism: 8 different batches processed per step
- With 8 GPUs and context_parallel_size=4: Only 2 different batches processed per step (each split across 4 GPUs)
- If your per-GPU micro_batch_size is 2, the global batch size decreases from 16 to 4

### Saving Compressed Models

yaml
save_compressed: true


Setting `save_compressed: true` enables saving models in compressed format:
- Reduces disk space usage by approximately 40%
- Maintains compatibility with vLLM for accelerated inference
- Maintains compatibility with llmcompressor for further optimization

### NCCL Tests for Performance Debugging

To validate acceptable data transfer speeds for your training job:

bash
./build/all_reduce_perf -b 8 -e 128M -f 2 -g 3


### Custom Integrations

Place your integration in any location — it doesn't need to be in the `integrations` folder as long as it's installed in a Python package in your environment. See [diff-transformer example](https://github.com/axolotl-ai-cloud/diff-transformer).

### Handling Variable Sequence Lengths

Handle both single-example and batched data:
- Single example: `sample['input_ids']` is `list[int]`
- Batched data: `sample['input_ids']` is `list[list[int]]`

python
utils.trainer.drop_long_seq(sample, sequence_len=2048, min_sequence_len=2)


## Multimodal Fine-Tuning

yaml
base_model: llava-hf/llava-1.6-7b-hf
model_type: LlavaForConditionalGeneration

image_token_crop: center
image_mean: [0.48145466, 0.4578275, 0.40821073]
image_std: [0.26862954, 0.26130258, 0.27577711]

# Image/text fine-tuning datasets
datasets:
  - path: your/mm dataset
    type:
      multi-modal columns: [images, conversations]


## Example Code Patterns

**Modal Cloud Integration:**
python
cli.cloud.modal_.ModalCloud(config, app=None)


**Running Commands in Modal:**
python
cli.cloud.modal_.run_cmd(cmd, run_folder, volumes=None)


**Custom Trainer Initialization:**
python
core.trainers.base.AxolotlTrainer(
    *_args,
    bench_data_collator=None,
    eval_data_collator=None,
    dataset_tags=None,
    **kwargs,
)


**Logging with Timing:**
python
core.trainers.base.AxolotlTrainer.log(logs, start_time=None)


**Raw Input Output Prompter:**
python
prompt_strategies.input_output.RawInputOutputPrompter()


## Troubleshooting

### CUDA OOM on multi-GPU
- Reduce `micro_batch_size` first
- Enable `gradient_checkpointing: true`
- Try `optim: adamw_bnb_8bit` instead of `adamw_torch`

### Dataset format errors
- Validate with `axolotl validate configs/your-config.yaml`
- Common issues: missing `role` field in chatml, wrong `conversation_role` capitalization

### DeepSpeed stage 2 vs 3
- Stage 2: better for single-node, less memory
- Stage 3: better for multi-node, more memory efficient

## Advanced Features

- **Multi-adapter merging**: Train multiple adapters on different datasets, merge with weighted averaging
- **Continued training**: Resume from a previous checkpoint with `--resume_from_checkpoint`
- **Special tokens**: Add custom tokens via `special_tokens` config or dataset preprocessing
- **Flash Attention**: Enabled by default on supported hardware (`--flash_attn: auto`)

## Reference Files

This skill includes comprehensive documentation in `references/`:

- **api.md** - API documentation
- **dataset-formats.md** - Dataset formats documentation
- **other.md** - Additional documentation

Use `view` to read specific reference files when detailed information is needed.
