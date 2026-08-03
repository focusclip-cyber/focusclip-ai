from google import genai
from dotenv import load_dotenv
import os
import ast
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def detect_speakers(transcript):

    prompt = f"""
You are an expert at identifying speakers.

Read the transcript carefully.

Return ONLY a valid Python list.

Example:

["John","Mary","Alex"]

Do not explain anything.
Do not use markdown.
Do not use ```.

Transcript:

{transcript}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    text = response.text.strip()

    text = text.replace("```python", "")
    text = text.replace("```", "")
    text = text.strip()

    try:
        return ast.literal_eval(text)
    except Exception:
        return []


def get_speaker_timestamps(segments, speaker_name):
    """
    Given Whisper's timestamped transcript segments, asks Gemini which
    segments were most likely spoken by `speaker_name`, then merges those
    into clean start/end ranges we can hand straight to ffmpeg.

    segments: [{"start": float, "end": float, "text": str}, ...]
    returns:  [{"start": float, "end": float}, ...]
    """

    if not segments:
        return []

    compact_segments = [
        {"i": idx, "start": seg["start"], "end": seg["end"], "text": seg["text"]}
        for idx, seg in enumerate(segments)
    ]

    prompt = f"""
You are an expert at analyzing conversation transcripts and figuring out
who is speaking based on context, tone, and turn-taking.

Below is a transcript broken into timestamped segments (JSON array).
Each segment has an index "i", a "start" and "end" time in seconds, and "text".

Identify every segment index most likely spoken by: "{speaker_name}"

Return ONLY a valid JSON array of integers (the segment indices).
Example: [0, 1, 4, 5, 9]

Do not explain anything.
Do not use markdown.
Do not use ```.

Segments:
{json.dumps(compact_segments)}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        indices = ast.literal_eval(text)
        indices = [int(i) for i in indices]
    except Exception:
        indices = []

    ranges = [
        {"start": segments[i]["start"], "end": segments[i]["end"]}
        for i in indices
        if 0 <= i < len(segments)
    ]

    return _merge_ranges(ranges)


def _merge_ranges(ranges, gap_threshold=2.0, padding=0.3):
    """
    Merges segments that are close together into one continuous clip
    (so we don't produce 20 tiny 2-second clips), and pads each clip
    slightly so cuts don't feel abrupt.
    """
    if not ranges:
        return []

    ranges = sorted(ranges, key=lambda r: r["start"])
    merged = [dict(ranges[0])]

    for r in ranges[1:]:
        last = merged[-1]
        if r["start"] - last["end"] <= gap_threshold:
            last["end"] = max(last["end"], r["end"])
        else:
            merged.append(dict(r))

    for r in merged:
        r["start"] = max(0, round(r["start"] - padding, 2))
        r["end"] = round(r["end"] + padding, 2)

    return merged
