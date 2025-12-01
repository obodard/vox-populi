import os
import sys
os.environ['OVERRIDES_DISABLE_RUNTIME_TYPE_CHECK'] = '1'

# Import and patch overrides before anything else
import overrides.signature
import overrides.overrides

# Monkey-patch to disable signature compatibility checking
overrides.signature.ensure_signature_is_compatible = lambda *args, **kwargs: None
overrides.signature.ensure_all_positional_args_defined_in_sub = lambda *args, **kwargs: None
overrides.signature.ensure_all_kwargs_defined_in_sub = lambda *args, **kwargs: None

import nemo.collections.asr as nemo_asr
import torch
from pydub import AudioSegment
from datetime import datetime

MODEL="../../data/parakeet-tdt-0.6b-v3.nemo"
source_file="../../data/2086-149220-0033.wav"


def convert_m4a_to_wav(input_file, output_file):
    print(f"Converting {input_file} to {output_file}")
    global source_file
    audio = AudioSegment.from_file(input_file, format="m4a")
    audio.export(output_file, format="wav")
    source_file = output_file


def check_gpu():
    global device
    # Check device availability and move model to GPU if available
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print("Using CUDA (NVIDIA GPU)")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using MPS (Apple GPU)")
    else:
        device = torch.device("cpu")
        print("Using CPU")
    return device


if __name__ == "__main__":
    device = check_gpu()

    # Load model from local file
    asr_model = nemo_asr.models.ASRModel.restore_from(restore_path=MODEL)
    asr_model = asr_model.to(device)
    print(f"Model {MODEL} loaded on: {device}\n\n")

    output = asr_model.transcribe([source_file])
    transcription = output[0].text

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H-%M-%S")
    output_file = f"../../data/transcript_{timestamp}.txt"

    # Write transcription to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(transcription)

    print(f"\nTranscription saved to: {output_file}")
    print(f"\nTranscription:\n{transcription}\n")

