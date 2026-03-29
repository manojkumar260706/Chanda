"""
step5_audio_alignment.py — Syllable-level audio alignment and transformation.

Takes the raw TTS audio and the rhythm/pitch mapping table, then:
    1. Splits the audio proportionally by duration weight (not forced-alignment)
    2. Applies time-stretching to each chunk based on duration multiplier
    3. Applies pitch-shifting to each chunk based on svara semitone offset

IMPORTANT DESIGN NOTE:
    The syllable-audio split is intentionally approximate. We divide the total
    audio proportionally by the sum of duration weights. This means syllable
    boundaries won't be phonetically precise — this is an accepted trade-off
    for a hackathon POC. True forced-alignment (e.g., via Montreal Forced Aligner)
    would be a future improvement.

Key functions:
    - split_audio_proportional(audio, sr, mapping_table) → per-syllable chunks
    - process_chunk(chunk, sr, duration_mult, pitch_semitones) → transformed chunk
    - process_all_chunks(audio, sr, mapping_table) → list of processed chunks
"""

import numpy as np
import librosa

from config import MIN_CHUNK_SAMPLES


# ---------------------------------------------------------------------------
# Proportional Audio Splitting
# ---------------------------------------------------------------------------

def split_audio_proportional(audio_array: np.ndarray, sr: int, mapping_table: list) -> list:
    """
    Split audio into per-syllable chunks proportional to duration weights.

    Each syllable gets a share of the total audio proportional to its
    duration multiplier (L=1.0, G=2.0). This is a simple, approximate
    alignment strategy.

    Example: If we have syllables with weights [1, 2, 1, 2] (total=6),
    the first syllable gets 1/6 of the audio, second gets 2/6, etc.

    Args:
        audio_array: Raw audio as a 1D numpy array.
        sr: Sample rate of the audio.
        mapping_table: List of dicts from build_mapping_table(), each with
                       'duration_mult' key.

    Returns:
        List of dicts, each with:
            'chunk'           → numpy array of the audio segment
            'syllable'        → syllable string
            'lg'              → 'L' or 'G'
            'svara'           → svara name
            'duration_mult'   → float multiplier
            'pitch_semitones' → int semitone offset
            'start_sample'    → start index in original audio
            'end_sample'      → end index in original audio
    """
    total_samples = len(audio_array)

    # Calculate total duration weight
    total_weight = sum(entry['duration_mult'] for entry in mapping_table)

    if total_weight == 0:
        # Edge case: no syllables or all zero weights
        return []

    # Calculate sample boundaries for each syllable
    chunks = []
    current_sample = 0

    for i, entry in enumerate(mapping_table):
        # Proportion of audio this syllable gets
        proportion = entry['duration_mult'] / total_weight

        # Calculate number of samples for this chunk
        if i == len(mapping_table) - 1:
            # Last chunk gets all remaining samples (avoids rounding errors)
            chunk_samples = total_samples - current_sample
        else:
            chunk_samples = int(round(proportion * total_samples))

        # Extract the audio chunk
        start = current_sample
        end = min(current_sample + chunk_samples, total_samples)
        chunk = audio_array[start:end]

        chunks.append({
            'chunk': chunk,
            'syllable': entry['syllable'],
            'lg': entry['lg'],
            'svara': entry['svara'],
            'duration_mult': entry['duration_mult'],
            'pitch_semitones': entry['pitch_semitones'],
            'start_sample': start,
            'end_sample': end,
        })

        current_sample = end

    return chunks


# ---------------------------------------------------------------------------
# Per-Chunk Audio Processing
# ---------------------------------------------------------------------------

