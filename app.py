"""
app.py — Streamlit UI for the Chanda Recitation System.

Provides a web interface for:
    - Entering Sanskrit verse text (any script)
    - Viewing the detected meter and syllable analysis table
    - Playing and downloading the generated recitation audio

Run with: streamlit run app.py
"""

import os
import streamlit as st
import pandas as pd
import time

from config import OUTPUT_DIR
from pipeline import run_pipeline


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Chanda — Sanskrit Recitation",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Custom CSS for a polished look
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0;
        font-family: 'Georgia', serif;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-top: -10px;
        margin-bottom: 30px;
        font-style: italic;
    }

    /* Meter badge */
    .meter-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 8px 20px;
        border-radius: 25px;
        font-size: 1.3rem;
        font-weight: 700;
        display: inline-block;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
    }

    /* Devanagari verse display */
    .verse-display {
        background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
        border-left: 4px solid #764ba2;
        padding: 20px;
        border-radius: 0 12px 12px 0;
        font-size: 1.4rem;
        font-family: 'Noto Sans Devanagari', 'Mangal', serif;
        line-height: 2;
        color: #333;
        margin: 15px 0;
    }

    /* Info cards */
    .info-card {
        background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
        padding: 15px 20px;
        border-radius: 12px;
        margin: 8px 0;
        color: #333;
    }

    /* Sidebar styling */
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #764ba2;
        border-bottom: 2px solid #764ba2;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }

    /* Status boxes */
    .status-processing {
        background: #fff3cd;
        border: 1px solid #ffc107;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
    }
    .status-done {
        background: #d4edda;
        border: 1px solid #28a745;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — Explanatory content
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🕉️ About Chanda")
    st.markdown("""
    **Chanda** (छन्द) refers to the metrical system governing Sanskrit poetry.
    This tool analyzes a verse's meter and generates a recitation where:
    """)

    st.markdown("### 📐 Laghu & Guru")
    st.markdown("""
    - **Laghu (L)** — Light syllable, short duration (1 unit)
    - **Guru (G)** — Heavy syllable, long duration (2 units)

    A Guru syllable takes **twice as long** to speak as a Laghu.
    """)

    st.markdown("### 🎵 Svara (Pitch Accents)")
    st.markdown("""
    Classical recitation uses three pitch levels:
    - **Udātta** — Raised pitch (+2 semitones)
    - **Anudātta** — Lowered pitch (-2 semitones)
    - **Svarita** — Neutral pitch (no change)
    """)

    st.markdown("### 📏 Anushtubh Meter")
    st.markdown("""
    The most common Sanskrit meter (used in Bhagavad Gita, Ramayana).
    - 4 pādas (quarter-verses) per verse
    - 8 syllables per pāda
    - 32 syllables total per verse
    """)

    st.divider()
    st.markdown("##### 🛠️ Tech Stack")
    st.markdown("""
    - `indic-transliteration` — Script conversion
    - `chanda` — Meter analysis
    - `indic-parler-tts` — Speech synthesis
    - `librosa` — Audio processing
    - `pydub` — Audio stitching
    """)


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------

# Title
st.markdown('<h1 class="main-title">🕉️ Chanda</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Melodic Constrained Sanskrit Recitation System</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Input Section
# ---------------------------------------------------------------------------

st.markdown("### 📝 Enter Sanskrit Verse")

col_input, col_options = st.columns([3, 1])

with col_input:
    # Default example: Ramayana opening (Anushtubh)
    default_verse = "को न्वस्मिन् साम्प्रतं लोके गुणवान् कश्च वीर्यवान्।\nधर्मज्ञश्च कृतज्ञश्च सत्यवाक्यो दृढव्रतः॥"

    verse_input = st.text_area(
        "Verse text (Devanagari, IAST, or ITRANS)",
        value=default_verse,
        height=120,
        placeholder="Enter a Sanskrit verse here...",
        key="verse_input",
    )

with col_options:
    scheme_option = st.selectbox(
        "Input format",
        options=["Auto-detect", "Devanagari", "IAST", "ITRANS"],
        index=0,
        key="scheme_select",
    )

    # Map selectbox choice to sanscript constants
    from indic_transliteration import sanscript
    scheme_map = {
        "Auto-detect": None,
        "Devanagari": sanscript.DEVANAGARI,
        "IAST": sanscript.IAST,
        "ITRANS": sanscript.ITRANS,
    }
    selected_scheme = scheme_map[scheme_option]

# Generate button
generate_clicked = st.button(
    "🎙️ Generate Recitation",
    type="primary",
    use_container_width=True,
    key="generate_btn",
)

st.divider()

# ---------------------------------------------------------------------------
# Processing and Results
# ---------------------------------------------------------------------------

if generate_clicked and verse_input.strip():
    # Run the full pipeline with a progress indicator
    with st.spinner("🔄 Processing verse... This may take a minute on first run (model download)."):
        try:
            result = run_pipeline(
                verse_input.strip(),
                source_scheme=selected_scheme,
            )

            # Cache raw TTS audio separately — numpy arrays in dedicated keys
            # so the regenerate flow can access them without re-running TTS
            st.session_state['tts_audio_array'] = result.pop('audio_array')
            st.session_state['tts_sample_rate'] = result.pop('sample_rate')

            # Store the rest of the result for display
            st.session_state['result'] = result
            st.session_state['has_result'] = True

        except Exception as e:
            st.error(f"❌ Pipeline error: {str(e)}")
            st.exception(e)
            st.session_state['has_result'] = False

elif generate_clicked and not verse_input.strip():
    st.warning("⚠️ Please enter a Sanskrit verse before generating.")


# ---------------------------------------------------------------------------
# Display Results (from session state)
# ---------------------------------------------------------------------------

if st.session_state.get('has_result', False):
    result = st.session_state['result']

    # --- Detected Meter ---
    st.markdown("### 📏 Detected Meter")
    st.markdown(f'<span class="meter-badge">{result["verse_meter"]}</span>', unsafe_allow_html=True)

    # --- Devanagari Display ---
    st.markdown("### 📜 Normalized Verse (Devanagari)")
    st.markdown(f'<div class="verse-display">{result["devanagari"]}</div>', unsafe_allow_html=True)

    # --- Info Row ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Input Format", result['detected_scheme'])
    with col2:
        st.metric("Total Syllables", result['num_syllables'])
    with col3:
        st.metric("Pādas", len(result['padas']))

    # --- Editable Syllable Analysis Table ---
    st.markdown("### 📊 Syllable Analysis — Editable")
    st.caption("Adjust Duration and Pitch per syllable, then click **Regenerate Audio** below.")

    mapping_table = result['mapping_table']
    num_syllables = len(mapping_table)

    # Initialize editable values in session state on first load
    if 'edited_durations' not in st.session_state or len(st.session_state['edited_durations']) != num_syllables:
        st.session_state['edited_durations'] = [entry['duration_mult'] for entry in mapping_table]
        st.session_state['edited_pitches'] = [entry['pitch_semitones'] for entry in mapping_table]

    # Render the editable table as columns of widgets
    # Header row
    hdr_cols = st.columns([0.4, 1.2, 0.6, 1.2, 1.8, 1.8])
    hdr_cols[0].markdown("**#**")
    hdr_cols[1].markdown("**Syllable**")
    hdr_cols[2].markdown("**L/G**")
    hdr_cols[3].markdown("**Svara**")
    hdr_cols[4].markdown("**Duration ×**")
    hdr_cols[5].markdown("**Pitch (st)**")

    # One row per syllable with number_input widgets
    for i, entry in enumerate(mapping_table):
        row_cols = st.columns([0.4, 1.2, 0.6, 1.2, 1.8, 1.8])

        row_cols[0].markdown(f"`{i+1}`")
        row_cols[1].markdown(f"**{entry['syllable']}**")

        # Color-coded L/G badge
        if entry['lg'] == 'G':
            row_cols[2].markdown(f"🟡 **{entry['lg']}**")
        else:
            row_cols[2].markdown(f"🟢 **{entry['lg']}**")

        row_cols[3].markdown(f"{entry['svara']}")

        # Editable duration multiplier: range 0.5x to 3.0x, step 0.25
        dur_val = row_cols[4].number_input(
            f"dur_{i}",
            min_value=0.5,
            max_value=3.0,
            value=st.session_state['edited_durations'][i],
            step=0.25,
            format="%.2f",
            key=f"dur_input_{i}",
            label_visibility="collapsed",
        )
        st.session_state['edited_durations'][i] = dur_val

        # Editable pitch shift: range -6 to +6 semitones, step 1
        pitch_val = row_cols[5].number_input(
            f"pitch_{i}",
            min_value=-6,
            max_value=6,
            value=st.session_state['edited_pitches'][i],
            step=1,
            key=f"pitch_input_{i}",
            label_visibility="collapsed",
        )
        st.session_state['edited_pitches'][i] = pitch_val

    # --- Action Buttons Row ---
    st.markdown("---")
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        regenerate_clicked = st.button(
            "🔄 Regenerate Audio (skip TTS)",
            type="primary",
            use_container_width=True,
            key="regenerate_btn",
        )

    with btn_col2:
        reset_clicked = st.button(
            "↩️ Reset to Defaults",
            use_container_width=True,
            key="reset_btn",
        )

    # Handle Reset
    if reset_clicked:
        st.session_state['edited_durations'] = [entry['duration_mult'] for entry in mapping_table]
        st.session_state['edited_pitches'] = [entry['pitch_semitones'] for entry in mapping_table]
        st.rerun()

    # Handle Regenerate — rerun Steps 5+6 only, using cached TTS audio
    if regenerate_clicked:
        with st.spinner("🔄 Reprocessing audio with updated parameters..."):
            try:
                from audio_alignment import process_all_chunks
                from stitch_export import stitch_and_export
                import time as _time

                # Build modified mapping table from user edits
                modified_table = []
                for i, entry in enumerate(mapping_table):
                    modified_table.append({
                        'syllable': entry['syllable'],
                        'lg': entry['lg'],
                        'svara': entry['svara'],
                        'duration_mult': st.session_state['edited_durations'][i],
                        'pitch_semitones': st.session_state['edited_pitches'][i],
                    })

                # Read cached TTS audio from session state (set during initial generation)
                audio_array = st.session_state['tts_audio_array']
                sample_rate = st.session_state['tts_sample_rate']

                t0 = _time.time()
                chunks = process_all_chunks(audio_array, sample_rate, modified_table)
                t_align = _time.time() - t0

                t0 = _time.time()
                export_result = stitch_and_export(chunks, sample_rate, result['output_path'])
                t_stitch = _time.time() - t0

                # Update result in session state with new audio info
                result['duration_secs'] = export_result['duration_secs']
                result['processing_times']['regen_alignment'] = t_align
                result['processing_times']['regen_stitch'] = t_stitch
                st.session_state['result'] = result
                st.session_state['regen_success'] = True

                st.rerun()

            except Exception as e:
                st.error(f"❌ Regeneration error: {str(e)}")
                st.exception(e)

    # Show success message if just regenerated
    if st.session_state.get('regen_success', False):
        st.success("✅ Audio regenerated with updated parameters!")
        st.session_state['regen_success'] = False

    # --- Audio Player and Download ---
    st.markdown("### 🔊 Generated Recitation")

    output_path = result['output_path']
    if os.path.exists(output_path):
        # Audio player
        st.audio(output_path, format="audio/wav")

        # Duration info
        st.markdown(f"**Duration:** {result['duration_secs']:.2f} seconds")

        # Download button
        with open(output_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()

        st.download_button(
            label="📥 Download WAV",
            data=audio_bytes,
            file_name="chanda_recitation.wav",
            mime="audio/wav",
            key="download_btn",
        )
    else:
        st.error("❌ Output audio file not found. Check the pipeline logs.")

    # --- Processing Times ---
    with st.expander("⏱️ Processing Times"):
        timing_data = []
        step_names = {
            'step1_normalization': '📝 Normalization',
            'step2_chanda_analysis': '📐 Chanda Analysis',
            'step3_mapping': '🎵 Rhythm/Pitch Mapping',
            'step4_tts': '🎙️ TTS Generation',
            'step5_alignment': '✂️ Audio Alignment',
            'step6_export': '📦 Stitch & Export',
            'regen_alignment': '🔄 Regen: Alignment',
            'regen_stitch': '🔄 Regen: Stitch',
            'total': '⏱️ Total (initial)',
        }
        for key, label in step_names.items():
            if key in result['processing_times']:
                timing_data.append({
                    'Step': label,
                    'Time (s)': f"{result['processing_times'][key]:.3f}",
                })

        st.table(pd.DataFrame(timing_data))

else:
    # Show placeholder when no results yet
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; color: #888;">
        <h3>Enter a Sanskrit verse above and click "Generate Recitation"</h3>
        <p>The system will analyze the meter, map rhythm and pitch, and generate a melodically constrained audio recitation.</p>
    </div>
    """, unsafe_allow_html=True)

