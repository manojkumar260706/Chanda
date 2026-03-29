"""
step6_stitch_export.py — Concatenate processed audio chunks and export final WAV.

Takes the list of processed audio chunks from Step 5 and:
    1. Converts each numpy chunk to a pydub AudioSegment
    2. Applies a small crossfade between adjacent chunks to smooth boundaries
    3. Exports the final concatenated audio as a .wav file

The crossfade helps mitigate boundary artifacts (clicks/pops) that arise from
processing audio segments independently.

Key functions:
    - numpy_to_audiosegment(array, sr)      → convert numpy to pydub
    - stitch_chunks(processed_list, sr)      → concatenate with crossfade
    - export_audio(audio_segment, path)      → write to .wav file
    - stitch_and_export(processed_list, sr, path) → full Step 6 pipeline
"""

import os
import numpy as np
from pydub import AudioSegment
import io

from config import CROSSFADE_MS, OUTPUT_DIR, DEFAULT_OUTPUT_FILENAME


# ---------------------------------------------------------------------------
# Numpy ↔ Pydub Conversion
# ---------------------------------------------------------------------------

def numpy_to_audiosegment(audio_array: np.ndarray, sr: int) -> AudioSegment:
    """
    Convert a numpy audio array to a pydub AudioSegment.

    Handles conversion from float32 [-1.0, 1.0] to int16 PCM format
    that pydub expects.

    Args:
        audio_array: 1D numpy array of audio samples (float32).
        sr: Sample rate.

    Returns:
        pydub AudioSegment object.
    """
    # Ensure float32
    audio = audio_array.astype(np.float32)

    # Clip to [-1.0, 1.0] range to avoid distortion
    audio = np.clip(audio, -1.0, 1.0)

    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)

    # Create AudioSegment from raw bytes
    segment = AudioSegment(
        data=audio_int16.tobytes(),
        sample_width=2,        # 16-bit = 2 bytes
        frame_rate=sr,
        channels=1,            # Mono
    )

    return segment


# ---------------------------------------------------------------------------
# Chunk Stitching
# ---------------------------------------------------------------------------

def stitch_chunks(processed_list: list, sr: int, crossfade_ms: int = CROSSFADE_MS) -> AudioSegment:
    """
    Concatenate processed audio chunks with crossfade smoothing.

    Each chunk is converted to an AudioSegment, then appended with a small
    crossfade to reduce boundary artifacts.

    Args:
        processed_list: List of dicts from process_all_chunks(), each with
                        'processed_chunk' (numpy array).
        sr: Sample rate.
        crossfade_ms: Duration of crossfade overlap in milliseconds.
                      Set to 0 for hard concatenation.

    Returns:
        Single pydub AudioSegment of the full stitched audio.
    """
    if not processed_list:
        # Return empty audio segment
        return AudioSegment.silent(duration=0, frame_rate=sr)

    print(f"[Stitch] Combining {len(processed_list)} chunks (crossfade={crossfade_ms}ms)")

    # Convert first chunk
    combined = numpy_to_audiosegment(processed_list[0]['processed_chunk'], sr)

    # Append remaining chunks with crossfade
    for i, chunk_data in enumerate(processed_list[1:], start=2):
        segment = numpy_to_audiosegment(chunk_data['processed_chunk'], sr)

        # Only apply crossfade if both segments are long enough
        # (crossfade can't exceed the length of either segment)
        effective_crossfade = min(crossfade_ms, len(combined), len(segment))

        if effective_crossfade > 0:
            combined = combined.append(segment, crossfade=effective_crossfade)
        else:
            combined = combined + segment

    print(f"[Stitch] Final audio duration: {len(combined) / 1000:.2f}s")
    return combined


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_audio(audio_segment: AudioSegment, output_path: str) -> str:
    """
    Export a pydub AudioSegment to a .wav file.

    Args:
        audio_segment: The pydub AudioSegment to export.
        output_path: Full file path for the output .wav.

    Returns:
        The output path string (for convenience).
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Export as WAV
    audio_segment.export(output_path, format="wav")
    print(f"[Export] Saved: {output_path}")

    return output_path


# ---------------------------------------------------------------------------
# Full Step 6 Pipeline
# ---------------------------------------------------------------------------

def stitch_and_export(
    processed_list: list,
    sr: int,
    output_path: str = None,
    crossfade_ms: int = CROSSFADE_MS
) -> dict:
    """
    Full Step 6 pipeline: stitch chunks → export WAV.

    Args:
        processed_list: List of dicts from process_all_chunks().
        sr: Sample rate.
        output_path: Output .wav file path. Defaults to OUTPUT_DIR/output.wav.
        crossfade_ms: Crossfade duration in ms.

    Returns:
        dict with keys:
            'output_path'   → path to the saved .wav file
            'duration_secs' → total duration in seconds
            'num_chunks'    → number of chunks stitched
    """
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, DEFAULT_OUTPUT_FILENAME)

    # Stitch all chunks
    combined = stitch_chunks(processed_list, sr, crossfade_ms)

    # Export to WAV
    export_audio(combined, output_path)

    duration_secs = len(combined) / 1000.0  # pydub uses milliseconds

    return {
        'output_path': output_path,
        'duration_secs': duration_secs,
        'num_chunks': len(processed_list),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Step 6: Stitch + Export ===\n")

    # Create synthetic test chunks (different frequencies to hear the transitions)
    sr = 22050
    chunk_duration = 0.3  # seconds each

    freqs = [440, 523, 587, 659]  # A4, C5, D5, E5
    test_chunks = []

    for i, freq in enumerate(freqs):
        t = np.linspace(0, chunk_duration, int(sr * chunk_duration), endpoint=False)
        chunk = 0.5 * np.sin(2 * np.pi * freq * t).astype(np.float32)
        test_chunks.append({
            'processed_chunk': chunk,
            'syllable': f'syl_{i}',
            'lg': 'G' if i % 2 == 0 else 'L',
            'svara': 'Udātta',
            'duration_mult': 1.0,
            'pitch_semitones': 0,
        })

    print(f"Test: {len(test_chunks)} chunks, {chunk_duration}s each")

    result = stitch_and_export(test_chunks, sr)
    print(f"\nOutput: {result['output_path']}")
    print(f"Duration: {result['duration_secs']:.2f}s")
    print(f"Chunks stitched: {result['num_chunks']}")
