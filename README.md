# Vox Populi

> ⚠️ **WORK IN PROGRESS**: This project is under active development. Features may be incomplete, and breaking changes may occur. Use at your own discretion.

**Vox Populi** is an AI-powered meeting intelligence system that transcribes audio recordings, generates structured summaries, maps transcripts to agenda items, and extracts actionable insights from meetings.

## 🎯 Features

- **Audio Transcription**: Convert meeting recordings to text using NVIDIA's Parakeet TDT ASR model
- **Smart Summarization**: Generate comprehensive meeting summaries with executive overviews, key decisions, and action items
- **Agenda Mapping**: Automatically align transcript sections with meeting agenda topics
- **Action Item Extraction**: Identify and structure tasks, assignees, and deadlines
- **Multi-format Support**: Process WAV audio files (with M4A conversion support)
- **GPU Acceleration**: Supports CUDA (NVIDIA), MPS (Apple Silicon), and CPU inference

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Agents](#agents)
- [License](#license)

## 🏗️ Architecture

The system consists of several specialized AI agents:

1. **Transcription Module** (`transcript.py`): Uses NVIDIA NeMo's Parakeet model for speech-to-text
2. **Summarizer Agent** (`summarizer_agent.py`): Generates structured meeting summaries using Google Gemini
3. **Agenda Parser Agent** (`agenda_parser_agent.py`): Maps transcript sections to agenda topics
4. **Action Item Extractor** (planned): Extracts and structures action items

## 📦 Prerequisites

- **Python**: 3.11
- **pip**: Latest version recommended
- **Operating System**: macOS, Linux, or Windows
- **Google API Key**: Required for Gemini-powered agents
- **GPU** (optional but recommended): 
  - NVIDIA GPU with CUDA support, or
  - Apple Silicon with MPS support

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vox-populi
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

Use the provided Makefile for simplified installation:

```bash
make install
```

This will:
- Install `nemo_toolkit` (without dependencies to avoid conflicts)
- Install all requirements from `requirements.txt`
- Install `texterrors` with binary-only option

#### Manual Installation (Alternative)

If you prefer manual installation:

```bash
pip install nemo_toolkit --no-deps
pip install -r requirements.txt
pip install --only-binary=:all: texterrors
```

## ⚙️ Setup

### 1. Download the Parakeet Model

Download NVIDIA's Parakeet TDT ASR model and place it in the `data/` folder:

```bash
cd data
# Download parakeet-tdt-0.6b-v3.nemo from NVIDIA NGC
# Direct link: https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemo/models/parakeet-tdt-0.6b
```

**Expected location**: `data/parakeet-tdt-0.6b-v3.nemo`

You can also use `wget` or `curl`:

```bash
cd data
wget <parakeet-model-download-url> -O parakeet-tdt-0.6b-v3.nemo
```

### 2. Configure Google API Key

The summarizer and agenda parser agents require a Google API key for Gemini access.

**Option A: Environment Variable (Recommended)**

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Add this to your `~/.zshrc` or `~/.bashrc` for persistence.

**Option B: Create .env File**

Create a `.env` file in the `summarizer_agent/` directory:

```bash
echo "GOOGLE_API_KEY=your-api-key-here" > summarizer_agent/.env
```

### 3. Prepare Your Audio Files

Place your audio recordings in the `data/` folder:

```bash
cp /path/to/your/meeting.wav data/
```

Supported formats:
- `.wav` (direct processing)
- `.m4a` (automatic conversion to WAV)

### 4. Prepare Meeting Agenda (Optional)

For agenda mapping features, create an agenda file:

```bash
nano data/agenda.md
```

Example format:

```markdown
# Meeting Agenda

## Date: 2025-12-01
## Attendees: Alice, Bob, Charlie

### Agenda Items

1. Introduction & Objectives (5 min)
2. Requirements Discussion (10 min)
3. Technical Review (15 min)
4. Next Steps (5 min)
```

## 📘 Usage

### Transcribe Audio

```bash
cd src/vox-machine
python transcript.py
```

This will:
- Load the Parakeet model
- Process the audio file
- Generate a timestamped transcript: `data/transcript_YYYYMMDD_HH-MM-SS.txt`

### Generate Meeting Summary

```bash
cd src/vox-machine
python summarizer_agent.py
```

Output includes:
- One-line summary
- Executive summary (3-4 paragraphs)
- Key decisions with rationale
- Action items with assignees and priorities
- Attendee list
- Open questions
- Sentiment analysis

### Map Transcript to Agenda

```bash
cd src/vox-machine
python agenda_parser_agent.py
```

This maps each section of the transcript to the corresponding agenda topic and saves the result as: `data/agenda_mapping_YYYYMMDD_HH-MM-SS.json`

## 📂 Project Structure

```
vox-populi/
├── README.md                      # This file
├── LICENSE                        # License information
├── Makefile                       # Installation and cleanup automation
├── requirements.txt               # Python dependencies
├── data/                          # Data directory
│   ├── parakeet-tdt-0.6b-v3.nemo # ASR model (download required)
│   ├── agenda.md                  # Meeting agenda template
│   ├── *.wav                      # Audio files
│   ├── transcript_*.txt           # Generated transcripts
│   └── agenda_mapping_*.json      # Agenda mappings
├── src/
│   └── vox-machine/
│       ├── main.py                        # Logging configuration
│       ├── transcript.py                  # Audio transcription module
│       ├── summarizer_agent.py            # Meeting summarization
│       ├── agenda_parser_agent.py         # Agenda-transcript mapper
│       └── action_item_extractor_agent.py # Action item extraction (WIP)
└── summarizer_agent/
    ├── __init__.py
    ├── agent.py                   # Simple agent wrapper
    └── .env                       # API key configuration
```

## 🤖 Agents

### Summarizer Agent

**Model**: Google Gemini 2.5 Flash Lite

**Purpose**: Generate structured meeting summaries with:
- One-line summary (≤140 chars)
- Executive summary (≤300 words)
- Key decisions with rationale
- Action items (labeled A1, A2, A3...)
- Attendee list
- Open questions
- Follow-ups
- Highlights with timestamps
- Tone and sentiment analysis

**Output Format**: JSON

### Agenda Parser Agent

**Model**: Google Gemini 2.5 Flash Lite

**Purpose**: Map transcript sections to agenda topics

**Features**:
- Preserves exact transcript text
- Assigns confidence levels (high/medium/low)
- Identifies unmapped sections
- Maintains chronological order

**Output Format**: JSON

## 🧹 Cleanup

Remove Python cache files and build artifacts:

```bash
make clean
```

## 🔧 Troubleshooting

### NeMo Import Errors

If you encounter signature compatibility errors with the `overrides` package, ensure you're using the patched version in `transcript.py` which disables runtime type checking.

### GPU Not Detected

Check GPU availability:

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"MPS available: {torch.backends.mps.is_available()}")
```

### API Key Issues

Verify your Google API key is set:

```bash
echo $GOOGLE_API_KEY
```

If empty, set it:

```bash
export GOOGLE_API_KEY="your-key-here"
```

### Agent Naming Issues

Agent names must be valid Python identifiers (letters, digits, underscores only). Avoid hyphens in folder names like `summarizer-agent`. Use `summarizer_agent` instead.

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NVIDIA NeMo**: ASR toolkit and Parakeet models
- **Google Gemini**: LLM-powered agents
- **Google ADK**: Agent Development Kit

---

**Note**: This is an experimental project. Agent behaviors and outputs may vary. Always review generated summaries and action items for accuracy.

