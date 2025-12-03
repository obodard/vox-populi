import os
import tempfile

import nemo.collections.asr as nemo_asr
import torch
from pydub import AudioSegment

MODEL = "../../data/parakeet-tdt-0.6b-v3.nemo"

# source_file="2086-149220-0033.wav"
# Chunk size in milliseconds (5 minutes = 300000ms)
CHUNK_SIZE_MS = 300000


def convert_m4a_to_wav(input_file, output_file):
    print(f"Converting {input_file} to {output_file}")
    global source_file
    audio = AudioSegment.from_file(input_file, format="m4a")
    audio.export(output_file, format="wav")
    source_file = output_file


def split_audio_into_chunks(audio_file, chunk_size_ms=CHUNK_SIZE_MS):
    """Split large audio file into smaller chunks"""
    print(f"Loading audio file: {audio_file}")
    audio = AudioSegment.from_wav(audio_file)
    duration_ms = len(audio)
    print(f"Audio duration: {duration_ms / 1000:.1f} seconds ({duration_ms / 60000:.1f} minutes)")

    chunk_files = []
    temp_dir = tempfile.mkdtemp()

    for i, start_ms in enumerate(range(0, duration_ms, chunk_size_ms)):
        end_ms = min(start_ms + chunk_size_ms, duration_ms)
        chunk = audio[start_ms:end_ms]
        chunk_file = os.path.join(temp_dir, f"chunk_{i:03d}.wav")
        chunk.export(chunk_file, format="wav")
        chunk_files.append(chunk_file)
        print(f"  Created chunk {i + 1}: {start_ms / 1000:.1f}s - {end_ms / 1000:.1f}s")

    return chunk_files, temp_dir


# convert_m4a_to_wav("CGI_2025Q4_opportunities_exploration.m4a", "CGI_2025Q4_opportunities_exploration.wav")
def check_gpu():
    global device
    # Check device availability and move model to GPU if available
    # Note: MPS has compatibility issues with this model, using CPU for stability
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print("Using CUDA (NVIDIA GPU)")
    else:
        device = torch.device("cpu")
        print("Using CPU")


if __name__ == "__main__":
    check_gpu()
    # Load model from local file
    print(f"\nLoading model {MODEL}...")
    asr_model = nemo_asr.models.ASRModel.restore_from(restore_path=MODEL)
    asr_model = asr_model.to(device)
    print(f"Model loaded on: {device}")

    # Split audio into chunks if file is large
    chunk_files, temp_dir = split_audio_into_chunks(source_file)

    print(f"\nTranscribing {len(chunk_files)} chunk(s)...\n")

    # Transcribe each chunk
    full_transcription = []
    for i, chunk_file in enumerate(chunk_files):
        print(f"Processing chunk {i + 1}/{len(chunk_files)}...")
        try:
            output = asr_model.transcribe([chunk_file], batch_size=1)
            # Extract text from the Hypothesis object
            if hasattr(output[0], 'text'):
                chunk_text = output[0].text
            else:
                chunk_text = str(output[0])
            full_transcription.append(chunk_text)
            print(f"  ✓ Chunk {i + 1} transcribed ({len(chunk_text)} chars)")
        except Exception as e:
            print(f"  ✗ Error transcribing chunk {i + 1}: {e}")
            full_transcription.append(f"[Error in chunk {i + 1}]")

    # Cleanup temporary files
    print("Cleaning up temporary files...")
    for chunk_file in chunk_files:
        try:
            os.remove(chunk_file)
        except OSError:
            pass
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    # Combine and display full transcription
    print(f"\n{'=' * 80}")
    print("FULL TRANSCRIPTION:")
    print(f"{'=' * 80}\n")
    transcription = " ".join(full_transcription)
    print(transcription)
    print(f"\n{'=' * 80}")
    print(f"Total characters: {len(transcription)}")
    print(f"{'=' * 80}\n")
