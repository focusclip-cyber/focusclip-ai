"""
FocusClip AI - Command Line Pipeline
-------------------------------------
Runs the full pipeline for a YouTube video with no frontend involved:

  YouTube URL -> download audio+video -> transcribe (Whisper)
  -> detect speakers (Gemini) -> find each speaker's timestamps (Gemini)
  -> cut clips (ffmpeg) -> save into output/<video_id>/<speaker>/clip_N.mp4

Usage:
    python run_pipeline.py "https://youtu.be/VIDEO_ID"

Optional flags:
    --speakers "Speaker 1,Speaker 2"   Only cut clips for these speakers
                                        (default: all detected speakers)
    --topic "the moment they argue"    Only cut clips where the speaker
                                        talks about this topic
    --output-dir "output"              Where finished clips are saved
                                        (default: "output")
"""

import argparse
import os
import shutil

from services.youtube_service import extract_video_id, download_audio, download_video
from services.transcript_service import get_transcript
from services.gemini_service import detect_speakers, get_speaker_timestamps
from services.clip_service import cut_clips


def run(youtube_url, only_speakers=None, topic=None, output_dir="output"):

    video_id = extract_video_id(youtube_url)
    if not video_id:
        print(f"Could not read a video ID from: {youtube_url}")
        return

    print(f"\n=== {youtube_url} ===")

    print("STEP 1 - Downloading audio...")
    audio_path = download_audio(youtube_url)

    print("STEP 2 - Downloading video...")
    video_path = download_video(youtube_url)

    print("STEP 3 - Transcribing (this can take a few minutes)...")
    transcript, segments = get_transcript(audio_path)
    print(f"         Transcript length: {len(transcript)} chars, {len(segments)} segments")

    print("STEP 4 - Detecting speakers...")
    speakers = detect_speakers(transcript)
    print(f"         Speakers found: {speakers}")

    if not speakers:
        print("No speakers detected, nothing to clip. Stopping.")
        return

    if only_speakers:
        speakers = [s for s in speakers if s in only_speakers]
        print(f"         Filtered to: {speakers}")

    all_clips = {}

    for speaker in speakers:

        if topic:
            print(f"\nSTEP 5 - Finding moments where {speaker} talks about: \"{topic}\"...")
        else:
            print(f"\nSTEP 5 - Finding timestamps for {speaker}...")

        timestamps = get_speaker_timestamps(segments, speaker, topic=topic)

        if not timestamps:
            print(f"         No clear moments found for {speaker}, skipping.")
            continue

        print(f"         Found {len(timestamps)} moment(s). Cutting clips...")
        clip_paths = cut_clips(video_path, timestamps, video_id, speaker)

        # Move clips from backend/clips/... into the client-facing output folder
        final_dir = os.path.join(output_dir, video_id, speaker.replace(" ", "_"))
        os.makedirs(final_dir, exist_ok=True)

        final_paths = []
        for src in clip_paths:
            dest = os.path.join(final_dir, os.path.basename(src))
            shutil.copy2(src, dest)
            final_paths.append(dest)

        all_clips[speaker] = final_paths
        print(f"         Saved {len(final_paths)} clip(s) to {final_dir}")

    print("\n=== DONE ===")
    total = sum(len(v) for v in all_clips.values())
    print(f"{total} clip(s) ready in: {os.path.join(output_dir, video_id)}\n")

    for speaker, paths in all_clips.items():
        print(f"{speaker}:")
        for p in paths:
            print(f"   - {p}")

    return all_clips


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run the full FocusClip AI pipeline from the command line.")
    parser.add_argument("youtube_url", help="YouTube video URL")
    parser.add_argument("--speakers", help="Comma-separated list of speakers to clip (default: all)", default=None)
    parser.add_argument("--topic", help="Only cut clips where the speaker talks about this topic", default=None)
    parser.add_argument("--output-dir", help="Where finished clips are saved", default="output")

    args = parser.parse_args()

    only_speakers = None
    if args.speakers:
        only_speakers = [s.strip() for s in args.speakers.split(",")]

    run(args.youtube_url, only_speakers=only_speakers, topic=args.topic, output_dir=args.output_dir)
