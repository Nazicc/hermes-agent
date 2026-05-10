---
name: songsee
description: "Use when generating spectrograms and audio feature visualizations (mel, chroma, MFCC, tempogram, etc.) from audio files via CLI. Useful for audio analysis, music production debugging, and visual documentation. NOT for: audio transcription, music generation, speech recognition, or when DAW software is more appropriate."
category: general
---

## Overview

`songsee` generates spectrograms and audio feature visualizations from audio files via CLI. It supports multiple audio formats and visualization types useful for music analysis, audio debugging, and technical documentation.

## Core Features

- **Mel spectrograms** — Most common audio visualization, shows frequency content over time
- **Chroma features** — Pitch class profiles, great for harmonic analysis
- **MFCC (Mel-Frequency Cepstral Coefficients)** — Texture, timbre, genre classification
- **Tempogram** — Rhythm, tempo patterns
- **Waveforms** — Basic amplitude over time
- **Spectral contrast** — Peak/valley differences across frequency bands
- **Tonnetz** — Harmonic relationships

## Usage

bash
# Basic mel spectrogram
songsee input.wav --output mel.png

# Multiple visualization types
songsee track.mp3 --viz mel chroma mfcc tempogram

# Custom parameters
songsee audio.flac --n_fft 2048 --hop_length 512 --n_mels 128

