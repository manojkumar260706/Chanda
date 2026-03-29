"""
step2_chanda_analysis.py — Meter detection and syllable-level analysis.

Uses the `chanda` library to:
    - Segment syllables from Devanagari text
    - Classify each syllable as Laghu (L) or Guru (G)
    - Identify the Sanskrit meter (Chandas) name

Key functions:
    - analyze_verse(text)       → full verse analysis (verse mode)
    - analyze_single_pada(line) → single pāda analysis
    - get_syllable_data(result) → extract structured syllable list
"""

from chanda import analyze_line, analyze_text


# ---------------------------------------------------------------------------
# Single Line / Pāda Analysis
# ---------------------------------------------------------------------------

def analyze_single_pada(line: str) -> dict:
    """
    Analyze a single pāda (quarter-verse line) for meter and syllable data.

    Uses chanda.analyze_line() with fuzzy matching enabled so that
    even slightly irregular lines can be identified.

    Args:
        line: A single line of Sanskrit text in Devanagari.

    Returns:
        dict with keys:
            'syllables'    → list of syllable strings ['को', 'न्व', ...]
            'lg'           → list of 'L'/'G' per syllable ['G', 'G', ...]
            'meter_names'  → list of identified meter names
            'gana'         → gaṇa notation string (e.g., 'ययय')
            'matra'        → total mātrā count
            'length'       → total syllable count
            'found'        → whether a meter was identified
            'syllable_lg'  → combined list of (syllable, L/G) tuples
    """
    result = analyze_line(line, fuzzy=True)

    # Extract meter names from the chanda attribute
    # result.chanda is a list of (name, details) tuples
    meter_names = []
    if result.chanda:
        meter_names = [name for name, _ in result.chanda]

    # Build the combined syllable + L/G list
    syllables = list(result.syllables) if result.syllables else []
    lg_tags = list(result.lg) if result.lg else []

    # Ensure both lists are the same length (defensive)
    min_len = min(len(syllables), len(lg_tags))
    syllable_lg = list(zip(syllables[:min_len], lg_tags[:min_len]))

    return {
        'syllables': syllables,
        'lg': lg_tags,
        'meter_names': meter_names,
        'gana': str(result.gana) if result.gana else '',
        'matra': result.matra if hasattr(result, 'matra') else 0,
        'length': result.length if hasattr(result, 'length') else len(syllables),
        'found': result.found if hasattr(result, 'found') else bool(meter_names),
        'syllable_lg': syllable_lg,
    }


# ---------------------------------------------------------------------------
# Full Verse Analysis (multi-line with verse grouping)
# ---------------------------------------------------------------------------

def analyze_verse(text: str) -> dict:
    """
    Analyze a full Sanskrit verse (typically 2-4 pādas).

    Uses chanda.analyze_text() with verse_mode=True for multi-line analysis.
    Also analyzes each pāda individually to get per-line syllable data.

    Args:
        text: Full verse text in Devanagari. Can contain dandas or newlines.

    Returns:
        dict with keys:
            'verse_meter'      → best-match meter name for the entire verse
            'pada_analyses'    → list of per-pāda analysis dicts
            'all_syllable_lg'  → combined syllable-LG list across all pādas
            'total_syllables'  → total syllable count across all pādas
    """
    # Split text into pādas by newline, danda, or double-danda
    import re
    raw_lines = re.split(r'[।॥\n]+', text)
    padas = [line.strip() for line in raw_lines if line.strip()]

    # Analyze each pāda individually for syllable-level data
    pada_analyses = []
    all_syllable_lg = []

    for pada in padas:
        analysis = analyze_single_pada(pada)
        pada_analyses.append(analysis)
        all_syllable_lg.extend(analysis['syllable_lg'])

    # Attempt verse-level meter identification
    verse_meter = _identify_verse_meter(text, pada_analyses)

    return {
        'verse_meter': verse_meter,
        'pada_analyses': pada_analyses,
        'all_syllable_lg': all_syllable_lg,
        'total_syllables': len(all_syllable_lg),
    }


def _identify_verse_meter(text: str, pada_analyses: list) -> str:
    """
    Identify the overall verse meter.

    Tries verse-level analysis first; if that doesn't yield results,
    falls back to the most common meter across individual pādas.

    Args:
        text: Full verse string.
        pada_analyses: List of per-pāda analysis dicts.

    Returns:
        Best-guess meter name string, or "Unknown" if none found.
    """
    # Try verse-level analysis via analyze_text
    try:
        text_result = analyze_text(text, verse_mode=True, fuzzy=True)
        # Check if verse-level result has identified meters
        if hasattr(text_result, 'result') and hasattr(text_result.result, 'verse'):
            for verse in text_result.result.verse:
                if verse.chanda:
                    best_meters, score = verse.chanda
                    if best_meters:
                        return ' / '.join(best_meters)
    except Exception:
        # If verse-level analysis fails, fall through to per-pāda fallback
        pass

    # Fallback: collect meter names from individual pādas
    all_meters = []
    for analysis in pada_analyses:
        all_meters.extend(analysis['meter_names'])

    if all_meters:
        # Return the most common meter name
        from collections import Counter
        most_common = Counter(all_meters).most_common(1)
        return most_common[0][0]

    return "Unknown"


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Step 2: Chanda Analysis ===\n")

    # Test verse: Ramayana opening (Anushtubh meter)
    test_verse = "को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्"
    print(f"Input: {test_verse}")

    # Single line analysis
    result = analyze_single_pada(test_verse)
    print(f"Meter: {result['meter_names']}")
    print(f"Syllables: {result['syllables']}")
    print(f"L/G pattern: {result['lg']}")
    print(f"Gaṇa: {result['gana']}")
    print(f"Mātrā count: {result['matra']}")
    print(f"Syllable-LG pairs: {result['syllable_lg']}")

    # Full verse analysis
    full_verse = "को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्।\nधर्मज्ञश्च कृतज्ञश्च सत्यवाक्यो दृढव्रतः॥"
    print(f"\nFull verse: {full_verse}")

    verse_result = analyze_verse(full_verse)
    print(f"Verse meter: {verse_result['verse_meter']}")
    print(f"Total syllables: {verse_result['total_syllables']}")
    print(f"All syllable-LG: {verse_result['all_syllable_lg']}")
    for i, pada in enumerate(verse_result['pada_analyses']):
        print(f"  Pāda {i+1}: {pada['syllables']} → {pada['lg']}")
