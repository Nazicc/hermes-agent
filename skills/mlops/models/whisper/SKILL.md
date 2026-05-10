---
name: whisper
description: "OpenAI Whisper for speech-to-text transcription, translation, and language identification. Use when: user wants to transcribe audio to text, translate speech to English, identify spoken languages, generate subtitles (SRT/VTT), extract word-level timestamps, or process multilingual podcasts/audio. Supports 99 languages with six model sizes (39M–1550M params). NOT for: text-to-speech, real-time streaming transcription, music lyrics extraction, or when native Whisper API/proprietary STT services are preferred."
category: general
---

## Core Capabilities

- **Transcription**: Audio → text in the same language (`task: transcribe`)
- **Translation**: Audio → English text (`task: translate`)
- **Language ID**: Detect dominant language without full transcription
- **Subtitle generation**: SRT, VTT, TXT, JSON output formats
- **Word-level timestamps**: Optional extraction for precise alignment

## When to Use Whisper

**Use when:**
- Speech-to-text transcription (99 languages)
- Podcast/video transcription
- Meeting notes automation
- Translation to English (from any language)
- Noisy audio transcription
- Multilingual audio processing
- Subtitle generation (SRT/VTT)
- Word-level timestamp extraction

**Use alternatives instead:**
- **AssemblyAI**: Managed API, speaker diarization
- **Deepgram**: Real-time streaming ASR
- **Google Speech-to-Text**: Cloud-based

## Installation

bash
# Requires Python 3.8-3.11
pip install -U openai-whisper

# Requires ffmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: choco install ffmpeg


## Supported Formats

MP3, WAV, FLAC, OGG, M4A, WebM. Long audio files automatically chunked.

## Model Selection

| Model  | Parameters | VRAM   | Speed (GPU) | Best for                        |
|--------|------------|--------|-------------|---------------------------------|
| tiny   | 39M        | ~1 GB  | ~32x        | Testing, quick drafts           |
| base   | 74M        | ~1 GB  | ~16x        | General use, prototyping        |
| small  | 244M       | ~2 GB  | ~6x         | Higher accuracy                 |
| medium | 769M       | ~5 GB  | ~2x         | Difficult accents, noise        |
| large  | 1550M      | ~10 GB | 1x          | Best accuracy, non-English      |
| turbo  | 809M       | ~6 GB  | ~8x         | Fast + accurate (v3 model)      |

**Recommendation**: `turbo` for best speed/quality, `medium` for general use, `large` for non-English or difficult audio.

## Python API

python
import whisper

model = whisper.load_model("base")

# Transcription (auto-detect language)
result = model.transcribe("audio.mp3")
print(result["text"])

# Specify language (faster)
result = model.transcribe("audio.mp3", language="en")

# Translation to English
result = model.transcribe("spanish.mp3", task="translate")

# Improve accuracy with context
result = model.transcribe(
    "audio.mp3",
    initial_prompt="This is a technical podcast about machine learning."
)

# Word-level timestamps
result = model.transcribe("audio.mp3", word_timestamps=True)

# Temperature fallback
result = model.transcribe("audio.mp3", temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0))

# Access segments
for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}")


### Language Detection

python
# Detect language only (faster, no full transcription)
result = model.transcribe("unknown_lang.mp3", language=None)
print(f"Detected: {result['language']}")  # e.g., "ja", "es", "fr"

# Then transcribe with detected language for best results
result = model.transcribe("unknown_lang.mp3", language=result["language"])


## Command Line Usage

bash
# Basic transcription
whisper audio.mp3 --model large

# Specify language and model
whisper audio.mp3 --model medium --language en

# Translation to English
whisper audio.mp3 --task translate

# Output formats
whisper audio.mp3 --output_format srt   # Subtitles
whisper audio.mp3 --output_format vtt   # WebVTT
whisper audio.mp3 --output_format txt    # Plain text
whisper audio.mp3 --output_format json   # JSON with timestamps

# Word-level timestamps
whisper audio.mp3 --word_timestamps True

# Beam search + temperature sampling
whisper audio.mp3 --model large --beam_size 5 --best_of 5


### CLI Options