def process_chunk(chunk: np.ndarray, sr: int, duration_mult: float, pitch_semitones: int) -> np.ndarray:
    """
    Apply time-stretching and pitch-shifting to a single audio chunk.

    Time stretch logic:
        - duration_mult = 2.0 means "this syllable should be 2x longer"
        - librosa.effects.time_stretch(rate) where rate < 1 slows down
        - So rate = 1.0 / duration_mult (2.0 → rate=0.5 → half speed → twice duration)
        - For Laghu (1.0): rate = 1.0 (no change)
        - For Guru  (2.0): rate = 0.5 (doubled duration)

    Pitch shift logic:
        - Udātta (+2 semitones): raises pitch
        - Anudātta (-2 semitones): lowers pitch
        - Svarita (0 semitones): no change

    Args:
        chunk: Audio segment as a 1D numpy array.
        sr: Sample rate.
        duration_mult: Duration multiplier (1.0 for Laghu, 2.0 for Guru).
        pitch_semitones: Semitone offset for pitch shifting.

    Returns:
        Processed audio chunk as a 1D numpy float32 array.
    """
    # Guard against empty or too-small chunks
    if len(chunk) < MIN_CHUNK_SAMPLES:
        # Return the chunk as-is if it's too small to process meaningfully
        return chunk.astype(np.float32)

    processed = chunk.astype(np.float32)

    # --- Time Stretching ---
    # Only stretch if multiplier differs from 1.0 (avoid unnecessary processing)
    if abs(duration_mult - 1.0) > 0.01:
        # rate = 1/mult → mult=2.0 gives rate=0.5 (slower = longer)
        stretch_rate = 1.0 / duration_mult

        # Clamp rate to avoid extreme values that cause artifacts
        stretch_rate = max(0.25, min(stretch_rate, 4.0))

        try:
            processed = librosa.effects.time_stretch(processed, rate=stretch_rate)
        except Exception as e:
            print(f"[Audio] Warning: time_stretch failed for chunk, skipping. Error: {e}")

    # --- Pitch Shifting ---
    # Only shift if semitones != 0
    if pitch_semitones != 0:
        try:
            processed = librosa.effects.pitch_shift(
                processed, sr=sr, n_steps=float(pitch_semitones)
            )
        except Exception as e:
            print(f"[Audio] Warning: pitch_shift failed for chunk, skipping. Error: {e}")

    return processed


# ---------------------------------------------------------------------------
# Process All Chunks
# ---------------------------------------------------------------------------

def process_all_chunks(audio_array: np.ndarray, sr: int, mapping_table: list) -> list:
    """
    Full Step 5 pipeline: split audio → process each chunk → return list.

    Args:
        audio_array: Raw TTS audio as a 1D numpy array.
        sr: Sample rate.
        mapping_table: List of dicts from build_mapping_table().

    Returns:
        List of dicts, each with:
            'processed_chunk' → numpy array of the transformed audio
            'syllable'        → syllable string
            'lg'              → 'L' or 'G'
            'svara'           → svara name
            'duration_mult'   → float multiplier
            'pitch_semitones' → int semitone offset
    """
    # Step 1: Split audio proportionally
    chunks = split_audio_proportional(audio_array, sr, mapping_table)

    # Step 2: Process each chunk
    processed_list = []
    total = len(chunks)

    for i, chunk_data in enumerate(chunks):
        syl = chunk_data['syllable']
        lg = chunk_data['lg']
        dur = chunk_data['duration_mult']
        pitch = chunk_data['pitch_semitones']

        print(f"[Audio] Processing chunk {i+1}/{total}: "
              f"'{syl}' ({lg}) dur={dur:.1f}x pitch={pitch:+d}st")

        # Apply time-stretch and pitch-shift
        processed = process_chunk(
            chunk_data['chunk'], sr,
            chunk_data['duration_mult'],
            chunk_data['pitch_semitones']
        )

        processed_list.append({
            'processed_chunk': processed,
            'syllable': syl,
            'lg': lg,
            'svara': chunk_data['svara'],
            'duration_mult': dur,
            'pitch_semitones': pitch,
        })

    return processed_list


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Step 5: Audio Alignment ===\n")

    # Create a synthetic test signal (1 second of 440Hz sine wave)
    sr = 22050
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    test_audio = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

    # Simulate a simple mapping table (4 syllables)
    test_mapping = [
        {'syllable': 'a', 'lg': 'L', 'svara': 'Anudātta', 'duration_mult': 1.0, 'pitch_semitones': -2},
        {'syllable': 'b', 'lg': 'G', 'svara': 'Udātta', 'duration_mult': 2.0, 'pitch_semitones': +2},
        {'syllable': 'c', 'lg': 'L', 'svara': 'Svarita', 'duration_mult': 1.0, 'pitch_semitones': 0},
        {'syllable': 'd', 'lg': 'G', 'svara': 'Anudātta', 'duration_mult': 2.0, 'pitch_semitones': -2},
    ]

    print(f"Test audio: {len(test_audio)} samples at {sr}Hz ({duration}s)")
    print(f"Mapping table: {len(test_mapping)} syllables")

    results = process_all_chunks(test_audio, sr, test_mapping)

    print(f"\nProcessed {len(results)} chunks:")
    for r in results:
        chunk_len = len(r['processed_chunk'])
        chunk_dur = chunk_len / sr
        print(f"  '{r['syllable']}' ({r['lg']}) → {chunk_len} samples ({chunk_dur:.3f}s)")
