from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv
import os
import ast
import json
import time

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _generate_with_retry(prompt, max_attempts=4, base_delay=5):
    """Calls Gemini and retries on temporary server overload (503) instead
    of throwing away a run that already spent minutes downloading/transcribing."""

    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )
        except genai_errors.ServerError as e:
            last_error = e
            wait = base_delay * attempt
            print(f"Gemini overloaded (attempt {attempt}/{max_attempts}). Retrying in {wait}s...")
            time.sleep(wait)

    raise last_error


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

    response = _generate_with_retry(prompt)

    text = response.text.strip()

    text = text.replace("```python", "")
    text = text.replace("```", "")
    text = text.strip()

    try:
        return ast.literal_eval(text)
    except Exception:
        return []


def get_speaker_timestamps(segments, speaker_name, topic=None):
    """
    Given Whisper's timestamped transcript segments, asks Gemini which
    segments were most likely spoken by `speaker_name`, then merges those
    into clean start/end ranges we can hand straight to ffmpeg.

    If `topic` is given, narrows it further to only segments where that
    speaker is talking about that specific topic.

    segments: [{"start": float, "end": float, "text": str}, ...]
    returns:  [{"start": float, "end": float}, ...]
    """

    if not segments:
        return []

    compact_segments = [
        {"i": idx, "start": seg["start"], "end": seg["end"], "text": seg["text"]}
        for idx, seg in enumerate(segments)
    ]

    if topic:
        instruction = (
            f'Identify every segment index most likely spoken by "{speaker_name}" '
            f'AND where the topic being discussed is: "{topic}". '
            f'Only include segments that satisfy BOTH conditions.'
        )
    else:
        instruction = f'Identify every segment index most likely spoken by: "{speaker_name}"'

    prompt = f"""
You are an expert at analyzing conversation transcripts and figuring out
who is speaking and what they're talking about, based on context, tone,
and turn-taking.

Below is a transcript broken into timestamped segments (JSON array).
Each segment has an index "i", a "start" and "end" time in seconds, and "text".

{instruction}

Return ONLY a valid JSON array of integers (the segment indices).
Example: [0, 1, 4, 5, 9]

Do not explain anything.
Do not use markdown.
Do not use ```.

Segments:
{json.dumps(compact_segments)}
"""

    response = _generate_with_retry(prompt)

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