| Flag               | Description                                      |
|--------------------|--------------------------------------------------|
| `--model`          | Model size: tiny/base/small/medium/large/turbo   |
| `--language`       | Language code (e.g., en, fr, de, zh) or auto    |
| `--task`           | `transcribe` (default) or `translate`            |
| `--output_format`  | Output format: srt/vtt/txt/json                  |
| `--word_timestamps`| Include word-level timestamps                    |
| `--fp16`           | Use FP16 acceleration (default on GPU)           |

## GPU Acceleration

python
# Automatically uses GPU if available
model = whisper.load_model("turbo")

# Force CPU
model = whisper.load_model("turbo", device="cpu")

# Force GPU
model = whisper.load_model("turbo", device="cuda")


10-20× faster on GPU. Real-time factors: tiny ~0.32 CPU / ~0.01 GPU; large ~1.0 CPU / ~0.05 GPU.

## Output Formats

| Format | Use case                          | Contains                |
|--------|-----------------------------------|-------------------------|
| `txt`  | Plain transcript, no timestamps   | Text only               |
| `vtt`  | Web captions, video players        | Timestamps + text       |
| `srt`  | Video subtitles, editors           | Sequential timestamps   |
| `json` | Processing, analysis               | Full metadata           |

## Batch Processing

python
import os

audio_files = ["file1.mp3", "file2.mp3", "file3.mp3"]

for audio_file in audio_files:
    print(f"Transcribing {audio_file}...")
    result = model.transcribe(audio_file)
    
    output_file = audio_file.replace(".mp3", ".txt")
    with open(output_file, "w") as f:
        f.write(result["text"])


## Real-Time Transcription

For streaming audio, use faster-whisper (4× faster):

bash
pip install faster-whisper


python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cuda", compute_type="float16")
segments, info = model.transcribe("audio.mp3", beam_size=5)

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")


## Integration

### Extract audio from video

bash
ffmpeg -i video.mp4 -vn -acodec pcm_s16le audio.wav
whisper audio.wav


### With LangChain

python
from langchain.document_loaders import WhisperTranscriptionLoader

loader = WhisperTranscriptionLoader(file_path="audio.mp3")
docs = loader.load()


## Troubleshooting

| Issue                        | Solution                                              |
|------------------------------|-------------------------------------------------------|
| Slow transcription           | Use smaller model or enable GPU/FP16                  |
| Poor accuracy                | Use `medium` or `large` model; ensure clear audio     |
| Wrong language               | Specify `--language` explicitly or use `auto`         |
| CUDA out of memory           | Use smaller model or batch with `chunk_length`        |
| CPU very slow                | Use `int8` quantization or `turbo` model              |
| MPS (Apple Silicon) fp16     | Use `dtype=torch.float32` on MPS devices              |
| No timestamps in output      | Use `word_timestamps=True` and `--word_timestamps true`|
| Audio has music              | Music transcribed as humming/singing, not filtered    |
| CUDA not available           | Falls back to CPU (significantly slower)              |

## Best Practices

1. **Use turbo/medium model** - Best speed/quality balance
2. **Specify language** - Faster than auto-detect
3. **Add initial prompt** - Improves technical terms, proper nouns
4. **Use GPU** - 10-20× faster
5. **Batch process** - More efficient for multiple files
6. **Split long audio** - <30 min chunks for best accuracy
7. **Check language support** - Quality varies by language
8. **Use faster-whisper** - 4× faster for real-time needs
9. **Monitor VRAM** - Scale model size to hardware
10. **Convert to WAV** - Better compatibility

## Limitations

1. **Hallucinations** - May repeat or invent text on low-quality audio
2. **Long-form accuracy** - Degrades on >30 min audio
3. **Speaker identification** - No diarization (use AssemblyAI)
4. **Accents** - Quality varies by accent
5. **Background noise** - Can affect accuracy
6. **Real-time latency** - Not suitable for live captioning (use Deepgram)
7. **Translation** - Only translates TO English, not from English

## Resources

- **GitHub**: https://github.com/openai/whisper ⭐ 72,900+
- **Paper**: https://arxiv.org/abs/2212.04356
- **Model cache**: `~/.cache/whisper/`
- **Available on**: Linux, macOS (MPS), Windows (CUDA)
