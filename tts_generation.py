"""
step4_tts_generation.py — Text-to-Speech generation using ai4bharat/indic-parler-tts.

Generates raw speech audio from Devanagari text using the Indic Parler TTS model
loaded via the parler-tts HuggingFace library. Runs locally, no API keys needed.

The model is loaded once and cached at module level to avoid repeated downloads
across multiple calls (important for Streamlit's re-run behavior).

Key functions:
    - get_tts_model()                          → lazy-load and cache model + tokenizer
    - generate_tts(devanagari_text, output_path) → generate .wav from text
"""

import os
import numpy as np
import torch
import soundfile as sf
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

from config import TTS_MODEL_NAME, TTS_VOICE_DESCRIPTION, OUTPUT_DIR


# ---------------------------------------------------------------------------
# Model Caching — load once, reuse across calls
# ---------------------------------------------------------------------------

# Module-level cache for the TTS model and tokenizer
_tts_model = None
_tts_tokenizer = None
_tts_device = None


def get_tts_model():
    """
    Lazy-load the TTS model and tokenizer. Cached at module level.

    Automatically selects CUDA if available, otherwise falls back to CPU.
    First call downloads the model from HuggingFace (~3-4 GB); subsequent
    calls reuse the cached instance.

    Returns:
        Tuple of (model, tokenizer, device_string)
    """
    global _tts_model, _tts_tokenizer, _tts_device

    if _tts_model is None:
        print(f"[TTS] Loading model: {TTS_MODEL_NAME}")
        print(f"[TTS] This may take a few minutes on first run (downloading weights)...")

        # Select device: prefer CUDA GPU, fall back to CPU
        _tts_device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[TTS] Using device: {_tts_device}")

        # Load model and move to device
        _tts_model = ParlerTTSForConditionalGeneration.from_pretrained(
            TTS_MODEL_NAME
        ).to(_tts_device)

        # Load tokenizer
        _tts_tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL_NAME)

        print("[TTS] Model loaded successfully.")

    return _tts_model, _tts_tokenizer, _tts_device


# ---------------------------------------------------------------------------
# TTS Generation
# ---------------------------------------------------------------------------

def generate_tts(devanagari_text: str, output_path: str = None) -> dict:
    """
    Generate speech audio from Devanagari text using indic-parler-tts.

    The voice style is controlled by the TTS_VOICE_DESCRIPTION in config.py.
    Output is saved as a WAV file.

    Args:
        devanagari_text: Sanskrit text in Devanagari script to synthesize.
        output_path: Full path for the output .wav file.
                     If None, saves to OUTPUT_DIR/raw_tts.wav

    Returns:
        dict with keys:
            'audio_array'   → numpy array of the generated audio waveform
            'sample_rate'   → sample rate of the generated audio (int)
            'output_path'   → path where the .wav file was saved
            'duration_secs' → duration of generated audio in seconds
    """
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "raw_tts.wav")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load cached model
    model, tokenizer, device = get_tts_model()

    print(f"[TTS] Generating speech for: {devanagari_text[:80]}...")

    # Tokenize the voice description (controls speaker style)
    input_ids = tokenizer(
        TTS_VOICE_DESCRIPTION,
        return_tensors="pt"
    ).input_ids.to(device)

    # Tokenize the actual text to speak
    prompt_input_ids = tokenizer(
        devanagari_text,
        return_tensors="pt"
    ).input_ids.to(device)

    # Generate audio with no_grad for efficiency
    with torch.no_grad():
        generation = model.generate(
            input_ids=input_ids,
            prompt_input_ids=prompt_input_ids,
        )

    # Convert to numpy array (squeeze batch dimension)
    audio_array = generation.cpu().numpy().squeeze()

    # Get the model's native sample rate
    sample_rate = model.config.sampling_rate

    # Calculate duration
    duration_secs = len(audio_array) / sample_rate

    # Save to disk
    sf.write(output_path, audio_array, sample_rate)
    print(f"[TTS] Audio saved: {output_path} ({duration_secs:.2f}s, {sample_rate}Hz)")

    return {
        'audio_array': audio_array,
        'sample_rate': sample_rate,
        'output_path': output_path,
        'duration_secs': duration_secs,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Step 4: TTS Generation ===\n")

    # Test with a simple Sanskrit phrase
    test_text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
    print(f"Input text: {test_text}")

    result = generate_tts(test_text)
    print(f"\nGenerated audio:")
    print(f"  Sample rate: {result['sample_rate']} Hz")
    print(f"  Duration: {result['duration_secs']:.2f} seconds")
    print(f"  Array shape: {result['audio_array'].shape}")
    print(f"  Saved to: {result['output_path']}")
