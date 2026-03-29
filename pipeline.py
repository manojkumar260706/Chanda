"""
pipeline.py — End-to-end orchestrator for the Chanda recitation pipeline.

Chains all 6 processing steps:
    Step 1: Input normalization (text → Devanagari)
    Step 2: Chanda analysis (syllable segmentation + L/G tagging + meter ID)
    Step 3: Rhythm + pitch mapping (duration multipliers + svara offsets)
    Step 4: TTS generation (Devanagari → raw audio via indic-parler-tts)
    Step 5: Audio alignment (proportional split → time-stretch → pitch-shift)
    Step 6: Stitch + export (concatenate → output.wav)

Key function:
    - run_pipeline(verse_text, source_scheme) → complete results dict
"""

import os
import time

from config import OUTPUT_DIR, DEFAULT_OUTPUT_FILENAME

# Import each processing module
from input_normalization import process_input
from chanda_analysis import analyze_verse
from rhythm_pitch_mapping import build_mapping_table
from tts_generation import generate_tts
from audio_alignment import process_all_chunks
from stitch_export import stitch_and_export


def run_pipeline(verse_text: str, source_scheme: str = None, output_path: str = None) -> dict:
    """
    Execute the full Chanda recitation pipeline from raw text to processed audio.

    Args:
        verse_text: Sanskrit verse in any supported scheme (IAST/ITRANS/Devanagari).
        source_scheme: Optional explicit input scheme. If None, auto-detected.
        output_path: Optional output .wav path. Defaults to output/output.wav.

    Returns:
        dict with keys:
            'input_text'       → original input text
            'detected_scheme'  → detected transliteration scheme
            'devanagari'       → normalized Devanagari text
            'padas'            → list of pāda strings
            'verse_meter'      → identified meter name
            'mapping_table'    → list of per-syllable mapping dicts
            'raw_tts_path'     → path to raw TTS audio
            'output_path'      → path to final processed audio
            'duration_secs'    → final audio duration in seconds
            'num_syllables'    → total syllable count
            'processing_times' → dict of per-step timing (seconds)
    """
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, DEFAULT_OUTPUT_FILENAME)

    timings = {}
    print("=" * 60)
    print("CHANDA RECITATION PIPELINE")
    print("=" * 60)

    # ===================================================================
    # STEP 1: Input Normalization
    # ===================================================================
    print("\n▸ Step 1: Input Normalization")
    t0 = time.time()

    input_result = process_input(verse_text, source_scheme)
    devanagari_text = input_result['devanagari']
    padas = input_result['padas']

    timings['step1_normalization'] = time.time() - t0
    print(f"  Detected scheme: {input_result['detected_scheme']}")
    print(f"  Devanagari: {devanagari_text}")
    print(f"  Pādas: {len(padas)}")

    # ===================================================================
    # STEP 2: Chanda Analysis
    # ===================================================================
    print("\n▸ Step 2: Chanda Analysis")
    t0 = time.time()

    verse_analysis = analyze_verse(devanagari_text)
    verse_meter = verse_analysis['verse_meter']
    syllable_lg = verse_analysis['all_syllable_lg']

    timings['step2_chanda_analysis'] = time.time() - t0
    print(f"  Meter: {verse_meter}")
    print(f"  Total syllables: {len(syllable_lg)}")
    print(f"  L/G pattern: {' '.join(lg for _, lg in syllable_lg)}")

    # ===================================================================
    # STEP 3: Rhythm + Pitch Mapping
    # ===================================================================
    print("\n▸ Step 3: Rhythm + Pitch Mapping")
    t0 = time.time()

    mapping_table = build_mapping_table(syllable_lg)

    timings['step3_mapping'] = time.time() - t0
    print(f"  Mapped {len(mapping_table)} syllables")
    # Print a compact summary
    for entry in mapping_table:
        print(f"    {entry['syllable']:<8} {entry['lg']} "
              f"dur={entry['duration_mult']:.1f}x "
              f"pitch={entry['pitch_semitones']:+d}st "
              f"({entry['svara']})")

    # ===================================================================
    # STEP 4: TTS Generation
    # ===================================================================
    print("\n▸ Step 4: TTS Generation")
    t0 = time.time()

    raw_tts_path = os.path.join(OUTPUT_DIR, "raw_tts.wav")
    tts_result = generate_tts(devanagari_text, raw_tts_path)
    audio_array = tts_result['audio_array']
    sample_rate = tts_result['sample_rate']

    timings['step4_tts'] = time.time() - t0
    print(f"  Raw TTS duration: {tts_result['duration_secs']:.2f}s")
    print(f"  Sample rate: {sample_rate}Hz")

    # ===================================================================
    # STEP 5: Syllable-level Audio Alignment
    # ===================================================================
    print("\n▸ Step 5: Audio Alignment")
    t0 = time.time()

    processed_chunks = process_all_chunks(audio_array, sample_rate, mapping_table)

    timings['step5_alignment'] = time.time() - t0
    print(f"  Processed {len(processed_chunks)} chunks")

    # ===================================================================
    # STEP 6: Stitch + Export
    # ===================================================================
    print("\n▸ Step 6: Stitch + Export")
    t0 = time.time()

    export_result = stitch_and_export(processed_chunks, sample_rate, output_path)

    timings['step6_export'] = time.time() - t0
    print(f"  Final audio: {export_result['duration_secs']:.2f}s")
    print(f"  Saved to: {export_result['output_path']}")

    # ===================================================================
    # Summary
    # ===================================================================
    total_time = sum(timings.values())
    timings['total'] = total_time

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print(f"  Total processing time: {total_time:.2f}s")
    print(f"  Output: {export_result['output_path']}")
    print("=" * 60)

    return {
        'input_text': verse_text,
        'detected_scheme': input_result['detected_scheme'],
        'devanagari': devanagari_text,
        'padas': padas,
        'verse_meter': verse_meter,
        'mapping_table': mapping_table,
        'raw_tts_path': raw_tts_path,
        'output_path': export_result['output_path'],
        'duration_secs': export_result['duration_secs'],
        'num_syllables': len(mapping_table),
        'processing_times': timings,
        # Raw TTS data for re-processing with modified parameters (skips TTS)
        'audio_array': audio_array,
        'sample_rate': sample_rate,
    }


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Default test verse: Ramayana opening shloka (Anushtubh meter)
    test_verse = "को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्।\nधर्मज्ञश्च कृतज्ञश्च सत्यवाक्यो दृढव्रतः॥"

    print(f"Test verse:\n{test_verse}\n")
    result = run_pipeline(test_verse)

    print(f"\n--- Final Results ---")
    print(f"Meter: {result['verse_meter']}")
    print(f"Syllables: {result['num_syllables']}")
    print(f"Output: {result['output_path']}")
    print(f"Duration: {result['duration_secs']:.2f}s")
