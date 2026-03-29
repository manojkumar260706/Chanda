"""
step3_rhythm_pitch_mapping.py — Rhythm and pitch assignment for each syllable.

Maps each syllable's L/G classification to:
    - A duration multiplier (Laghu=1.0, Guru=2.0)
    - A svara (pitch accent) name and semitone offset

The svara assignment uses a simplified positional cycling model:
    [Anudātta, Udātta, Svarita] repeating within each pāda.

This is a conscious simplification — real Vedic svara rules are
text-dependent and accent-marked. For this POC, the cyclic approach
produces a recognizable melodic contour.

Key functions:
    - assign_duration(syllable_lg_list)   → add duration multipliers
    - assign_svara(syllable_list)         → add svara names + semitone offsets
    - build_mapping_table(syllable_lg)    → complete mapping table
"""

from config import (
    LAGHU_MULTIPLIER,
    GURU_MULTIPLIER,
    SVARA_CYCLE,
    SVARA_SEMITONE_MAP,
    DEFAULT_PADA_SIZE,
)


# ---------------------------------------------------------------------------
# Duration Assignment
# ---------------------------------------------------------------------------

def assign_duration(syllable_lg_list: list) -> list:
    """
    Map each syllable's Laghu/Guru tag to a duration multiplier.

    Laghu (L) → LAGHU_MULTIPLIER (1.0) — 1 unit of time
    Guru  (G) → GURU_MULTIPLIER  (2.0) — 2 units of time

    Args:
        syllable_lg_list: List of (syllable_str, 'L' or 'G') tuples.

    Returns:
        List of (syllable_str, 'L'/'G', duration_multiplier) tuples.
    """
    result = []
    for syllable, lg_tag in syllable_lg_list:
        if lg_tag == 'G':
            mult = GURU_MULTIPLIER
        else:
            # Default to Laghu for any tag that isn't 'G'
            mult = LAGHU_MULTIPLIER
        result.append((syllable, lg_tag, mult))
    return result


# ---------------------------------------------------------------------------
# Svara (Pitch Accent) Assignment
# ---------------------------------------------------------------------------

def assign_svara(syllable_lg_list: list, pada_size: int = DEFAULT_PADA_SIZE) -> list:
    """
    Assign svara (pitch accent) to each syllable based on position within pāda.

    The SVARA_CYCLE [Anudātta, Udātta, Svarita] repeats within each pāda.
    When we cross a pāda boundary (every `pada_size` syllables), the cycle resets.

    Example for 8-syllable pāda:
        Position: 0     1       2       3        4       5       6       7
        Svara:    Anu   Udā     Sva     Anu      Udā     Sva     Anu     Udā

    Args:
        syllable_lg_list: List of (syllable_str, 'L'/'G') tuples.
        pada_size: Number of syllables per pāda (default 8 for Anushtubh).

    Returns:
        List of (syllable_str, 'L'/'G', svara_name, semitone_offset) tuples.
    """
    result = []
    cycle_len = len(SVARA_CYCLE)

    for i, (syllable, lg_tag) in enumerate(syllable_lg_list):
        # Position within current pāda (resets every pada_size syllables)
        pos_in_pada = i % pada_size

        # Cycle through svaras within the pāda
        svara_name = SVARA_CYCLE[pos_in_pada % cycle_len]
        semitones = SVARA_SEMITONE_MAP[svara_name]

        result.append((syllable, lg_tag, svara_name, semitones))

    return result


# ---------------------------------------------------------------------------
# Combined Mapping Table
# ---------------------------------------------------------------------------

def build_mapping_table(syllable_lg_list: list, pada_size: int = DEFAULT_PADA_SIZE) -> list:
    """
    Build the complete mapping table combining duration and pitch for each syllable.

    This is the core output of Step 3 — a list of tuples that fully describe
    how each syllable should be transformed in the audio processing steps.

    Args:
        syllable_lg_list: List of (syllable_str, 'L'/'G') tuples from Step 2.
        pada_size: Syllables per pāda (default 8).

    Returns:
        List of dicts, each with:
            'syllable'        → the syllable string
            'lg'              → 'L' or 'G'
            'svara'           → svara name (Udātta / Anudātta / Svarita)
            'duration_mult'   → float duration multiplier
            'pitch_semitones' → int semitone offset for pitch shifting
    """
    # Get duration multipliers
    with_duration = assign_duration(syllable_lg_list)

    # Get svara assignments
    with_svara = assign_svara(syllable_lg_list, pada_size)

    # Merge into final table
    mapping_table = []
    for (syl_d, lg_d, dur), (syl_s, lg_s, svara, semi) in zip(with_duration, with_svara):
        mapping_table.append({
            'syllable': syl_d,
            'lg': lg_d,
            'svara': svara,
            'duration_mult': dur,
            'pitch_semitones': semi,
        })

    return mapping_table


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Step 3: Rhythm + Pitch Mapping ===\n")

    # Simulate output from Step 2 (syllable, L/G pairs)
    # Example: "को न्वस्मिन् साम्प्रतं लोके" pāda
    sample_syllable_lg = [
        ('को', 'G'), ('न्व', 'L'), ('स्मिन्', 'G'), ('सा', 'G'),
        ('म्प्र', 'G'), ('तं', 'G'), ('लो', 'G'), ('के', 'G'),
    ]

    print("Input syllable-LG pairs:")
    for syl, lg in sample_syllable_lg:
        print(f"  {syl} → {lg}")

    print("\nMapping table:")
    table = build_mapping_table(sample_syllable_lg)
    print(f"{'Syllable':<10} {'L/G':<5} {'Svara':<12} {'Duration':<10} {'Pitch (st)':<10}")
    print("-" * 50)
    for row in table:
        print(f"{row['syllable']:<10} {row['lg']:<5} {row['svara']:<12} "
              f"{row['duration_mult']:<10.1f} {row['pitch_semitones']:<10}")
