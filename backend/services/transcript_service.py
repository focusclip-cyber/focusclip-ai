import os
import whisper

# Tell Whisper exactly where ffmpeg.exe is (only needed on Windows where
# ffmpeg isn't already on PATH)
FFMPEG_BIN_DIR = r"C:\ffmpeg-8.1.2-essentials_build\bin"
if os.path.isdir(FFMPEG_BIN_DIR) and FFMPEG_BIN_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] += os.pathsep + FFMPEG_BIN_DIR

model = whisper.load_model("base")


def get_transcript(audio_path):
    """
    Runs Whisper on the audio file.

    Returns:
        text (str): full transcript as one string (same as before)
        segments (list[dict]): timestamped chunks, e.g.
            [{"start": 0.0, "end": 3.4, "text": "Hey everyone..."}, ...]
            Needed so we can later figure out WHEN a given speaker talks.
    """
    result = model.transcribe(audio_path)

    segments = [
        {
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
        }
        for seg in result["segments"]
    ]

    return result["text"], segments
