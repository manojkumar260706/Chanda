"""
config.py — Global configuration constants for the Chanda POC.

Central place for all tunable parameters: durations, pitch offsets,
TTS model names, file paths, etc.
"""

import os

# =============================================================================
# Project Paths
# =============================================================================
# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Output directory for generated audio files
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Default output filename
DEFAULT_OUTPUT_FILENAME = "output.wav"

# =============================================================================
# Rhythm Configuration — Laghu / Guru duration multipliers
# =============================================================================
# Laghu (light syllable) = 1 mātrā unit of duration
LAGHU_MULTIPLIER = 1.0

# Guru (heavy syllable) = 2 mātrā units of duration (twice as long)
GURU_MULTIPLIER = 2.0

# Base duration of one mātrā unit in seconds.
# This is a reference value; actual duration comes from proportional splitting
# of the TTS-generated audio, so this is used mainly for documentation.
BASE_DURATION_SECONDS = 0.2

# =============================================================================
# Pitch / Svara Configuration — Vedic pitch accent system
# =============================================================================
# Svara names
UDATTA = "Udātta"       # Raised pitch (high tone)
ANUDATTA = "Anudātta"   # Lowered pitch (low tone)
SVARITA = "Svarita"     # Neutral / falling pitch (middle tone)

# Svara → semitone offset mapping for pitch shifting
SVARA_SEMITONE_MAP = {
    UDATTA: +2,      # Raise by 2 semitones
    ANUDATTA: -2,    # Lower by 2 semitones
    SVARITA: 0,      # No pitch change
}

# Positional svara cycle applied across each pāda (quarter-verse).
# This is a simplified cyclic model; real Vedic accents are text-specific.
# The cycle repeats every 3 syllables within a pāda.
SVARA_CYCLE = [ANUDATTA, UDATTA, SVARITA]

# Default pāda size for Anushtubh meter (8 syllables per quarter-verse)
DEFAULT_PADA_SIZE = 8

# =============================================================================
# TTS Configuration — ai4bharat/indic-parler-tts
# =============================================================================
# HuggingFace model identifier (loaded via parler-tts library)
TTS_MODEL_NAME = "ai4bharat/indic-parler-tts"

# Voice description prompt — controls speaker style, clarity, pace
TTS_VOICE_DESCRIPTION = (
    "A female speaker with a calm, clear, and narrating voice. "
    "The speech is steady and measured. Very clear audio."
)

# =============================================================================
# Audio Processing Configuration
# =============================================================================
# Sample rate for audio processing (will be overridden by TTS model's native SR)
DEFAULT_SAMPLE_RATE = 22050

# Crossfade duration in milliseconds when stitching chunks (smooths boundaries)
CROSSFADE_MS = 10

# Minimum chunk length in samples to avoid processing errors on tiny slices
MIN_CHUNK_SAMPLES = 512
