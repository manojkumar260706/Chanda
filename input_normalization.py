"""
step1_input_normalization.py — Input parsing and transliteration to Devanagari.

Accepts Sanskrit verse text in any supported scheme (IAST, ITRANS, Devanagari, etc.)
and normalizes it to Devanagari for downstream processing.

Key functions:
    - detect_script(text)            → auto-detect the input transliteration scheme
    - normalize_to_devanagari(text)  → convert to Devanagari
    - clean_verse(text)              → strip punctuation, split into pādas
"""

import re
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


# ---------------------------------------------------------------------------
# Script / Scheme Detection
# ---------------------------------------------------------------------------

def detect_script(text: str) -> str:
    """
    Heuristic detection of the input script/transliteration scheme.

    Strategy:
        1. If text contains Devanagari Unicode characters → DEVANAGARI
        2. If text contains IAST-specific diacritics (ā, ī, ū, ṛ, ṣ, ṇ, ṭ, ḍ, ś) → IAST
        3. Otherwise → assume ITRANS (ASCII-based transliteration)

    Args:
        text: Input Sanskrit verse string.

    Returns:
        sanscript constant identifying the detected scheme.
    """
    # Check for Devanagari Unicode block (U+0900 to U+097F)
    if re.search(r'[\u0900-\u097F]', text):
        return sanscript.DEVANAGARI

    # Check for IAST-specific diacritical marks
    # These characters distinguish IAST from ITRANS
    iast_markers = set('āīūṛṝḷṃḥṅñṭḍṇśṣ' + 'ĀĪŪṚṜḶṂḤṄÑṬḌṆŚṢ')
    if any(ch in iast_markers for ch in text):
        return sanscript.IAST

    # Default assumption: ITRANS (most common ASCII scheme)
    return sanscript.ITRANS


def normalize_to_devanagari(text: str, source_scheme: str = None) -> str:
    """
    Convert input text to Devanagari script.

    If source_scheme is None, auto-detects the scheme using detect_script().
    If text is already in Devanagari, returns it as-is (no double conversion).

    Args:
        text: Input Sanskrit verse string in any scheme.
        source_scheme: Optional explicit source scheme (sanscript constant).
                       If None, auto-detected.

    Returns:
        The verse text in Devanagari script.
    """
    if source_scheme is None:
        source_scheme = detect_script(text)

    # If already Devanagari, no conversion needed
    if source_scheme == sanscript.DEVANAGARI:
        return text

    # Transliterate from detected/specified scheme to Devanagari
    devanagari_text = transliterate(text, source_scheme, sanscript.DEVANAGARI)
    return devanagari_text


# ---------------------------------------------------------------------------
# Verse Cleaning and Pāda Splitting
# ---------------------------------------------------------------------------

def clean_verse(text: str) -> dict:
    """
    Clean the verse text and split into pādas (quarter-verses).

    Operations:
        - Normalize whitespace (collapse multiple spaces, strip edges)
        - Split on danda (।) and double-danda (॥) markers
        - Filter out empty segments
        - Return both the full cleaned text and the individual pādas

    Args:
        text: Devanagari verse text (may contain dandas).

    Returns:
        dict with keys:
            'full_text'  → cleaned full verse string (dandas removed)
            'padas'      → list of pāda strings (quarter-verse lines)
            'num_padas'  → number of pādas found
    """
    # Replace double-danda first (so it doesn't get split as two singles)
    # Then replace single danda — both become newline for splitting
    cleaned = text.replace('॥', '\n').replace('।', '\n')

    # Split into lines, strip whitespace, filter empties
    padas = [line.strip() for line in cleaned.split('\n') if line.strip()]

    # Reconstruct full text without dandas (space-separated pādas)
    full_text = ' '.join(padas)

    return {
        'full_text': full_text,
        'padas': padas,
        'num_padas': len(padas),
    }


# ---------------------------------------------------------------------------
# Convenience: Full Step 1 Pipeline
# ---------------------------------------------------------------------------

def process_input(text: str, source_scheme: str = None) -> dict:
    """
    Full Step 1 pipeline: detect scheme → convert to Devanagari → clean & split.

    Args:
        text: Raw input verse string in any scheme.
        source_scheme: Optional explicit source scheme.

    Returns:
        dict with keys:
            'detected_scheme' → name of the detected/used scheme
            'devanagari'      → full verse in Devanagari
            'padas'           → list of pāda strings
            'num_padas'       → count of pādas
    """
    # Detect input scheme
    scheme = source_scheme if source_scheme else detect_script(text)

    # Convert to Devanagari
    devanagari = normalize_to_devanagari(text, scheme)

    # Clean and split into pādas
    verse_data = clean_verse(devanagari)

    # Map scheme constant to human-readable name
    scheme_names = {
        sanscript.DEVANAGARI: "Devanagari",
        sanscript.IAST: "IAST",
        sanscript.ITRANS: "ITRANS",
    }
    scheme_name = scheme_names.get(scheme, str(scheme))

    return {
        'detected_scheme': scheme_name,
        'devanagari': verse_data['full_text'],
        'padas': verse_data['padas'],
        'num_padas': verse_data['num_padas'],
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Test with IAST input (Bhagavad Gita 2.47)
    iast_verse = "karmaṇyevādhikāraste mā phaleṣu kadācana"
    print("=== Step 1: Input & Normalization ===\n")
    print(f"Input (IAST): {iast_verse}")

    result = process_input(iast_verse)
    print(f"Detected scheme: {result['detected_scheme']}")
    print(f"Devanagari: {result['devanagari']}")
    print(f"Pādas ({result['num_padas']}): {result['padas']}")

    # Test with Devanagari input
    dev_verse = "को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्।\nधर्मज्ञश्च कृतज्ञश्च सत्यवाक्यो दृढव्रतः॥"
    print(f"\nInput (Devanagari): {dev_verse}")

    result2 = process_input(dev_verse)
    print(f"Detected scheme: {result2['detected_scheme']}")
    print(f"Devanagari: {result2['devanagari']}")
    print(f"Pādas ({result2['num_padas']}): {result2['padas']}")
