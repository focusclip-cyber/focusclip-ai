import os
import subprocess


def cut_clips(video_path, timestamps, video_id, speaker_name):
    """
    Cuts one .mp4 clip per {start, end} timestamp range using ffmpeg.

    Saves them under: backend/clips/<video_id>/<speaker>/clip_1.mp4, clip_2.mp4, ...

    Returns a list of relative file paths (used to build download URLs).
    """

    safe_speaker = "".join(c if c.isalnum() else "_" for c in speaker_name) or "speaker"
    out_dir = os.path.join("clips", video_id, safe_speaker)
    os.makedirs(out_dir, exist_ok=True)

    clip_paths = []

    for idx, ts in enumerate(timestamps, start=1):
        start = ts["start"]
        end = ts["end"]
        duration = round(end - start, 2)

        if duration <= 0:
            continue

        out_file = os.path.join(out_dir, f"clip_{idx}.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-avoid_negative_ts", "make_zero",
            out_file,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"ffmpeg failed on clip {idx}: {result.stderr[-800:]}")
            continue

        clip_paths.append(out_file.replace("\\", "/"))

    return clip_paths
