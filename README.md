# 🕉️ Chanda — Melodic Constrained Sanskrit Recitation System (POC)

A proof-of-concept system that takes Sanskrit verse text as input, analyzes its metrical structure (Chandas), and generates a speech audio file where **rhythm** (syllable duration) and **pitch** (svara movement) are governed by the verse's metrical and melodic framework.

---

## 📐 Background

### Chandas (Sanskrit Meters)
Sanskrit poetry is governed by formal metrical systems called **Chandas**. Each verse is composed of syllables classified as:
- **Laghu (L)** — Light syllable, short duration (1 mātrā unit)
- **Guru (G)** — Heavy syllable, long duration (2 mātrā units)

This classification determines the **rhythm** of recitation — a Guru syllable takes twice as long to speak as a Laghu.

### Svara (Pitch Accents)
Classical recitation uses a **melodic/pitch framework** rooted in Vedic svaras:
- **Udātta** — Raised pitch (high tone, +2 semitones)
- **Anudātta** — Lowered pitch (low tone, -2 semitones)
- **Svarita** — Neutral/falling pitch (middle tone, no change)

### Anushtubh Meter
The most common meter (used in Bhagavad Gita, Ramayana) — 8 syllables per quarter-verse (pāda), 4 pādas per verse, 32 syllables total.

---

## 🏗️ Architecture

```
Input Text (IAST/ITRANS/Devanagari)
        │
        ▼
┌─────────────────────┐
│ Step 1: Normalize    │  → Devanagari
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Step 2: Analyze      │  → Syllables + L/G + Meter
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Step 3: Map          │  → Duration multipliers + Svara offsets
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Step 4: TTS          │  → Raw audio (indic-parler-tts)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Step 5: Align        │  → Time-stretch + Pitch-shift per syllable
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Step 6: Stitch       │  → Final output.wav
└─────────────────────┘
```

---

## 📁 Project Structure

```
Chanda/
├── config.py                    # Global configuration constants
├── input_normalization.py       # Input parsing + transliteration
├── chanda_analysis.py           # Meter detection + syllable L/G tagging
├── rhythm_pitch_mapping.py      # Duration multipliers + svara offsets
├── tts_generation.py            # TTS via ai4bharat/indic-parler-tts
├── audio_alignment.py           # Syllable-level time-stretch + pitch-shift
├── stitch_export.py             # Concatenate chunks → output.wav
├── pipeline.py                  # End-to-end orchestrator
├── app.py                       # Streamlit UI
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── output/                      # Generated audio files
```

---

## 🚀 Setup

### Prerequisites
- Python 3.10+
- `ffmpeg` installed and on PATH
- (Optional) CUDA-capable GPU for faster TTS inference

### Installation

```bash
# Clone the repository
cd Chanda

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### First Run Note
The TTS model (`ai4bharat/indic-parler-tts`, ~3-4 GB) is downloaded from HuggingFace on first run and cached locally.

---

## 🎯 Usage

### Streamlit UI (Recommended)
```bash
streamlit run app.py
```
Opens a web interface where you can enter a verse, view the analysis, and play/download the generated audio.

### CLI Pipeline
```bash
python pipeline.py
```
Runs the full pipeline on a default test verse and saves output to `output/output.wav`.

### Individual Steps
Each module can be tested independently:
```bash
python input_normalization.py
python chanda_analysis.py
python rhythm_pitch_mapping.py
python tts_generation.py
python audio_alignment.py
python stitch_export.py
```

---

## 🔧 Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| Transliteration | `indic-transliteration` |
| Meter Analysis | `chanda` (hrishikeshrt) |
| TTS | `ai4bharat/indic-parler-tts` via HuggingFace |
| Audio Slicing | `pydub` + `ffmpeg` |
| Duration + Pitch | `librosa` |
| UI | `Streamlit` |

---

## ⚠️ Known Limitations & Design Decisions

1. **Approximate syllable alignment**: Audio is split proportionally by duration weight (sum of L/G units), not via forced-alignment techniques. Syllable boundaries won't be phonetically precise.

2. **Simplified svara model**: The svara (pitch accent) assignment uses a positional cycling pattern `[Anudātta, Udātta, Svarita]` repeating within each pāda. Real Vedic accents are text-dependent and marked in manuscripts.

3. **Boundary artifacts**: Processing audio segments independently can introduce clicks at chunk boundaries. A 10ms crossfade is applied to mitigate this, but some artifacts may remain.

4. **CPU inference speed**: Without a CUDA GPU, TTS generation can take 30-120 seconds per verse. With a GPU, it typically takes 5-15 seconds.

5. **POC scope**: This is a hackathon proof-of-concept demonstrating the feasibility of meter-constrained recitation. Production quality would require forced-alignment, richer prosody modeling, and fine-tuned TTS.

---

## 📜 License

This project is a proof-of-concept for educational and research purposes.
